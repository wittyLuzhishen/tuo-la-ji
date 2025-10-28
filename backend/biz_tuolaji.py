from flask_socketio import emit
from biz_utils import add_game_log, common_check
from dao_room import get_player_info, is_game_started, is_player_turn, rooms
from dao_user import get_user_info
from game_enum import (ClientDataKey, PlayerKey, PlayerStatus, RoomKey, RoomSettingKey, 
    ServerDataKey, ServerMessageType, UserKey
)
from game_logic import compare_hands
from server_message_emitter import broadcast_game_info

MIN_SHOWDOWN_ROUND = 1 # 开牌时要达到的轮数

def handle_look_at_cards(data:dict):
    """
    处理玩家看牌事件
    """
    user_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    player = common_check(user_id, room_id, should_game_started=True)
    if not player:
        return
        
    if not is_game_started(room_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏未开始"})
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"不是用户{user_id}的回合"})
        return
        
    # 检查玩家是否已弃牌
    if player[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌，无法看牌"})
        return
        
    # 获取玩家手牌
    cards = player[PlayerKey.Cards.value]
    if not cards:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"无法获取用户{user_id}的手牌"})
        return
        
    # 更新玩家看牌状态
    player[PlayerKey.HasLookedAtCards.value] = True
    
    # 发送手牌给玩家
    emit(ServerMessageType.ShowCards.value, {ServerDataKey.Cards.value: cards}, to=user_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_fold(data:dict):
    """
    处理玩家弃牌事件
    """
    user_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    player = common_check(user_id, room_id, should_game_started=True)
    if not player:
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "不是您的回合"})
        return
        
    # 检查玩家是否已弃牌
    if player[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌，不能再次弃牌"})
        return
        
    # 弃牌
    player[PlayerKey.Status.value] = PlayerStatus.Folded.value
    user_info = get_user_info(player[PlayerKey.UserID.value])
    if not user_info:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"无法获取用户{user_id}的信息"})
        return
    # 添加游戏日志
    add_game_log(room_id, f"{user_info[UserKey.Username.value]} 弃牌")
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_call(data:dict):
    """
    处理玩家跟注事件
    """
    user_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    
    player = common_check(user_id, room_id, should_game_started=True)

    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "无法获取玩家信息"})
        return

    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "不是您的回合"})
        return
        
    # 检查玩家是否已弃牌
    if player[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌，无法跟注"})
        return
        
    # 获取当前下注信息
    room = rooms[room_id]
    current_bet = room[RoomKey.CurrentBet.value]
    call_amount = current_bet if not player[PlayerKey.HasLookedAtCards.value] else current_bet * 2
    
    # 不检查玩家是否有足够的金币，允许负值
        
    # 扣除金币并更新下注
    # 扣减玩家金币
    player[PlayerKey.Coins.value] -= call_amount    
    # 加
    player[PlayerKey.CurrentBet.value] += current_bet
    room[RoomKey.Pot.value] += call_amount
    
    # 添加游戏日志
    add_game_log(room_id, f"{player[PlayerKey.ID.value]} 跟注 {call_amount}")
    
    # 广播下注信息
    emit(ServerMessageType.RoomUpdatedWithPlayerBets.value, {
        ServerDataKey.PlayerID.value: player[PlayerKey.ID.value],
        ServerDataKey.CallAmount.value: call_amount,
        ServerDataKey.Pot.value: room[RoomKey.Pot.value]
    }, room=room_id)
    
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_raise(data:dict):
    """
    处理玩家加注事件
    """
    user_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    add_amount = data.get(ClientDataKey.AddAmount.value, 0)
    
    player = common_check(user_id, room_id, should_game_started=True)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "无法获取玩家信息"})
        return
        
    # 检查是否是玩家的回合
    if not is_player_turn(room_id, user_id):
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "不是您的回合"})
        return
        
    # 检查玩家是否已弃牌
    if player[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌，无法加注"})
        return
        
    # 检查加注金额是否有效
    if add_amount <= 0:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "加注金额必须大于0"})
        return
        
    # 获取当前下注信息
    room = rooms[room_id]
    room[RoomKey.CurrentBet.value] += add_amount
    current_bet = room[RoomKey.CurrentBet.value]
        
    # 计算总下注金额
    total_bet = current_bet if not player[PlayerKey.HasLookedAtCards.value] else current_bet * 2
    
    # 扣减玩家金币
    player[PlayerKey.Coins.value] -= total_bet
    # 加
    player[PlayerKey.CurrentBet.value] += total_bet
    room[RoomKey.Pot.value] += total_bet
    
    # 添加游戏日志
    add_game_log(room_id, f"{player[PlayerKey.ID.value]} 加注，本次出注 {total_bet}，底注变为 {current_bet}")
    
    # 广播下注信息
    emit(ServerMessageType.RoomUpdatedWithPlayerBets.value, {
        ServerDataKey.PlayerID.value: player[PlayerKey.ID.value],
        ServerDataKey.RaiseAmount.value: total_bet,
        ServerDataKey.CurrentBet.value: current_bet,
        ServerDataKey.Pot.value: room[RoomKey.Pot.value]
    }, room=room_id)
    # 广播游戏信息
    broadcast_game_info(room_id)


def handle_showdown(data:dict):
    """
    处理玩家开牌事件
    """
    user_id = data.get(ClientDataKey.PlayerID.value, "").strip()
    room_id = data.get(ClientDataKey.RoomID.value, "").strip()
    player_id_to_be_showdown = data.get(ClientDataKey.PlayerIdToBeShowdown.value, "").strip()
        
    player = common_check(user_id, room_id, should_game_started=True)
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "无法获取玩家信息"})
        return
        
    # 检查玩家是否已弃牌
    if player[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "您已弃牌，无法开牌"})
        return
    
    if not player_id_to_be_showdown:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "被开牌玩家ID不能为空"})
        return

    player_to_be_showdown = get_player_info(room_id, player_id_to_be_showdown, check_status=True)
    if not player_to_be_showdown:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"被开牌玩家 {player_id_to_be_showdown} 不存在"})
        return
        
    if player_to_be_showdown[PlayerKey.Status.value] == PlayerStatus.Folded.value:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"被开牌玩家 {player_id_to_be_showdown} 已弃牌"})
        return

    room = rooms[room_id]
    if room[RoomKey.CurrentRound.value] < MIN_SHOWDOWN_ROUND:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"当前轮数为{room[RoomKey.CurrentRound.value]}，无法开牌"})
        return
    
    # 开牌需要付出双倍的注
    # 计算总下注金额
    current_bet = room[RoomKey.CurrentBet.value]
    total_bet = (current_bet if not player[PlayerKey.HasLookedAtCards.value] else current_bet * 2) * 2
    # 扣减玩家金币
    player[PlayerKey.Coins.value] -= total_bet
    # 加
    player[PlayerKey.CurrentBet.value] += total_bet
    room[RoomKey.Pot.value] += total_bet
    
    winner_index = compare_hands([player[PlayerKey.Cards.value], player_to_be_showdown[PlayerKey.Cards.value]], 
        raise_compare_hand_index=0,
        isDiffentSuit235GreaterThanThreeOfAKind=room[RoomKey.Settings.value][RoomSettingKey.IsDiffentSuit235GreaterThanThreeOfAKind.value],
        is_A23_as_straight=room[RoomKey.Settings.value][RoomSettingKey.IsA23AsStraight.value],
    )[0]
    
    # 检查是否有玩家赢下了游戏
    if winner_index == 0:
        # 被比牌的玩家输了，状态更新为弃牌
        player_id_to_be_showdown[PlayerKey.Status.value] = PlayerStatus.Folded.value
    elif winner_index == 1:
        # 发起比牌的玩家输了，状态更新为弃牌
        player[PlayerKey.Status.value] = PlayerStatus.Folded.value
    
    # 广播游戏信息
    broadcast_game_info(room_id)