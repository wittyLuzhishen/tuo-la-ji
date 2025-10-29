import random
# 直接导入eventlet，因为我们已经强制使用eventlet模式
import eventlet
from flask import session, request
from flask_socketio import emit, join_room as socketio_join_room, leave_room as socketio_leave_room
import time

from biz_utils import add_game_log, common_check
from game_logic import compare_hands, create_deck, deal_cards, shuffle_deck
from dao_user import get_user_info, set_user_info
from game_enums import (GameStatus, PlayerKey, PlayerStatus, RoomSettingKey, RoomKey,
    RoomStatus, OnlineStatus, UserKey
)
from message_enums import (ServerMessageType, ServerDataKey)
from dao_room import (create_room, get_player_info, get_playing_players, get_room_list, is_game_started, 
    is_player_turn, is_room_owner, leave_room as leave_room_dao, reset_room_for_new_game, reset_room_when_game_end, 
    rooms, reconnect_timer, find_player_in_room, get_room_by_player_id, seat_player, update_player_online_status, 
    get_room_info, join_room as join_room_dao, update_player_status, update_room_settings
)
from server_message_emitter import broadcast_game_info

LOST_RECONNECT_TIMEOUT = 30 # 掉线重连等待秒数，如超时未重连则视为彻底断开连接
CONTINUE_NEW_GAME_TIMER = "continue_new_game_timer" # 继续游戏定时器名称
CONTINUE_NEW_GAME_TIMEOUT = 10 # 继续游戏定时器超时秒数
INNER_TURN_LOST_RECONNECT_TIMEOUT = 10 # 轮到某玩家行动，但是该玩家掉线了，等待他上限的秒数
TURN_TIMEOUT = 20 # 玩家出牌时间秒数，如超时未出牌则视为弃牌
MIN_SHOW_DOWM_TURN = 1 # 想要比牌，最少经过多少轮


# Socket.IO事件处理函数
def handle_connect():
    """
    处理客户端基本连接事件
    
    关键点：
    1. 只负责处理连接建立，发送连接成功消息
    2. 不立即分配user_id，等待客户端可能的重连请求
    3. 重连逻辑完全由reconnect_with_id和handle_reconnect处理
    """
    # 获取当前socket连接的会话ID
    socket_id = request.sid
    
    print(f"客户端连接成功，socket_id={socket_id}，之后要等待可能的重连请求")
    
    # 向客户端发送连接成功消息，不包含user_id
    # 客户端收到此消息后，应决定是否发送reconnect_with_id请求
    emit(ServerMessageType.Connected.value, {"connected": True})
    
    # 返回socket_id作为临时标识符，客户端应等待后续的user_id_assigned消息
    return socket_id

def handle_reconnect(user_id:str):
    """
    处理客户端重连逻辑或新连接的用户ID分配
    
    功能：
    1. 如果提供了有效的user_id，尝试重连验证
    2. 如果未提供user_id或重连失败，分配新的user_id
    3. 统一处理用户标识的生成和管理

    Returns:
        tuple: (成功标志, user_id, room_id)
    """
    # 获取当前socket连接的会话ID作为备选user_id
    socket_id = request.sid

    # 根据是否提供了有效的user_id决定处理方式
    if user_id != "":
        print(f"用户{user_id}尝试重连")
        
        # 检查是否在允许重连的时间段内
        if user_id in reconnect_timer:
            # 重连成功
            timer = reconnect_timer.pop(user_id)
            if hasattr(timer, 'cancel'):
                timer.cancel()
            
            # 保持原来的用户ID
            emit(ServerMessageType.UserIDAssigned.value, {'user_id': user_id}, room=user_id)
            # 获取用户原来所在的房间
            room_id = get_room_by_player_id(user_id)
            if room_id:
                print(f"用户{user_id}重连成功，正在重新加入房间{room_id}")
                
                # 处理房间加入逻辑
                _join_room(room_id, user_id, reconnect=True)
                
                if room_id in rooms:
                    room = rooms[room_id]
                    # 如果房间状态是等待结束，且有玩家重新连接，恢复游戏状态
                    if room[RoomKey.Status.value] == RoomStatus.WaitingToDestroy.value:
                        # 恢复房间状态为正常状态
                        room[RoomKey.Status.value] = RoomStatus.Normal.value
                        add_game_log(room_id, f"玩家 {user_id} 重新连接，取消房间解散")
                    
                    # 无论房间状态如何，都广播游戏信息以更新玩家在线状态
                    broadcast_game_info(room_id)
                else:
                    print(f"房间{room_id}不存在")
                    room_id = None
            else:
                print(f"用户{user_id}重连成功，但不在任何房间中")
                room_id = None
            
            return True, user_id, room_id
        else:
            # 重连超时，分配新的user_id
            print(f"用户{user_id}重连超时，分配新用户ID={socket_id}")
            user_id = socket_id
            emit(ServerMessageType.UserIDAssigned.value, {'user_id': user_id}, room=user_id)
    else:
        user_id = socket_id
        print(f"客户端未提供user_id，使用socket_id作为新的user_id={socket_id}")
        emit(ServerMessageType.UserIDAssigned.value, {'user_id': user_id}, room=user_id)


def handle_disconnect(reason:str, user_id:str):
    """
    处理客户端断开连接事件
    
    Args:
        reason: 断开连接的原因，用于区分主动断开和网络不佳导致的断开
    """

    if not user_id:
        return

    # 区分断开连接的原因
    is_network_issue = False
    disconnect_reason_text = "未知原因"
    
    # Socket.IO常见的断开原因代码
    # 网络相关的断开原因
    network_reasons = [
        'io server disconnect',  # 服务器主动断开（可能是超时）
        'ping timeout',          # 心跳超时
        'transport close',       # 传输层关闭（可能是网络问题）
        'transport error'        # 传输错误
    ]
    
    # 主动断开的原因
    active_reasons = [
        'io client disconnect',  # 客户端主动断开（如关闭标签页）
        'io client error'        # 客户端错误
    ]
    
    if reason in network_reasons:
        is_network_issue = True
        disconnect_reason_text = "网络连接中断"
    elif reason in active_reasons:
        disconnect_reason_text = "用户主动断开连接"
    else:
        disconnect_reason_text = f"{reason}"
    
    # 记录断开连接信息
    print(f"用户{user_id}断开连接，原因: {disconnect_reason_text}")
    
    # 查找玩家所在的房间
    room_id = get_room_by_player_id(user_id)

    if not is_network_issue: # 如果是主动断开连接
        # 检查玩家是否在房间中
        if not room_id:
            print(f"用户{user_id}不在任何房间中，在大厅里主动断开连接")
        else:
            _leave_room(room_id, user_id)
            print(f"用户{user_id}在房间{room_id}中，主动断开连接")
            # 添加离开房间的日志
            add_game_log(room_id, f"{user_id} 主动离开，已移出房间{room_id}")
    else: # 网络原因导致断线，加入重连倒计时
        if room_id:
            update_player_online_status(room_id, user_id, OnlineStatus.LostConnection)
        reconnect_timer[user_id] = eventlet.spawn_after(LOST_RECONNECT_TIMEOUT, _clean_lost_player, user_id, room_id)
        emit(ServerMessageType.LostConnection.value, {"user_id": user_id})
    
    # 广播游戏信息，更新其他玩家看到的状态
    broadcast_game_info(room_id)


def _clean_lost_player(user_id:str, room_id:str):
    """
    处理丢失连接的玩家
    """

    if user_id in reconnect_timer:
        # 取消定时器任务，避免内存泄漏和重复执行
        timer = reconnect_timer.pop(user_id)
        # 安全地取消定时器，如果它是一个cancelable对象
        if hasattr(timer, 'cancel'):
            timer.cancel()
        print(f"用户{user_id}的重连定时器已取消")
    
    # 从房间中移除玩家
    _leave_room(room_id, user_id)
    add_game_log(room_id, f"{user_id} 超时未重连成功，已移出房间{room_id}")
    # 广播游戏信息，更新其他玩家看到的状态
    broadcast_game_info(room_id)


def _join_room(room_id, user_id, reconnect=False)->tuple:
    """加入/重新进入房间"""
    if not room_id or not user_id or room_id not in rooms:
        return False, "房间不存在或用户ID为空"
    if room_id not in rooms:
        return False, "房间不存在"
    max_player_number = rooms[room_id][RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber.value]
    if not reconnect and max_player_number <= len(rooms[room_id][RoomKey.Players.value]):
        return False, "房间已满"
    socketio_join_room(room=room_id, sid=user_id)
    print(f"用户{user_id}加入房间{room_id}，是否重连：{reconnect}")
    if reconnect:
        update_player_online_status(room_id, user_id, OnlineStatus.Online)
        add_game_log(room_id, f"玩家 {user_id} 重新连接")
        # 向该玩家推送历史状态
        emit(ServerMessageType.ReconnectRestore.value, get_room_info(room_id, user_id), room=user_id)
    else:
        join_room_dao(room_id, user_id)
        add_game_log(room_id, f"玩家 {user_id} 加入房间")
        emit(ServerMessageType.RoomJoined.value, {
            ServerDataKey.RoomID.value: room_id,
            ServerDataKey.UserID.value: user_id,
        })

    # 通知其他玩家该玩家已加入房间
    broadcast_game_info(room_id)
    return True, "加入/重新进入房间成功"


def _leave_room(room_id:str, user_id:str):
    """
    玩家主动离开房间
    """
    # 检查玩家是否在房间中
    player, _ = find_player_in_room(room_id, user_id)
    if not player:
        return False
        
    # 检查玩家是否是当前回合玩家
    if is_player_turn(room_id, user_id):
        # 自动弃牌并进入下一个玩家
        update_player_status(room_id, user_id, PlayerStatus.Folded)
    
    update_player_online_status(room_id, user_id, OnlineStatus.Offline)
    # 从房间中移除玩家
    leave_room_dao(room_id, user_id)
    # 离开Socket.IO通信房间
    socketio_leave_room(room=room_id, sid=user_id)
    print(f"已将用户{user_id}移出房间{room_id}")
    
    # 广播游戏信息，更新其他玩家看到的状态
    broadcast_game_info(room_id)
    return True


def handle_set_userinfo(user_id:str, username:str, avatar_url:str):
    """
    处理设置用户名事件
    """
    if not user_id or not username or not avatar_url:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "玩家ID、用户昵称、头像URL均不能为空"})
        return
    
    set_user_info(user_id, {
        UserKey.ID.value: user_id,
        UserKey.Username.value: username,
        UserKey.AvatarURL.value: avatar_url,
    })

    emit(ServerMessageType.UserInfoUpdated.value, {
        ServerDataKey.Username.value: username,
        ServerDataKey.AvatarURL.value: avatar_url
    })


def handle_get_room_list():
    """
    处理获取房间列表事件
    """
    emit(ServerMessageType.RoomList.value, {ServerDataKey.RoomList.value: get_room_list()})


def handle_get_room_details(room_id:str):
    """
    处理获取房间详情事件
    """

    if not room_id or room_id.strip() == "":
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    room_details = get_room_info(room_id)
    if not room_details:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return
        
    emit(ServerMessageType.RoomDetails.value, {ServerDataKey.Room.value: room_details})


def handle_create_room(user_id: str, room_name: str = ""):
    """
    处理创建房间事件
    """
    user_id = user_id.strip()
    room_name = room_name.strip()

    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户ID不能为空"})
        return
        
    # 检查玩家是否已在房间中
    existing_room_id = get_room_by_player_id(user_id)
    if existing_room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您已在房间{existing_room_id}中"})
        return
        
    # 创建新房间
    room_id = create_room(user_id, room_name)
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "创建房间失败"})
        return
    
    # 加入房间
    _join_room(room_id, user_id)
    
    # 发送房间信息给客户端
    emit(ServerMessageType.RoomCreated.value, {
        ServerDataKey.RoomID.value: room_id,
        ServerDataKey.Room.value: get_room_info(room_id)
    })
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_join_room(user_id:str, room_id:str):
    """
    处理加入房间事件
    """
    
    if not user_id or user_id.strip() == "":
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户ID不能为空"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    # 检查房间是否存在
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间{room_id}不存在"})
        return
        
    # 检查玩家是否已在房间中
    existing_room_id = get_room_by_player_id(user_id)
    if existing_room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您已在房间{existing_room_id}中"})
        return
        
    # 加入游戏房间
    success, message = _join_room(room_id, user_id)
    if not success:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: message})
        return
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_leave_room(user_id:str, room_id:str):
    """玩家主动离开房间"""

    if not room_id or not user_id:
        return
    player = find_player_in_room(room_id, user_id)
    if not player:
        return
    if is_game_started(room_id):
        print(f"游戏已开始，不能离开房间，房间号{room_id}，用户ID{user_id}")
        return
    room = rooms[room_id]
    room[RoomKey.Players.value].remove(player)

    emit(ServerMessageType.PlayerLeaved.value, {
        ServerDataKey.UserID.value: user_id,
        ServerDataKey.Username.value: player[PlayerKey.Username.value],
    })

    broadcast_game_info(room_id)


def _handle_sit_donw_or_up(user_id:str, room_id:str, is_sit_down:bool, seat_index:int)->bool:
    player = common_check(user_id, room_id, should_game_started=False)
    if not player:
        return False

    if is_sit_down:
        if seat_index < 0 or seat_index >= len(rooms[room_id][RoomKey.Seats.value]):
            emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"座位索引{seat_index}无效"})
            return False
        # 如果玩家已坐下或已准备就绪，无需坐下
        if player[PlayerKey.Status.value] in [PlayerStatus.Ready.value, PlayerStatus.Seated.value]:
            emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"玩家状态为：{player[PlayerKey.Status.value]}，无需再次坐下"})
            return False
    else:
        # 如果玩家是观众，不允许站起
        if player[PlayerKey.Status.value] == PlayerStatus.Spectator.value:
            emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "观众无法站起"})
            return False

    # 为玩家分配座位
    seat_player(room_id, player, seat_index)
    
    # 广播游戏信息
    broadcast_game_info(room_id)

    return True


def handle_sit_down(user_id:str, room_id:str, seat_index:int):
    """
    处理玩家坐下事件
    """

    
    _handle_sit_donw_or_up(user_id, room_id, True, seat_index)


def handle_stand_up(user_id:str, room_id:str):
    """
    处理玩家站起事件
    """
    
    _handle_sit_donw_or_up(user_id, room_id, False, -1)


def handle_ready(user_id:str, room_id:str, turn_ready:bool):
    """
    处理玩家准备/取消准备事件
    """
        
    # 查找玩家
    player = common_check(user_id, room_id, should_game_started=False)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您不在房间{room_id}中"})
        return False
    if player[PlayerKey.Coins.value] < rooms[room_id][RoomKey.Settings.value][RoomSettingKey.BaseBet.value]*MIN_SHOW_DOWM_TURN:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您的金币余额不足"})
        return False
    
    if turn_ready and player[PlayerKey.Status.value] != PlayerStatus.Seated.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"玩家状态为：{player[PlayerKey.Status.value]}，无法准备"})
        return False
    elif not turn_ready and player[PlayerKey.Status.value] != PlayerStatus.Ready.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"玩家状态为：{player[PlayerKey.Status.value]}，无法取消准备"})
        return False

    # 更新玩家状态
    update_player_status(room_id, user_id, PlayerStatus.Ready if turn_ready else PlayerStatus.Seated)
    
    # 广播游戏信息
    broadcast_game_info(room_id)
    # 检查是否所有玩家都已准备就绪
    check_for_new_game(room_id)


def check_for_new_game(room_id:str):
    """
    检查房间是否可以开始新游戏
    """
    room = rooms[room_id]
    if room[RoomKey.GameStatus.value] != GameStatus.Playing.value:
        return False
    if not all(player[PlayerKey.Status.value] == PlayerStatus.Ready.value for player in room[RoomKey.Players.value]):
        return False
    continue_players = [p for p in room[RoomKey.Players.value] if p[PlayerKey.Status.value] == PlayerStatus.Ready.value]
    if len(continue_players) < 2:
        for player in continue_players:
            _leave_room(room_id, player[PlayerKey.ID.value])
        print(f"房间{room_id}即将解散，因为只有 {len(continue_players)} 人选择继续游戏")
        del rooms[room_id]
        emit(ServerMessageType.RoomClosed.value, {ServerDataKey.RoomID.value: room_id}, room=room_id)
        socketio_leave_room(room=room_id)
        return False
    # 所有玩家都已准备就绪，游戏开始
    # 重置房间状态
    reset_room_for_new_game(room_id, room[RoomKey.Players.value], room[RoomKey.Seats.value])
    eventlet.spawn(start_game_loop, room_id)
    broadcast_game_info(room_id)
    return True


def start_game_loop(room_id:str):
    """
    进入游戏主循环，开始游戏
    """
    if room_id not in rooms:
        return False
    room = rooms[room_id]
    room[RoomKey.ID.value] = room_id
    room[RoomKey.GameStatus.value] = GameStatus.Playing.value
    # 为玩家发牌
    deal_cards_to_players(room_id)
    # 更新玩家状态为Playing，为每个玩家发送牌信息
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Status.value] = PlayerStatus.Playing.value
        emit(ServerMessageType.GameStarted.value, get_player_info(room_id, player[PlayerKey.ID.value], True), room=room_id)
    
    next_player_index = get_next_player_seat_index(room, room[RoomKey.LastWinner], None)
    first_player_index = next_player_index
    # 游戏主循环
    while room[RoomKey.GameStatus.value] == GameStatus.Playing.value:
        # 判断当局游戏是否可以结束
        if check_current_game_end(room):
            settle(room)
            # 在重置游戏状态前进行广播
            reset_room_when_game_end(room_id)
            broadcast_game_info(room_id)
            break
        
        # 游戏逻辑
        current_turn_player_id = get_next_online_playing_player(room[RoomKey.Seats.value], room_id, next_player_index)
        if not current_turn_player_id:
            print(f"在所有玩家中，没有找到在线的、未弃牌的玩家")
            continue

        room[RoomKey.CurrentTurnPlayerID.value] = current_turn_player_id
        current_turn_player = find_player_in_room(room_id, current_turn_player_id)[0]
        if not current_turn_player:
            print(f"在所有玩家中，没有找到玩家{current_turn_player_id}")
            continue
        player_last_coins = current_turn_player[PlayerKey.Coins.value]
        # 向玩家发送轮到行动的消息
        emit(ServerMessageType.StartTurn.value, {ServerDataKey.UserID.value: current_turn_player_id})
        
        is_player_action_done = False
        start_time = time.time()
        while time.time() - start_time < TURN_TIMEOUT:
            # 检查玩家是否行动
            if check_player_action_done(room_id, current_turn_player_id, player_last_coins):
                is_player_action_done = True
                break
            eventlet.sleep(0.2)
        if not is_player_action_done:
            # 玩家超时未行动，视为弃牌
            update_player_status(room_id, current_turn_player_id, PlayerStatus.Folded.value)
            emit(ServerMessageType.PlayerFolded.value, {ServerDataKey.UserID.value: current_turn_player_id})

        next_player_index = get_next_player_seat_index(room, current_turn_player_id, first_player_index)
    # 一局游戏结束
    
    # 等待玩家决定是否继续游戏
    room.continue_new_game_timer = eventlet.spawn_after(CONTINUE_NEW_GAME_TIMEOUT, clean_no_ready_player, room_id)
    broadcast_game_info(room_id)


def clean_no_ready_player(room_id:str):
    """
    清除房间中未准备就绪的玩家
    """
    if room_id not in rooms:
        return
    room = rooms[room_id]
    if not hasattr(room, CONTINUE_NEW_GAME_TIMER):
        return
    room.continue_new_game_timer.cancel()
    del room.continue_new_game_timer
    for player in room[RoomKey.Players.value]:
        if player[PlayerKey.Status.value] != PlayerStatus.Ready.value:
            _leave_room(room_id, player[PlayerKey.ID.value])


def deal_cards_to_players(room_id:str):
    """
    为玩家发牌
    """
    if room_id not in rooms:
        return False
    room = rooms[room_id]
    # 创建一副新牌并洗牌
    deck = shuffle_deck(create_deck())
    # 从庄家开始，按座位顺序为每个玩家发牌
    seats = room[RoomKey.Seats.value]
    # 找出room[RoomKey.Seats]中值为room[RoomKey.LastWinner]的元素的index
    last_winner_index = seats.index(room[RoomKey.LastWinner])
    reordered_deal_cards_player_id_list = seats[last_winner_index:] + seats[:last_winner_index]
    for player_id in reordered_deal_cards_player_id_list:
        player = find_player_in_room(room_id, player_id)[0]
        if player is None:
            raise ValueError(f"玩家{player_id}不在房间{room_id}中")
        if player[PlayerKey.Status.value] != PlayerStatus.Ready.value:
            raise ValueError(f"玩家{player_id}状态为：{player[PlayerKey.Status.value]}，无法发牌")

        # 从牌组中发牌
        cards, deck = deal_cards(deck)
        # 为玩家分配牌
        player[PlayerKey.Cards.value] = cards
    
    return True


def get_next_player_seat_index(room, current_turn_player_id, first_player_index):
    """
    获取下一个未被弃牌的玩家座位索引
    """
    seats = room[RoomKey.Seats.value]
    current_turn_player_seat_index = seats.index(current_turn_player_id)
    next_index = (current_turn_player_seat_index + 1) % len(seats)
    if next_index == first_player_index:
        room[RoomKey.CurrentRound] += 1
    return next_index


def get_next_online_playing_player(seats:list, room_id:str, start_player_index:int)->str:
    """
    获取下一个未被弃牌的玩家ID
    """
    for i in range(len(seats)):
        player_id = seats[(start_player_index + i) % len(seats)]
        player = find_player_in_room(room_id, player_id)[0]
        if player is None:
            print(f"玩家{player_id}不在房间{room_id}中")
        if player[PlayerKey.Status.value] == PlayerStatus.Playing.value:
            if player[PlayerKey.OnlineStatus.value] == OnlineStatus.Online.value:
                return player_id
            elif player[PlayerKey.OnlineStatus.value] == OnlineStatus.LostConnection.value:
                start_time = time.time()
                while time.time() - start_time < INNER_TURN_LOST_RECONNECT_TIMEOUT:
                    player = find_player_in_room(room_id, player_id)[0]
                    if player is None:
                        print(f"玩家{player_id}不在房间{room_id}中")
                        break
                    if player[PlayerKey.Status.value] == PlayerStatus.Playing.value \
                        and player[PlayerKey.OnlineStatus.value] == OnlineStatus.Online.value:
                        return player_id
                    eventlet.sleep(0.2)

                player = find_player_in_room(room_id, player_id)[0]
                if player is not None:
                    player[PlayerKey.Status.value] = PlayerStatus.Folded.value

    return None


def check_player_action_done(room_id:str, current_turn_player_id:str, player_last_coins:int):
    """
    检查玩家是否完成行动
    """
    # 从房间中获取玩家
    player = find_player_in_room(room_id, current_turn_player_id)[0]
    if player is None:
        print(f"玩家{current_turn_player_id}不在房间{room_id}中")
        return True
    
    # 如果玩家的金币减少了或玩家弃牌，则视为行动完成
    if player[PlayerKey.Coins.value] < player_last_coins \
        or player[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        return True
    return False


def check_current_game_end(room):
    """
    检查当局游戏是否可以结束。如果所有玩家离线且在 达到手数（轮数）上限、达到奖池上限或只剩一个玩家没有弃牌，则游戏结束。
    """
    # 检查是否达到手数（轮数）上限
    if room[RoomKey.CurrentRound.value] >= room[RoomKey.Settings.value][RoomSettingKey.MaxRounds.value]:
        return True
    # 检查是否达到奖池上限
    if room[RoomKey.Pot.value] >= room[RoomKey.Settings.value][RoomSettingKey.MaxPotAmount.value]:
        return True
    # 检查是否最多只剩一个玩家没有弃牌
    players = room[RoomKey.Players.value]
    playing_players = get_playing_players(players)
    if len(playing_players) <= 1:
        return True

    return False


def settle(room:str):
    """游戏结算，更新金币。"""
    # 找到游戏赢家
    playing_players = get_playing_players(room[RoomKey.Players.value])
    if len(playing_players) == 0:
        print("本局无赢家")
        room[RoomKey.LastWinner.value] = None
        room[RoomKey.Pot.value] = 0 
        return
    winner_player_list:list = []
    if len(playing_players) == 1:
        winner_player_list.append(playing_players[0])
    else:
        # 比较玩家的牌的大小
        card_list = [player[PlayerKey.Cards.value] for player in playing_players]
        winner_hand_index_list = compare_hands(card_list, raise_compare_hand_index=None, 
            isDiffentSuit235GreaterThanThreeOfAKind=room[RoomKey.Settings.value][RoomSettingKey.IsDiffentSuit235GreaterThanThreeOfAKind.value], 
            is_A23_as_straight=room[RoomKey.Settings.value][RoomSettingKey.IsA23AsStraight.value]
        )
        for winner_hand_index in winner_hand_index_list:
            winner_player_list.append(playing_players[winner_hand_index])

    # 如果有多个赢家，随机选择一个
    room[RoomKey.LastWinner.value] = winner_player_list[random.randint(0, len(winner_player_list) - 1)][PlayerKey.ID.value]
    # 计算每个赢家的金币奖励
    pot_amount = room[RoomKey.Pot.value]
    # 除不尽的金币丢弃
    winner_coins = pot_amount // len(winner_player_list)
    for winner_player in winner_player_list:
        winner_player[PlayerKey.Coins.value] += winner_coins
    room[RoomKey.Pot.value] = 0 


def handle_update_settings(user_id:str, room_id:str, settings:dict):
    """
    处理更新房间设置事件（仅房主可操作）
    """
    
    player = common_check(user_id, room_id, should_game_started=False)
    if not player:
        return False

    if not settings:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间设置不能为空"})
        return False
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "只有房主可以更改房间设置"})
        return
        
    # 更新房间设置
    success, message = update_room_settings(room_id, settings)
    if not success:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: message})
        return
        
    emit(ServerMessageType.SettingsUpdated.value, {ServerDataKey.Settings.value: get_room_info(room_id)[RoomKey.Settings.value]})
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_kick_player(user_id:str, room_id:str, to_be_kicked_user_id:str):
    """
    处理踢出玩家事件（仅房主可操作）
    """
    
    player = common_check(user_id, room_id, should_game_started=False)
    if not player:
        return False        
        
    if not to_be_kicked_user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "要踢出的玩家ID不能为空"})
        return False
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "只有房主可以踢出玩家"})
        return False
        
    # 不能踢出自己
    if user_id == to_be_kicked_user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "不能踢出自己"})
        return False
        
    # 检查目标玩家是否在房间中
    player_to_be_kicked = get_player_info(room_id, to_be_kicked_user_id)
    if not player_to_be_kicked:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"要踢出的玩家{to_be_kicked_user_id}不在房间{room_id}中"})
        return False
    # 即便玩家已经就绪也可以踢出，可以踢出不喜欢的玩家
    # 踢出玩家
    _leave_room(room_id, to_be_kicked_user_id)
    # 离开Socket.IO通信房间
    socketio_leave_room(room=room_id, sid=to_be_kicked_user_id)
    
    emit(ServerMessageType.PlayerKicked.value, {ServerDataKey.UserID.value: to_be_kicked_user_id})
    # 广播游戏信息
    broadcast_game_info(room_id)
    

def handle_continue_game(user_id:str, room_id:str, continue_game:bool):
    """
    处理游戏继续/退出选择。当一局游戏结束后，玩家的状态被设置为Seated，如果玩家选择继续游戏，状态被设置为Ready。
    """

    player = common_check(user_id, room_id, should_game_started=False)
    if not player:
        return False
        
    # 更新玩家状态
    if not continue_game:
        # 玩家选择不继续游戏，从房间中移除
        _leave_room(room_id, user_id)
        return
        
    update_player_status(room_id, user_id, PlayerStatus.Ready.value)
    
    # 广播游戏信息
    broadcast_game_info(room_id)

    check_for_new_game(room_id)


def handle_set_avatar(user_id:str, avatar_url:str):
    """
    处理设置头像事件
    """
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
    if not avatar_url:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "头像URL不能为空"})
        return

        
    # 更新玩家头像
    user_info = get_user_info(user_id)
    if not user_info:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户不存在"})
        return
    
    # 更新用户头像
    user_info[UserKey.AvatarURL.value] = avatar_url
    #set_user_info(user_id, user_info)

    emit(ServerMessageType.AvatarSet.value, {ServerDataKey.UserID.value: user_id, ServerDataKey.AvatarURL.value: avatar_url})


def allowed_file(filename):
    """
    检查文件是否为允许的图片类型
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


