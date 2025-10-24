# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏工具函数模块
包含广播函数和辅助函数
"""

import random
import threading
import time
from flask import request, session
from flask_socketio import emit, join_room, leave_room

# 导入全局变量和模块
from game_enum import ServerDataKey, RoomSettingKey, RoomStatus, PlayerStatus, ServerMessageType
from room_manager import find_next_seated_and_online_player, get_active_players, get_room_players, reset_room_for_game_end, rooms, RoomKey, PlayerKey, GameStatus, get_player_info_without_cards, add_game_log
from game_logic import compare_hands, SUITS, RANKS

# 决定是否继续游戏的倒计时，如果倒计时结束玩家没有做出选择，则认为他不继续下一局
ContinueTimerName = "continue_timer"
# 继续游戏倒计时秒数
ContinueTimerSeconds = 10

def broadcast_game_info(room_id):
    """
    向房间内所有玩家广播游戏信息
    """
    if room_id not in rooms:
        return
        
    room = rooms[room_id]
    players_info = []
    
    for player in room[RoomKey.Players.value]:
        player_info = get_player_info_without_cards(room_id, player[PlayerKey.ID.value])
        players_info.append(player_info)
    
    emit(ServerMessageType.GameInfo.value, {
        ServerDataKey.RoomID.value: room_id,
        ServerDataKey.Players.value: players_info,
        ServerDataKey.Status.value: room[RoomKey.Status.value],
        ServerDataKey.CurrentTurnPlayerID.value: room[RoomKey.CurrentTurnPlayerID.value],
        ServerDataKey.Pot.value: room[RoomKey.Pot.value],
        ServerDataKey.CurrentBet.value: room[RoomKey.CurrentBet.value],
        ServerDataKey.CurrentRound.value: room[RoomKey.CurrentRound.value],
        ServerDataKey.GameLog.value: room[RoomKey.GameLog.value],
        ServerDataKey.Settings.value: room[RoomKey.Settings.value],
    }, room=room_id)


def broadcast_room_updated_with_player_bets(room_id):
    """
    向房间内所有玩家广播更新后的玩家下注信息
    """
    if room_id not in rooms:
        return
        
    room = rooms[room_id]
    players_info = []
    
    for player in room[RoomKey.Players.value]:
        player_info = get_player_info_without_cards(room_id, player[PlayerKey.ID.value])
        players_info.append(player_info)
    
    emit(ServerMessageType.RoomUpdatedWithPlayerBets.value, {
        ServerDataKey.RoomID.value: room_id,
        ServerDataKey.Players.value: players_info,
        ServerDataKey.Pot.value: room[RoomKey.Pot.value],
        ServerDataKey.CurrentBet.value: room[RoomKey.CurrentBet.value],
        ServerDataKey.CurrentTurnPlayerID.value: room[RoomKey.CurrentTurnPlayerID.value],
    }, room=room_id)


def create_deck():
    """
    创建一副扑克牌
    返回包含52张牌的列表
    """
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append((rank, suit))
    return deck


def shuffle_deck(deck):
    """
    洗牌，
    返回洗牌后的牌组
    """
    random.shuffle(deck)
    return deck


def deal_cards(deck, num_cards=3):
    """
    从牌组中发牌，
    参数：
        deck: 牌组列表
        num_cards: 要发的牌数，默认3张
    返回：
        发出的牌列表和剩余牌组
    """
    if len(deck) < num_cards:
        return [], deck
        
    cards = deck[:num_cards]
    remaining_deck = deck[num_cards:]
    return cards, remaining_deck


def determine_winner(room_id):
    """
    确定游戏胜利者
    比较所有未弃牌玩家的手牌，确定胜利者并分配奖池
    """
    if room_id not in rooms:
        return
        
    room = rooms[room_id]
    
    # 获取所有未弃牌的玩家
    active_players = get_active_players(room_id)
    
    # 如果只有一个玩家未弃牌，直接获胜
    if len(active_players) == 1:
        winner = active_players[0]
        pot = room[RoomKey.Pot.value]
        winner[PlayerKey.Coins.value] += pot
        room[RoomKey.Pot.value] = 0
        # 添加游戏日志
        add_game_log(room_id, f"{winner[PlayerKey.Username.value]} 获胜，赢得 {room[RoomKey.Pot.value]} 金币")
        
        # 重置游戏状态
        reset_room_for_game_end(room_id, winner[PlayerKey.ID.value])
        
        # 广播游戏结果
        emit(ServerMessageType.GameOver.value, {
            ServerDataKey.Winner.value: winner[PlayerKey.ID.value],
            ServerDataKey.WinnerUsername.value: winner[PlayerKey.Username.value],
            ServerDataKey.Pot.value: pot,
            ServerDataKey.Reason.value: "其他玩家都已弃牌"
        }, room=room_id)
        
        # 启动10秒倒计时，等待玩家选择是否继续
        start_continue_timer(room_id)
        
        # 广播游戏信息
        broadcast_game_info(room_id)
        return
    
    # 多个玩家未弃牌，比较手牌
    hands = []
    for player in active_players:
        hands.append(player[PlayerKey.Cards.value])
    
    # 比较手牌
    winner_index = compare_hands(*hands)
    winner = active_players[winner_index]
    
    # 分配奖池
    winner[PlayerKey.Coins.value] += room[RoomKey.Pot.value]
    
    # 添加游戏日志
    room[RoomKey.GameLog.value].append({
        "message": f"{winner[PlayerKey.Username.value]} 获胜，赢得 {room[RoomKey.Pot.value]} 金币",
        "timestamp": str(uuid.uuid4()),
    })
    
    # 重置游戏状态
    room[RoomKey.Status.value] = RoomStatus.Normal.value
    
    # 设置所有玩家的状态为seated
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Status.value] = PlayerStatus.Seated.value
    
    # 广播游戏结果
    emit("game_over", {
        "winner": winner[PlayerKey.ID.value],
        "winner_username": winner[PlayerKey.Username.value],
        "pot": room[RoomKey.Pot.value],
        "reason": "手牌最大"
    }, room=room_id)
    
    # 启动10秒倒计时，等待玩家选择是否继续
    start_continue_timer(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def try_start_new_game_when_all_decided(room_id):
    """
    当所有还在房间中的玩家都已做出选择（包括离线玩家），尝试开始新一局游戏。
    如果同意继续新一局游戏的人数不足2人，将解散房间
    """
    if room_id not in rooms:
        return False
        
    # 检查是否所有玩家都已做出选择（包括离线玩家）
    from room_manager import reset_room_for_new_game
    from event_handlers import broadcast_game_info
    
    # 获取所有玩家，而不仅仅是在线玩家
    all_players = rooms[room_id][RoomKey.Players.value]
    all_decided = True
    
    # 检查是否所有玩家都已做出选择（状态为ready或已离开）
    all_decided = True
    for p in all_players:
        # 当一局游戏结束后，玩家的状态为Seated，如果玩家选择继续，状态为Ready，否则玩家会被移出房间
        if p[PlayerKey.Status.value] != PlayerStatus.Ready.value:
            all_decided = False
            break
    
    # 如果此时还是有玩家没有做出选择，无法开始下一局游戏
    if not all_decided:
        return False
    
    # 统计选择继续的玩家（包括在线和离线但选择继续的玩家）
    continue_players = [p for p in all_players if p[PlayerKey.Status.value] == PlayerStatus.Ready.value]
    
    # 取消继续游戏定时器
    if hasattr(rooms[room_id], ContinueTimerName):
        rooms[room_id].continue_timer = None

    if len(continue_players) >= 2:  # 至少需要2个玩家才能继续游戏
        # 重置房间状态
        reset_room_for_new_game(room_id)
        
        # 广播游戏信息
        broadcast_game_info(room_id)
        
        emit(ServerMessageType.GameReset.value, {ServerDataKey.RoomID.value: room_id}, room=room_id)
        # TODO 开始新一局游戏
        return True
    else:
        print(f"房间{room_id}即将解散，因为只有 {len(continue_players)} 人选择继续游戏")
           
        del rooms[room_id]
        
        emit("room_disbanded", {"room_id": room_id}, room=room_id)
        return True


def start_continue_timer(room_id):
    """
    启动游戏继续倒计时，10秒后自动处理未做选择的玩家
    """
    if room_id not in rooms:
        return
        
    # 取消之前的定时器（如果存在）
    if hasattr(rooms[room_id], ContinueTimerName) and rooms[room_id].continue_timer is not None:
        # 注意：我们无法真正取消threading.Thread，但可以忽略它的执行
        rooms[room_id].continue_timer = None
    
    def check_continue_timeout():
        time.sleep(ContinueTimerSeconds)  # 等待倒计时结束
        
        # 检查房间是否还存在
        if room_id not in rooms:
            print(f"Room {room_id} does not exist when checking continue timeout")
            return
            
        # 检查定时器是否已被替换
        if rooms[room_id].continue_timer != threading.current_thread():
            print(f"Timer for room {room_id} was replaced before timeout")
            return  # 定时器已被替换，忽略此执行
        
        # 获取所有玩家，而不仅仅是在线玩家
        all_players = rooms[room_id][RoomKey.Players.value]
        
        # 将未做选择的玩家移除房间
        from room_manager import leave_room
        players_to_remove = []
        for p in all_players:
            if p[PlayerKey.Status.value] != PlayerStatus.Ready.value:
                players_to_remove.append(p[PlayerKey.ID.value])
        
        # 移除未做选择的玩家
        for player_id in players_to_remove:
            leave_room(room_id, player_id)
            
        # 处理游戏继续决策
        try_start_new_game_when_all_decided(room_id)
        
        # 清除定时器引用
        if room_id in rooms:
            rooms[room_id].continue_timer = None
    
    # 启动定时器线程
    timer_thread = threading.Thread(target=check_continue_timeout)
    timer_thread.daemon = True
    timer_thread.start()
    
    # 保存定时器引用
    rooms[room_id].continue_timer = timer_thread


def end_game(room_id):
    """
    结束游戏，重置房间状态
    """
    if room_id not in rooms:
        return
        
    room = rooms[room_id]
    
    # 重置游戏状态
    room[RoomKey.Status.value] = RoomStatus.Normal.value
    
    # 游戏状态已重置，无需额外清理
    
    # 重置所有玩家的游戏状态
    from game_enum import PlayerStatus
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Folded.value] = False
        # 游戏结束后，玩家状态设为seated（已坐下），等待选择是否继续
        player[PlayerKey.Status.value] = PlayerStatus.Seated.value
    
    # 启动10秒倒计时，等待玩家选择是否继续
    start_continue_timer(room_id)
    
    # 广播游戏结束
    broadcast_game_info(room_id, "游戏已结束，房间已重置")


def next_turn(room_id):
    """
    进入下一个玩家的回合
    """
    if room_id not in rooms:
        return
        
    room = rooms[room_id]
    
    # 找到下一个在座位上的、在线的玩家
    next_turn_player, next_turn_index = find_next_seated_and_online_player(room[RoomKey.Seats.value], room_owner_id)
    # 如果所有玩家都已弃牌或离线，结束游戏
    if not next_turn_player:
        # TODO
        # 检查是否还有在线玩家
        online_players = [p for p in players_list if p[PlayerKey.IsOnline.value]]
        if not online_players:
            # 没有在线玩家，设置一个定时器，如果一段时间后仍无玩家上线，则结束游戏
            add_game_log(room_id, "所有玩家已离线，游戏将在30秒后自动结束")
            
            # 设置房间状态为等待结束
            room[RoomKey.Status.value] = RoomStatus.WaitingToDestroy.value
            
            # 设置定时器，30秒后检查是否还有玩家上线
            import threading
            def check_players_online():
                import time
                time.sleep(30)  # 等待30秒
                
                # 检查房间是否还存在
                if room_id not in rooms:
                    return
                    
                # 检查房间状态
                if rooms[room_id][RoomKey.Status.value] != RoomStatus.WaitingToDestroy.value:
                    return
                    
                # 再次检查是否有在线玩家
                current_online_players = [p for p in rooms[room_id][RoomKey.Players.value] if p[PlayerKey.IsOnline.value]]
                if not current_online_players:
                    # 仍然没有在线玩家，结束游戏
                    add_game_log(room_id, "30秒内无玩家重新连接，游戏自动结束")
                    end_game(room_id)
                else:
                    # 有玩家重新连接，恢复游戏状态
                    rooms[room_id][RoomKey.Status.value] = RoomStatus.PLAYING.value
                    add_game_log(room_id, "有玩家重新连接，游戏继续")
            
            # 启动定时器线程
            timer_thread = threading.Thread(target=check_players_online)
            timer_thread.daemon = True
            timer_thread.start()
            
            return
        else:
            # 所有在线玩家都已弃牌，结束游戏
            determine_winner(room_id)
            return
        return
    
    # 设置到达了玩家的回合
    set_current_turn_player(room_id, next_turn_player[PlayerKey.ID.value])
    
    # 检查下一个玩家是否有足够的金币跟注
    if next_turn_player[PlayerKey.Coins.value] < room[RoomKey.CurrentBet.value]:
        # 如果金币不足，自动弃牌
        next_turn_player[PlayerKey.Folded.value] = True
        
        # 添加游戏日志
        room[RoomKey.GameLog.value].append({
            "message": f"{next_turn_player[PlayerKey.Username.value]} 金币不足，自动弃牌",
            "timestamp": str(uuid.uuid4()),
        })
        
        # 继续下一个玩家
        next_turn(room_id)
        return
    
    # 设置下一个玩家
    set_current_turn_player(room_id, next_turn_player[PlayerKey.ID.value])
    
    # 发送start_turn事件，通知前端当前回合玩家
    emit("start_turn", {
        "player_id": next_turn_player[PlayerKey.ID.value],
        "player_name": next_turn_player[PlayerKey.Username.value],
        "active_players_count": len([p for p in players_list if not p[PlayerKey.Folded.value] and p[PlayerKey.IsOnline.value]])
    }, room=room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def allowed_file(filename):
    """
    检查文件是否为允许的图片类型
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_room_by_player_id(player_id):
    """
    根据玩家ID查找所在房间
    返回房间ID，如果玩家不在任何房间则返回None
    """
    for room_id, room in rooms.items():
        for player in room[RoomKey.Players.value]:
            if player[PlayerKey.ID.value] == player_id:
                return room_id
    return None


def is_player_in_room(room_id, player_id):
    """
    检查玩家是否在指定房间中
    """
    if room_id not in rooms:
        return False
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            return True
    return False


def is_game_started(room_id):
    """
    检查游戏是否已开始
    """
    if room_id not in rooms:
        return False
    return rooms[room_id][RoomKey.GameStatus.value] == GameStatus.Playing.value


def is_player_turn(room_id, player_id):
    """
    检查是否是玩家的回合
    """
    if room_id not in rooms:
        return False
        
    current_player_id = rooms[room_id][RoomKey.CurrentTurnPlayerID.value]
    if current_player_id is None:
        return False
        
    # 直接比较玩家ID
    return current_player_id == player_id


def is_player_folded(room_id, player_id):
    """
    检查玩家是否已弃牌
    """
    if room_id not in rooms:
        return True
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            return player[PlayerKey.Folded.value]
    return True


def get_player_cards(room_id, player_id):
    """
    获取玩家的手牌
    """
    if room_id not in rooms:
        return []
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            return player[PlayerKey.Cards.value]
    return []


def update_player_coins(room_id, player_id, amount):
    """
    更新玩家金币数量
    """
    if room_id not in rooms:
        return False
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            player[PlayerKey.Coins.value] += amount
            return True
    return False


def update_player_bet(room_id, player_id, amount):
    """
    更新玩家当前下注金额
    """
    if room_id not in rooms:
        return False
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            player[PlayerKey.CurrentBet.value] = amount
            return True
    return False


def update_player_folded(room_id, player_id, folded=True):
    """
    更新玩家弃牌状态
    """
    if room_id not in rooms:
        return False
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            player[PlayerKey.Folded.value] = folded
            return True
    return False


def update_player_status(room_id, player_id, status):
    """
    更新玩家状态
    """
    if room_id not in rooms:
        return False
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            player[PlayerKey.Status.value] = status
            return True
    return False


def update_player_looked_at_cards(room_id, player_id, looked=True):
    """
    更新玩家看牌状态
    """
    if room_id not in rooms:
        return False
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            player[PlayerKey.HasLookedAtCards.value] = looked
            return True
    return False


def add_to_pot(room_id, amount):
    """
    向奖池添加金币
    """
    if room_id not in rooms:
        return False
        
    rooms[room_id][RoomKey.Pot.value] += amount
    return True


def set_current_bet(room_id, amount):
    """
    设置当前下注金额
    """
    if room_id not in rooms:
        return False
        
    rooms[room_id][RoomKey.CurrentBet.value] = amount
    return True


def get_pot(room_id):
    """
    获取当前奖池金额
    """
    if room_id not in rooms:
        return 0
    return rooms[room_id][RoomKey.Pot.value]


def get_current_bet(room_id):
    """
    获取当前下注金额
    """
    if room_id not in rooms:
        return 0
    return rooms[room_id][RoomKey.CurrentBet.value]


def get_player_by_id(room_id, player_id):
    """
    根据玩家ID获取玩家对象
    """
    if room_id not in rooms:
        return None
        
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            return player
    return None


def get_current_player(room_id):
    """
    获取当前回合的玩家
    """
    if room_id not in rooms:
        return None
        
    current_player_id = rooms[room_id][RoomKey.CurrentTurnPlayerID.value]
    if current_player_id is None:
        return None
        
    # 根据玩家ID获取玩家对象
    return get_player_by_id(room_id, current_player_id)


def set_current_turn_player(room_id, player_id):
    """
    设置当前回合的玩家
    """
    if room_id not in rooms:
        return False
        
    rooms[room_id][RoomKey.CurrentTurnPlayerID.value] = player_id
    return True


def set_game_status(room_id, game_status):
    """
    设置游戏状态
    """
    if room_id not in rooms:
        return False
        
    rooms[room_id][RoomKey.GameStatus.value] = game_status
    if game_status == GameStatus.Playing.value:
        for player in get_room_players(room_id):
            player[PlayerKey.Status.value] = PlayerStatus.Playing.value
    return True


def get_game_status(room_id):
    """
    获取游戏状态
    """
    if room_id not in rooms:
        return None
    return rooms[room_id][RoomKey.GameStatus.value]


def get_room_settings(room_id):
    """
    获取房间设置
    """
    if room_id not in rooms:
        return None
    return rooms[room_id][RoomKey.Settings.value]