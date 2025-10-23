# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏事件处理模块
包含所有Socket.IO事件处理函数
"""

import os
import uuid
from flask import request, session, send_from_directory
from flask_socketio import emit, join_room, leave_room

# 导入模块
from game_enum import ClientDataKey, EmitMessageType, RoomStatus, SessionKey, PlayerStatus, EmitDataKey
from room_manager import (
    rooms, RoomKey, PlayerKey, GameStatus, RoomSettingKey,
    reset_room_for_new_game, get_player_info_without_cards, create_room, join_room, leave_room,
    update_player_online_status, get_room_list, get_room_details,
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
    处理客户端连接事件
    """
    user_id = str(uuid.uuid4())
    print(f"用户连接：{user_id}")
    session[SessionKey.UserID.value] = user_id
    emit(EmitMessageType.Connected.value, {"user_id": user_id})
    
    # 检查玩家是否已经在某个房间中，这是为了处理玩家断线重连的情况
    room_id = get_room_by_player_id(user_id)
    
    if room_id and room_id in rooms:
        room = rooms[room_id]
        
        # 无论房间状态如何，都更新玩家在线状态
        update_player_online_status(room_id, user_id, True)
        
        # 如果房间状态是等待结束，且有玩家重新连接，恢复游戏状态
        if room[RoomKey.Status.value] == RoomStatus.WaitingToDestroy.value:
            # 恢复游戏状态
            room[RoomKey.State.value] = RoomStatus.Normal.value
            add_game_log(room_id, f"玩家 {user_id} 重新连接，游戏继续")
        
        # 无论房间状态如何，都广播游戏信息以更新玩家在线状态
        broadcast_game_info(room_id)


def handle_disconnect():
    """
    处理客户端断开连接事件
    """
    user_id = session.get(SessionKey.UserID.value)
    if not user_id:
        return
        
    # 查找玩家所在的房间
    room_id = get_room_by_player_id(user_id)
    if not room_id:
        return

    # 更新玩家在线状态
    update_player_online_status(room_id, user_id, False)
    
    # 如果游戏已开始且当前玩家是断线的玩家，自动跳过他的回合
    if is_game_started(room_id) and is_player_turn(room_id, user_id):
        # 添加游戏日志
        player = get_player_by_id(room_id, user_id)
        if player:
            add_game_log(room_id, f"{player} 离线，自动跳过他的回合")
        
        # 自动弃牌并进入下一个玩家
        update_player_folded(room_id, user_id, True)
        next_turn(room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_set_username(data):
    """
    处理设置用户名事件
    """
    username = data.get("username", "").strip()
    if not username:
        emit("error", {"message": "用户名不能为空"})
        return
        
    session["username"] = username
    emit("username_set", {"username": username})


def handle_create_room():
    """
    处理创建房间事件
    """
    user_id = session.get(SessionKey.UserID.value)
    username = session.get(SessionKey.Username.value)

    if not user_id or not username:
        emit("error", {"message": "请先设置用户名"})
        return
        
    # 检查玩家是否已在房间中
    existing_room_id = get_room_by_player_id(user_id)
    if existing_room_id:
        emit("error", {"message": "您已在房间中"})
        return
        
    # 创建新房间
    room_id = create_room(user_id, username)
    
    # 加入Socket.IO房间
    join_room(room_id)
    
    # 发送房间信息给客户端
    emit("room_created", {
        "room_id": room_id,
        "room": get_room_details(room_id)
    })
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_join_room(data):
    """
    处理加入房间事件
    """
    user_id = session.get(SessionKey.UserID.value)
    username = session.get(SessionKey.Username.value)
    room_id = data.get("room_id", "").strip()
    
    if not user_id or not username:
        emit("error", {"message": "请先设置用户名"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    # 检查房间是否存在
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    # 检查玩家是否已在房间中
    existing_room_id = get_room_by_player_id(user_id)
    if existing_room_id:
        emit("error", {"message": "您已在房间中"})
        return
        
    # 加入房间
    if not join_room(room_id, user_id, username):
        emit("error", {"message": "房间已满"})
        return
        
    # 加入Socket.IO房间
    join_room(room_id)
    
    # 发送房间信息给客户端
    emit("room_joined", {
        "room_id": room_id,
        "room": get_room_details(room_id)
    })
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_leave_room():
    """
    处理离开房间事件
    """
    user_id = session.get(SessionKey.UserID.value)
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    # 查找玩家所在的房间
    room_id = get_room_by_player_id(user_id)
    if not room_id:
        emit("error", {"message": "您不在任何房间中"})
        return
        
    # 如果游戏已开始，不允许离开
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始，无法离开房间"})
        return
        
    # 离开房间
    leave_room(room_id, user_id)
    
    # 离开Socket.IO房间
    leave_room(room_id)
    
    # 发送离开成功消息
    emit("room_left", {"room_id": room_id})
    
    # 如果房间还存在，广播游戏信息
    if room_id in rooms:
        broadcast_game_info(room_id)


def handle_get_room_list():
    """
    处理获取房间列表事件
    """
    emit("room_list", {"rooms": get_room_list()})


def handle_get_room_details(data):
    """
    处理获取房间详情事件
    """
    room_id = data.get("room_id", "").strip()
    
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    room_details = get_room_details(room_id)
    if not room_details:
        emit("error", {"message": "房间不存在"})
        return
        
    emit("room_details", {"room": room_details})


def handle_sit_down(data:dict):
    """
    处理玩家坐下事件
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
        
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始，无法坐下"})
        return
        
    # 查找玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit("error", {"message": "您不在此房间中"})
        return
        
    # 更新玩家状态
    from game_enum import PlayerStatus
    player[PlayerKey.Status.value] = PlayerStatus.Seated.value
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_stand_up(data:dict):
    """
    处理玩家站起事件
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
        
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始，无法站起"})
        return
        
    # 查找玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit("error", {"message": "您不在此房间中"})
        return
        
    # 更新玩家状态
    from game_enum import PlayerStatus
    player[PlayerKey.Status.value] = PlayerStatus.Spectator.value
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_ready(data:dict):
    """
    处理玩家准备/取消准备事件
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    is_ready = data.get(ClientDataKey.Ready.value, True)
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始，无法更改准备状态"})
        return
        
    # 查找玩家
    player = get_player_by_id(room_id, user_id)
    if not player:
        emit("error", {"message": "您不在此房间中"})
        return
        
    # 更新玩家状态
    from game_enum import PlayerStatus
    status = PlayerStatus.Ready.value if is_ready else PlayerStatus.Seated.value
    update_player_online_status(room_id, user_id, status)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_update_settings(data:dict):
    """
    处理更新房间设置事件（仅房主可操作）
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    settings = data.get(ClientDataKey.Settings.value, {})
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始，无法更改设置"})
        return
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit("error", {"message": "只有房主可以更改房间设置"})
        return
        
    # 更新房间设置
    if not update_room_settings(room_id, settings):
        emit("error", {"message": "设置更新失败，请检查设置参数"})
        return
        
    # 广播游戏信息
    broadcast_game_info(room_id)
    
    emit("settings_updated", {"settings": get_room_settings(room_id)})


def handle_kick_player(data:dict):
    """
    处理踢出玩家事件（仅房主可操作）
    """
    user_id = session.get(SessionKey.UserID.value)
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    target_player_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    
    if not user_id:
        emit("error", {"message": "用户未登录"})
        return
        
    if not room_id:
        emit("error", {"message": "房间ID不能为空"})
        return
        
    if not target_player_id:
        emit("error", {"message": "目标玩家ID不能为空"})
        return
        
    if room_id not in rooms:
        emit("error", {"message": "房间不存在"})
        return
        
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始，无法踢出玩家"})
        return
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit("error", {"message": "只有房主可以踢出玩家"})
        return
        
    # 不能踢出自己
    if user_id == target_player_id:
        emit("error", {"message": "不能踢出自己"})
        return
        
    # 检查目标玩家是否在房间中
    target_player = get_player_by_id(room_id, target_player_id)
    if not target_player:
        emit("error", {"message": "目标玩家不在此房间中"})
        return
        
    # 踢出玩家
    leave_room(room_id, target_player_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)
    
    emit("player_kicked", {"player_id": target_player_id})


def handle_start_game(data:dict):
    """
    处理开始游戏事件（仅房主可操作）
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
        
    if is_game_started(room_id):
        emit("error", {"message": "游戏已开始"})
        return
        
    # 检查是否是房主
    if not is_room_owner(room_id, user_id):
        emit("error", {"message": "只有房主可以开始游戏"})
        return
        
    # 检查是否有足够的玩家
    min_players = 2
    online_players = get_online_players(room_id)
    if len(online_players) < min_players:
        emit("error", {"message": f"至少需要{min_players}名玩家才能开始游戏"})
        return
        
    # 检查所有玩家是否都已准备
    ready_players = count_ready_players(room_id)
    if ready_players < len(online_players):
        emit("error", {"message": "还有玩家未准备"})
        return
        
    # 开始游戏
    set_game_status(room_id, GameStatus.Playing.value)
    
    # 创建并洗牌
    deck = shuffle_deck(create_deck())
    
    # 发牌
    players = rooms[room_id][RoomKey.Players.value]
    
    for player in players:
        cards, deck = deal_cards(deck, 3)
        player[PlayerKey.Cards.value] = cards
        player[PlayerKey.HasLookedAtCards.value] = False
        # 设置玩家状态为playing
        player[PlayerKey.Status.value] = PlayerStatus.Playing.value
    
    
    # 设置当前玩家（房主的下一个玩家）
    room_owner_id = user_id
    
    if room_owner_id is not None:
        # 获取所有玩家列表，并找到庄家在列表中的位置
        players_list = players  # players已经是列表，无需转换
        room_owner_index = None
        for i, player in enumerate(players_list):
            if player[PlayerKey.ID.value] == room_owner_id:
                room_owner_index = i
                break
        
        if room_owner_index is None:
            print(f"未找到房主， userId：{room_owner_id}")
        next_player_index = (room_owner_index + 1) % len(players_list)
        # 找到下一个在线玩家
        while not players_list[next_player_index][PlayerKey.IsOnline.value]:
            # 设置已离线的玩家状态为弃牌，如果离线的玩家再次上线，通过检查是否弃牌的状态来判断是否重新加入游戏
            players_list[next_player_index][PlayerKey.Status.value] = PlayerStatus.Folded.value
            next_player_index = (next_player_index + 1) % len(players_list)
        
        # 设置当前玩家ID
        next_player_id = players_list[next_player_index][PlayerKey.ID.value]
        set_current_turn_player(room_id, next_player_id)
        
        # 发送start_turn事件，通知前端当前回合玩家
        next_player = players_list[next_player_index]
        emit(EmitMessageType.StartTurn.value, {
            EmitDataKey.PlayerID.value: next_player[PlayerKey.ID.value],
            EmitDataKey.PlayerName.value: next_player[PlayerKey.Username.value],
            EmitDataKey.ActivePlayersCount.value: len([p for p in players_list if p[PlayerKey.IsOnline.value]])
        }, room=room_id)
    
    # 设置庄家索引?
    
    
    # 重置当前回合
    rooms[room_id][RoomKey.CurrentRound.value] = 1
    
    # 添加游戏日志
    add_game_log(room_id, "游戏开始")
    
    # 广播游戏信息
    broadcast_game_info(room_id)
    
    emit("game_started", {"room_id": room_id})


def handle_look_at_cards(data:dict):
    """
    处理玩家看牌事件
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
        emit("error", {"message": "您已弃牌，无法看牌"})
        return
        
    # 获取玩家手牌
    cards = get_player_cards(room_id, user_id)
    if not cards:
        emit("error", {"message": "无法获取手牌"})
        return
        
    # 更新玩家看牌状态
    update_player_looked_at_cards(room_id, user_id, True)
    
    # 发送手牌给玩家
    emit("show_cards", {"cards": cards}, to=user_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_fold(data:dict):
    """
    处理玩家弃牌事件
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
        emit("error", {"message": "您已弃牌"})
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
    
    # 设置游戏状态为开牌
    set_game_status(room_id, GameStatus.Showdown.value)
    
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
        from room_manager import leave_room
        leave_room(room_id, user_id)
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