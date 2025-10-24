# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏事件处理模块
包含所有Socket.IO事件处理函数
"""

import array
import os
import time
import uuid
from flask import request, session, send_from_directory
from flask_socketio import emit, join_room as socketio_join_room, leave_room as socketio_leave_room

# 导入模块
from game_enum import ClientDataKey, ServerMessageType, RoomStatus, SessionKey, PlayerStatus, ServerDataKey
from old.app import get_player_info, room
from room_manager import (
    find_next_seated_and_online_player, find_player_in_room, get_player_count, get_room_players, rooms, RoomKey, PlayerKey, GameStatus, RoomSettingKey,
    reset_room_for_new_game, get_player_info_without_cards, create_room, join_room as game_join_room,
    leave_room as game_leave_room, update_player_online_status, get_room_list, get_room_details,
    update_room_settings, get_room_owner, is_room_owner, get_active_players,
    get_online_players, count_ready_players, add_game_log
)
from utils import (
    broadcast_game_info, broadcast_room_updated_with_player_bets,
    create_deck, shuffle_deck, deal_cards, determine_winner, next_turn, end_game,
    allowed_file, get_room_by_player_id, is_player_in_room,
    is_game_started, is_player_turn, is_player_folded, get_player_cards,
    update_player_coins, update_player_bet, update_player_folded,
    update_player_looked_at_cards, add_to_pot,
    set_current_bet, get_pot, get_current_bet, get_player_by_id,
    get_current_player, set_current_turn_player, set_game_status, get_game_status,
    get_room_settings
)
from game_logic import compare_hands


# Socket.IO事件处理函数
def handle_connect():
    """
    处理客户端连接/重连事件
    """
    # 尝试从session中获取现有user_id（用于重连情况）
    existing_user_id = session.get(SessionKey.UserID.value, None)
    user_id = None
    if existing_user_id:
        user_id = existing_user_id
        print(f"用户{user_id}重连")
    else:
        # 如果是新连接（session中没有user_id），或者用户是第一次连接（localStorage中没有user_id）
        # 则生成新的UUID作为user_id
        user_id = str(uuid.uuid4())
        print(f"用户{user_id}连接")
    
    # 更新session中的user_id
    session[SessionKey.UserID.value] = user_id
    
    # 向客户端发送连接成功消息，包含user_id
    emit(ServerMessageType.Connected.value, {"user_id": user_id})
    
    # 检查玩家是否已经在某个房间中，这是为了处理玩家断线重连的情况
    room_id = get_room_by_player_id(user_id)
    
    if room_id and room_id in rooms:
        room = rooms[room_id]
        
        # 无论房间状态如何，都更新玩家在线状态
        update_player_online_status(room_id, user_id, True)
        
        # 如果房间状态是等待结束，且有玩家重新连接，恢复游戏状态
        if room[RoomKey.Status.value] == RoomStatus.WaitingToDestroy.value:
            # 恢复房间状态为正常状态
            room[RoomKey.Status.value] = RoomStatus.Normal.value
            add_game_log(room_id, f"玩家 {user_id} 重新连接，游戏继续")
        
        # 无论房间状态如何，都广播游戏信息以更新玩家在线状态
        broadcast_game_info(room_id)


def handle_disconnect(reason):
    """
    处理客户端断开连接事件
    
    Args:
        reason: 断开连接的原因，用于区分主动断开和网络不佳导致的断开
    """
    user_id = session.get(SessionKey.UserID.value)
    if not user_id:
        return
        
    # 查找玩家所在的房间
    room_id = get_room_by_player_id(user_id)
    if not room_id:
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
    
    # 如果是主动断开连接，将玩家移出房间
    if not is_network_issue:
        # 先检查房间是否仍然存在
        if room_id in rooms:
            # 获取玩家信息用于日志
            player = get_player_by_id(room_id, user_id)
            player_name = player if player else f"玩家{user_id}"
            
            # 添加离开房间的日志
            add_game_log(room_id, f"{player_name} 主动离开，已移出房间")
            
            # 执行离开房间逻辑
            try:
                # 离开Socket.IO通信房间
                socketio_leave_room(room_id)
                # 离开游戏房间，调用room_manager.py的leave_room函数（导入时重命名为game_leave_room）
                game_leave_room(room_id, user_id)
                print(f"已将用户{user_id}移出房间{room_id}")
            except Exception as e:
                print(f"移出用户{user_id}时出错: {e}")
        
        # 对于主动离开的玩家，需要广播游戏信息
        broadcast_game_info(room_id)
        return
    
    # 对于网络问题断开的玩家，仅更新在线状态，保留在房间中等待重连
    update_player_online_status(room_id, user_id, False)
    
    # 如果游戏已开始且当前玩家是断线的玩家
    if is_game_started(room_id) and is_player_turn(room_id, user_id):
        # 添加网络中断的游戏日志
        player = get_player_by_id(room_id, user_id)
        if player:
            add_game_log(room_id, f"{player} 网络连接中断，等待重连...")
        
        # 自动弃牌并进入下一个玩家
        update_player_folded(room_id, user_id, True)
        next_turn(room_id)
    else:
        # 如果不是当前回合玩家，也记录网络中断日志
        player = get_player_by_id(room_id, user_id)
        if player and is_game_started(room_id):
            add_game_log(room_id, f"{player} 网络连接中断")
    
    # 广播游戏信息，更新其他玩家看到的状态
    broadcast_game_info(room_id)


def handle_set_username(data: dict):
    """
    处理设置用户名事件
    """
    username = data.get(ClientDataKey.Username.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    user_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    if not room_id or not user_id or not username:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID、玩家ID、用户昵称不能为空"})
        return
    player = find_player_in_room(room_id, user_id)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"在房间{room_id}中没有找到玩家{user_id}"})
        return
        
    session[SessionKey.Username.value] = username
    player[PlayerKey.Username.value] = username
    emit(ServerMessageType.UsernameSet.value, {ServerDataKey.Username.value: username})


def handle_create_room():
    """
    处理创建房间事件
    """
    user_id = session.get(SessionKey.UserID.value)
    username = session.get(SessionKey.Username.value)

    if not user_id or not username:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "请先设置用户名"})
        return
        
    # 检查玩家是否已在房间中
    existing_room_id = get_room_by_player_id(user_id)
    if existing_room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您已在房间{existing_room_id}中"})
        return
        
    # 创建新房间
    room_id = create_room(user_id, username)
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "创建房间失败"})
        return
    
    # 加入Socket.IO通信房间
    socketio_join_room(room_id)
    
    # 发送房间信息给客户端
    emit(ServerMessageType.RoomCreated.value, {
        ServerDataKey.RoomID.value: room_id,
        ServerDataKey.Room.value: get_room_details(room_id)
    })
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_join_room(data: dict):
    """
    处理加入房间事件
    """
    user_id = session.get(SessionKey.UserID.value)
    username = session.get(SessionKey.Username.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id or not username:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "请先设置用户名"})
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
    result = game_join_room(room_id, user_id, username)
    if not result[0]:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"加入房间{room_id}失败， 原因：{result[1]}"})
        return
        
    # 加入Socket.IO通信房间
    socketio_join_room(room_id)
    
    # 发送房间加入消息给客户端
    emit(ServerMessageType.RoomJoined.value, {
        ServerDataKey.RoomID.value: room_id,
        ServerDataKey.Room.value: get_room_details(room_id)
    })
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_leave_room():
    """
    处理离开房间事件
    """
    user_id = session.get(SessionKey.UserID.value)
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    # 查找玩家所在的房间
    room_id = get_room_by_player_id(user_id)
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您不在任何房间中"})
        return
    
    player = find_player_in_room(room_id, user_id)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"在房间{room_id}中没有找到玩家{user_id}"})
        return

    # 如果游戏已开始且玩家未弃牌，不允许离开，主动关闭页面或刷新页面就没法防住了
    if is_game_started(room_id) and not player[PlayerKey.Folded.value]:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始且玩家未弃牌，无法离开房间"})
        return
        
    # 离开游戏房间
    result = game_leave_room(room_id, user_id)
    if not result[0]:
        return
    
    # 离开Socket.IO通信房间
    socketio_leave_room(room_id)
    
    # 发送离开成功消息
    emit(ServerMessageType.RoomLeft.value, {ServerDataKey.RoomID.value: room_id})
    
    # 如果房间还存在，广播游戏信息
    if room_id in rooms:
        broadcast_game_info(room_id)


def handle_get_room_list():
    """
    处理获取房间列表事件
    """
    emit(ServerMessageType.RoomList.value, {ServerDataKey.RoomList.value: get_room_list()})


def handle_get_room_details(data:dict):
    """
    处理获取房间详情事件
    """
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    room_details = get_room_details(room_id)
    if not room_details:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return
        
    emit(ServerMessageType.RoomDetails.value, {ServerDataKey.Room.value: room_details})


def handle_sit_down(data:dict):
    """
    处理玩家坐下事件
    """
    user_id = session.get(SessionKey.UserID.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    seat_index = int(data.get(ClientDataKey.SeatIndex.value, -1).strip())
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return
        
    if is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始，无法坐下"})
        return
    
    if seat_index < 0 or seat_index >= len(rooms[room_id][RoomKey.Seats.value]):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"座位索引{seat_index}无效"})
        return


    # 查找玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您不在此房间{room_id}中"})
        return
        
    # 如果玩家已坐下或已准备就绪，无需坐下
    if player[PlayerKey.Status.value] in [PlayerStatus.Ready.value, PlayerStatus.Seated.value]:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"玩家状态为：{player[PlayerKey.Status.value]}，无需再次坐下"})
        return
        
    # 为玩家分配座位
    seat_player(room_id, player, seat_index)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_stand_up(data:dict):
    """
    处理玩家站起事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return
        
    if is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始，无法站起"})
        return
        
    # 查找玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您不在房间{room_id}中"})    
        return
    
    # 如果玩家是观众，不允许站起
    if player[PlayerKey.Status.value] == PlayerStatus.Spectator.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "观众无法站起"})
        return

    # 让玩家离开座位，并更新玩家状态为观众
    seat_player(room_id, player, -1)
    
    # 广播游戏信息
    broadcast_game_info(room_id)

def seat_player(room_id:str, player:dict, new_seat_index:int=-1):
    """
    为玩家分配座位。如果new_seat_index为-1，则让玩家起立。
    """
    if room_id not in rooms:
        return False
    
    seats = rooms[room_id][RoomKey.Seats.value]
    if new_seat_index >= len(seats):
        return False
    
    # 查看玩家是否已在座位上
    for seat_index, seated_player_id in enumerate(seats):
        if seated_player_id != player[PlayerKey.ID.value]:
            continue
        # 玩家已坐在某个座位上
        if seat_index == new_seat_index:# 玩家现在坐的位置和想要坐的位置一样
            # 玩家已在指定座位上
            print(f"玩家{player}已在座位{new_seat_index}上")
            return True
        else:# 玩家现在坐的位置和想要坐的位置不一样
            seats[seat_index] = None # 从原座位上离开
            if new_seat_index < 0:
                # 玩家要站起来
                print(f"玩家{player}要站起来")
                # 更新玩家状态
                player[PlayerKey.Status.value] = PlayerStatus.Spectator.value
                return True
            
            print(f"玩家{player}要坐到座位{new_seat_index}上，当前位置为{seat_index}")
            break
            
    seats[new_seat_index] = player[PlayerKey.ID.value]
    # 更新玩家状态
    player[PlayerKey.Status.value] = PlayerStatus.Seated.value
    return True

def handle_ready(data:dict):
    """
    处理玩家准备/取消准备事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    want_ready = data.get(ClientDataKey.Ready.value, True)
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return
        
    if is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始，无法更改准备状态"})
        return
        
    # 查找玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"您不在房间{room_id}中"})
        return
        
    if want_ready and player[PlayerKey.Status.value] != PlayerStatus.Seated.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"玩家状态为：{player[PlayerKey.Status.value]}，无法准备"})
        return
    elif not want_ready and player[PlayerKey.Status.value] != PlayerStatus.Ready.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"玩家状态为：{player[PlayerKey.Status.value]}，无法取消准备"})
        return

    # 更新玩家状态
    status = PlayerStatus.Ready.value if want_ready else PlayerStatus.Seated.value
    update_player_online_status(room_id, user_id, status)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_update_settings(data:dict):
    """
    处理更新房间设置事件（仅房主可操作）
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    settings = data.get(ClientDataKey.Settings.value, None)
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return

    if not settings:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间设置不能为空"})
        return
        
    if is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始，无法更改设置"})
        return
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "只有房主可以更改房间设置"})
        return
        
    # 更新房间设置
    if not update_room_settings(room_id, settings):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "设置更新失败，请检查设置参数"})
        return
        
    # 广播游戏信息
    broadcast_game_info(room_id)
    
    emit(ServerMessageType.SettingsUpdated.value, {ServerDataKey.Settings.value: get_room_settings(room_id)})


def handle_kick_player(data:dict):
    """
    处理踢出玩家事件（仅房主可操作）
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    to_kick_player_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if not to_kick_player_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "目标玩家ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return
        
    if is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始，无法踢出玩家"})
        return
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "只有房主可以踢出玩家"})
        return
        
    # 不能踢出自己
    if user_id == to_kick_player_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "不能踢出自己"})
        return
        
    # 检查目标玩家是否在房间中
    player_to_be_kicked = get_player_by_id(room_id, to_kick_player_id)
    if not player_to_be_kicked:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"要踢出的玩家{to_kick_player_id}不在房间{room_id}中"})
        return
    # 即便玩家已经就绪也可以踢出，可以踢出不喜欢的玩家
    # 踢出玩家
    game_leave_room(room_id, to_kick_player_id)
    socketio_leave_room(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)
    
    emit(ServerMessageType.PlayerKicked.value, {ServerDataKey.PlayerID.value: to_kick_player_id})


def handle_start_game(data:dict):
    """
    处理开始游戏事件（仅房主可操作）
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return False
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return False
    room = rooms[room_id]
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return False
        
    if is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始"})
        return False
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "只有房主可以开始游戏"})
        return False
        
    # 检查是否有足够的玩家
    min_players = 2
    player_count = get_player_count(room_id)
    if player_count < min_players:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"至少需要{min_players}名玩家才能开始游戏"})
        return False
        
    # 检查所有玩家是否都已准备
    ready_players = count_ready_players(room_id)
    if ready_players != player_count:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"已准备玩家{ready_players}名，需要{player_count}名玩家都完成准备"})
        return False
        
    # 开始游戏
    set_game_status(room_id, GameStatus.Playing.value)
    
    # 创建并洗牌
    deck = shuffle_deck(create_deck())
    
    # 发牌
    players = get_room_players(room_id)
    
    for player in players:
        cards, deck = deal_cards(deck, 3)
        player[PlayerKey.Cards.value] = cards
        print(f"玩家{player[PlayerKey.Username.value]}被发到的牌：{cards}")
        player[PlayerKey.HasLookedAtCards.value] = False
    
    # 设置当前玩家（房主的下一个玩家）
    room_owner_id = user_id
    
    if room_owner_id is None:
        print(f"房主ID为空， userId：{user_id}")
        return False
    ###################################################
    # 添加游戏日志
    add_game_log(room_id, "游戏开始")
    
    # 广播游戏信息
    broadcast_game_info(room_id)

    # 每名玩家应该先交底注
    for seated_user_id in room[RoomKey.Seats.value]:
        if seated_user_id is not None:
            #emit(ServerMessageType.DiscloseBet.value, {ServerDataKey.PlayerID.value: seated_user_id})
            player = find_player_in_room(room_id, seated_user_id)
            if not player:
                continue
            base_bet = room[RoomKey.Settings][RoomSettingKey.BaseBet.value]
            player[PlayerKey.Coins.value] -= base_bet
            add_game_log(room_id, f"{player[PlayerKey.Username.value]} 交了{base_bet}个金币作为底注")
            room[RoomKey.Pot.value] += base_bet
            add_game_log(room_id, f"当前游戏池金额为{room[RoomKey.Pot.value]}")
            # 广播游戏信息
            broadcast_game_info(room_id)


    # 找到下一个在座位上的、在线的玩家
    next_turn_player, next_turn_index = find_next_seated_and_online_player(room[RoomKey.Seats.value], room_owner_id)

    # 设置到达了玩家的回合
    set_current_turn_player(room_id, next_turn_player[PlayerKey.ID.value])
    # 发送start_turn事件，通知前端轮到当前回合玩家行动
    emit(ServerMessageType.StartTurn.value, {
        ServerDataKey.PlayerID.value: next_turn_player[PlayerKey.ID.value],
        ServerDataKey.PlayerName.value: next_turn_player[PlayerKey.Username.value],
        ServerDataKey.ActivePlayersCount.value: len([p for p in room[RoomKey.Players.value] if p[PlayerKey.IsOnline.value]])
    }, room=room_id)
    

    # 重置当前回合
    rooms[room_id][RoomKey.CurrentRound.value] = 1
    
    # 广播游戏信息
    broadcast_game_info(room_id)
    
    emit(ServerMessageType.GameStarted.value, {ServerDataKey.RoomID.value: room_id})


def handle_look_at_cards(data:dict):
    """
    处理玩家看牌事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间不存在"})
        return
        
    if not is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏未开始"})
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"不是用户{user_id}的回合"})
        return
        
    # 检查玩家是否已弃牌
    if is_player_folded(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌，无法看牌"})
        return
        
    # 获取玩家手牌
    cards = get_player_cards(room_id, user_id)
    if not cards:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"无法获取用户{user_id}的手牌"})
        return
        
    # 更新玩家看牌状态
    update_player_looked_at_cards(room_id, user_id, True)
    
    # 发送手牌给玩家
    emit(ServerMessageType.ShowCards.value, {ServerDataKey.Cards.value: cards}, to=user_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_fold(data:dict):
    """
    处理玩家弃牌事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户未登录"})
        return
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间{room_id}不存在"})
        return
        
    if not is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏未开始"})
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "不是您的回合"})
        return
        
    # 检查玩家是否已弃牌
    if is_player_folded(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌"})
        return
        
    # 弃牌
    update_player_folded(room_id, user_id, True)
    
    # 添加游戏日志
    player = get_player_by_id(room_id, user_id)
    if player:
        add_game_log(room_id, f"{player[PlayerKey.Username.value]} 弃牌")
    
    # 检查是否只剩一个玩家未弃牌
    active_players = get_active_players(room_id)
    if len(active_players) == 1:
        # 游戏结束，确定胜利者
        determine_winner(room_id)
    else:
        # 进入下一个玩家的回合
        next_turn(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_call(data:dict):
    """
    处理玩家跟注事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    if not is_game_started(room_id):
        emit("error", {"message": "游戏未开始"})
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit("error", {"message": "不是您的回合"})
        return
        
    # 检查玩家是否已弃牌
    if is_player_folded(room_id, user_id):
        emit("error", {"message": "您已弃牌，无法跟注"})
        return
        
    # 获取玩家和当前下注信息
    player = get_player_by_id(room_id, user_id)
    current_bet = get_current_bet(room_id)
    
    if not player:
        emit("error", {"message": "无法获取玩家信息"})
        return
        
    # 计算需要跟注的金额
    call_amount = current_bet - player[PlayerKey.CurrentBet.value]
    
    # 检查玩家是否有足够的金币
    if player[PlayerKey.Chips.value] < call_amount:
        emit("error", {"message": "金币不足，无法跟注"})
        return
        
    # 扣除金币并更新下注
    update_player_coins(room_id, user_id, -call_amount)
    update_player_bet(room_id, user_id, current_bet)
    add_to_pot(room_id, call_amount)
    
    # 添加游戏日志
    add_game_log(room_id, f"{player[PlayerKey.Username.value]} 跟注 {call_amount}")
    
    # 广播下注信息
    broadcast_room_updated_with_player_bets(room_id)
    
    # 进入下一个玩家的回合
    next_turn(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_raise(data:dict):
    """
    处理玩家加注事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    amount = data.get(ClientDataKey.Amount.value, 0)
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    if not is_game_started(room_id):
        emit("error", {"message": "游戏未开始"})
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit("error", {"message": "不是您的回合"})
        return
        
    # 检查玩家是否已弃牌
    if is_player_folded(room_id, user_id):
        emit("error", {"message": "您已弃牌，无法加注"})
        return
        
    # 检查加注金额是否有效
    if amount <= 0:
        emit("error", {"message": "加注金额必须大于0"})
        return
        
    # 获取玩家和当前下注信息
    player = get_player_by_id(room_id, user_id)
    current_bet = get_current_bet(room_id)
    
    if not player:
        emit("error", {"message": "无法获取玩家信息"})
        return
        
    # 计算总下注金额
    total_bet = current_bet + amount
    
    # 计算需要支付的金额
    pay_amount = total_bet - player[PlayerKey.CurrentBet.value]
    
    # 检查玩家是否有足够的金币
    if player[PlayerKey.Chips.value] < pay_amount:
        emit("error", {"message": "金币不足，无法加注"})
        return
        
    # 扣除金币并更新下注
    update_player_coins(room_id, user_id, -pay_amount)
    update_player_bet(room_id, user_id, total_bet)
    add_to_pot(room_id, pay_amount)
    set_current_bet(room_id, total_bet)
    
    # 添加游戏日志
    add_game_log(room_id, f"{player[PlayerKey.Username.value]} 加注到 {total_bet}")
    
    # 广播下注信息
    broadcast_room_updated_with_player_bets(room_id)
    
    # 进入下一个玩家的回合
    next_turn(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_showdown(data:dict):
    """
    处理玩家开牌事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    if not is_game_started(room_id):
        emit("error", {"message": "游戏未开始"})
        return
        
    # 检查玩家是否已弃牌
    if is_player_folded(room_id, user_id):
        emit("error", {"message": "您已弃牌，无法开牌"})
        return
        
    # 检查是否所有玩家都已看牌
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.IsOnline.value] and not player[PlayerKey.Folded.value] and not player[PlayerKey.HasLookedAtCards.value]:
            emit("error", {"message": "还有玩家未看牌，无法开牌"})
            return
    
    # 设置游戏状态为等待玩家决策
    set_game_status(room_id, GameStatus.Wating.value)
    
    # 确定胜利者
    determine_winner(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_continue_game(data:dict):
    """
    处理游戏继续/退出选择
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    continue_game = data.get(ClientDataKey.ContinueGame.value, False)
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    # 获取玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit("error", {"message": "您不在此房间中"})
        return
        
    # 更新玩家状态
    from game_enum import PlayerStatus
    if continue_game:
        update_player_online_status(room_id, user_id, PlayerStatus.Ready.value)
    else:
        # 玩家选择不继续游戏，从房间中移除
        game_leave_room(room_id, user_id)
        socketio_leave_room(room_id)
        # 广播游戏信息
        broadcast_game_info(room_id)
        return
    
    # 处理游戏继续决策
    from utils import try_start_new_game_when_all_decided
    try_start_new_game_when_all_decided(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_set_avatar(data:dict):
    """
    处理设置头像事件
    """
    user_id = session.get(SessionKey.UserID.value)
    avatar_url = data.get(ClientDataKey.AvatarURL.value, "").strip()
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    # 查找玩家所在的房间
    room_id = get_room_by_player_id(user_id)
    if not room_id:
        emit("error", {"message": "您不在任何房间中"})
        return
        
    # 更新玩家头像
    player = get_player_by_id(room_id, user_id)
    if player:
        player[PlayerKey.Avatar.value] = avatar_url
        
        # 广播游戏信息
        broadcast_game_info(room_id)
        
        emit("avatar_set", {"avatar_url": avatar_url})