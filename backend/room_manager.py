# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏房间管理模块
包含房间状态管理和玩家信息管理等功能
"""

import time
import random
from flask import session
from backend.utils import broadcast_game_info
from game_enum import GameStatus, RoomKey, PlayerKey, PlayerStatus, RoomSettingKey, RoomStatus


# 存储服务器上所有房间信息的变量
rooms = {}

# 默认房间设置
DEFAULT_ROOM_SETTINGS = {
    RoomSettingKey.IsDiffentSuit235GreaterThanThreeOfAKind.value: True,
    RoomSettingKey.IsA23AsStraight.value: True,
    RoomSettingKey.InitialCoins.value: 1000,
    RoomSettingKey.BaseBet.value: 2,
    RoomSettingKey.MaxBet.value: 100,
    RoomSettingKey.MaxHands.value: 10,
    RoomSettingKey.MaxPotAmount.value: 1500,
    RoomSettingKey.MaxPlayerNumber.value: 6,
}

def find_player_in_room(room_id:str, player_id:str)->tuple:
    """
    在房间中查找玩家，返回玩家对象和在Players数组中的索引，对返回玩家信息的修改会影响全局数据。
    如果找不到玩家，返回 (None, None)
    """
    if room_id not in rooms:
        return None, None
        
    for i, player in enumerate(rooms[room_id][RoomKey.Players.value]):
        if player[PlayerKey.ID.value] == player_id:
            return player, i
    return None, None

# TODO
def reset_room_for_game_end(room_id:str, last_winner_id:str)->bool:
    """当刚决出胜负，一局游戏刚结束时，重置房间的状态"""
    if room_id not in rooms:
        return False
        
    room = rooms[room_id]
    room[RoomKey.GameStatus.value] = GameStatus.Wating.value
    room[RoomKey.LastWinner.value] = last_winner_id
    room[RoomKey.Status.value] = RoomStatus.Normal.value
    room[RoomKey.Pot.value] = 0
    room[RoomKey.CurrentTurnPlayerID.value] = None
    room[RoomKey.CurrentRound.value] = None
    room[RoomKey.CurrentBet.value] = room[RoomKey.Settings.value][RoomSettingKey.BaseBet.value]
    # 设置所有玩家的状态为seated
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Status.value] = PlayerStatus.Seated.value


def reset_room_for_new_game(room_id:str, last_winner_id:str)->bool:
    """
    当所有玩家都同意继续游戏时，
    重置房间状态到初始状态，
    保留玩家信息和房间设置，但重置游戏相关状态
    """
    if room_id not in rooms:
        return False
        
    room = rooms[room_id]
    room[RoomKey.Owner.value] = room[RoomKey.Players.value][0][PlayerKey.ID.value]
    room[RoomKey.GameStatus.value] = GameStatus.Wating.value
    #room[RoomKey.Seats.value] = 
    # 提取所有玩家ID到列表中
    player_ids = [player[PlayerKey.ID.value] for player in room[RoomKey.Players.value]]
    if last_winner_id and last_winner_id in player_ids:
        room[RoomKey.LastWinner.value] = last_winner_id
    else:
        room[RoomKey.LastWinner.value] = None # 开始游戏时，如果last_winner_id为None，则随机选择庄家
    room[RoomKey.Seats.value] = [None] * len(room[RoomKey.Players.value])
    room[RoomKey.GameLog.value] = []
    room[RoomKey.Pot.value] = 0
    room[RoomKey.CurrentBet.value] = room[RoomKey.Settings.value][RoomSettingKey.BaseBet.value]
    room[RoomKey.CurrentTurnPlayerID.value] = None
    room[RoomKey.CurrentRound.value] = None
    
    # 重置所有玩家的状态
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Folded.value] = False
        player[PlayerKey.Cards.value] = None
        player[PlayerKey.HasLookedAtCards.value] = False
    
    return True


# 找到第一个出牌的玩家，他是坐在庄家逆时针位置的下一个玩家
def find_next_seated_and_online_player(seats:list, current_player_id:str)->tuple:
    """找到当前玩家的逆时针方向的下一个坐在座位上的玩家以及座位索引。含有耗时操作！"""
    current_index = next((i for i, p in enumerate(seats) if p[PlayerKey.ID.value] == current_player_id), None)
    if current_index is None:
        print(f"未找到当前玩家的索引，房间号：{room_id}， userId：{current_player_id}")
        return None, None
    next_index = current_index
    visit_count = 0
    step = -1 # 座位索引是按顺时针顺序递增的，但游戏的下家是逆时针方向的，所以索引应每次减小
    while True:
        next_index = (next_index + step) % len(seats)
        visit_count += 1
        if visit_count >= len(seats):
            return None, None
        
        if seats[next_index] is not None:
            next_player = find_player_in_room(room_id, seats[next_index])[0]
            if next_player:
                print(f"等待一段时间，然后找到下一个玩家：{next_player[PlayerKey.Username.value]}，座位索引：{next_index}")
                time.sleep(5) # 等待，万一玩家断线重连了呢
                if next_player[PlayerKey.IsOnline.value] == True:
                    return next_player, next_index
                else:
                    # 设置已离线的玩家状态为弃牌，如果离线的玩家再次上线，通过检查是否弃牌的状态来判断是否可以重新加入游戏
                    next_player[PlayerKey.Status.value] = PlayerStatus.Folded.value
                    # 广播游戏信息
                    broadcast_game_info(room_id)
# end find_next_seated_player


def get_player_info_without_cards(room_id, player_id):
    """
    获取玩家信息，
    返回玩家信息的字典，不包括手牌
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        return None
    
    player_copy = player.copy()
    del player_copy[PlayerKey.Cards.value]
    return player_copy


def create_room(player_id:str, username:str, room_name:str=None)->str:
    """
    玩家创建新房间，初始化房间状态，
    返回房间ID（4位数字），如果没有可用的房间号则返回None
    """
    # 生成4位数字的房间号
    # 尝试最多100次生成不重复的房间号
    max_attempts = 100
    room_id = None
    
    # 检查是否还有可用的4位数字房间号
    if len(rooms) >= 10000:  # 4位数字范围是0000-9999，共10000个可能
        return None
    
    for _ in range(max_attempts):
        # 生成0000-9999之间的随机数
        candidate_id = str(random.randint(0, 9999)).zfill(4)
        # 检查是否已存在
        if candidate_id not in rooms:
            room_id = candidate_id
            break
    
    # 如果无法找到可用的房间号，返回None
    if room_id is None:
        return None
    
    # 创建新玩家
    new_player = {
        PlayerKey.ID.value: player_id,
        PlayerKey.Username.value: username,
        PlayerKey.Coins.value: DEFAULT_ROOM_SETTINGS[RoomSettingKey.InitialCoins.value], # 根据房间设置设置
        PlayerKey.Status.value: PlayerStatus.Spectator.value, # 根据房间设置设置
        PlayerKey.Avatar.value: None, #?,
        PlayerKey.OnlineStatus.value: True,
        PlayerKey.Folded.value: False,
    }
    
    # 创建新房间
    rooms[room_id] = {
        RoomKey.Name.value: room_name or f"{username}的房间",  # 房间名称
        RoomKey.Players.value: [new_player],  # 使用列表存储玩家，保持顺序
        RoomKey.Owner.value: player_id,  # 创建房间的人成为该房间的首任房主
        RoomKey.Settings.value: DEFAULT_ROOM_SETTINGS.copy(),  # 游戏设置
        RoomKey.GameStatus.value: GameStatus.Wating.value,  # 游戏状态
        RoomKey.Status.value: RoomStatus.Normal.value,  # 房间状态?
        RoomKey.Seats.value: [None] * DEFAULT_ROOM_SETTINGS[RoomSettingKey.MaxPlayerNumber.value],  # 座位信息，根据房间设置设置
        RoomKey.LastWinner.value: None,  # 上一局的赢家ID，用于确定下一局的庄家
        RoomKey.GameLog.value: [],  # 游戏日志
    }
    
    return room_id


def join_room(room_id, player_id, username)->tuple:
    """
    加入房间，
    返回是否成功加入
    return success, reason
    """
    if room_id not in rooms:
        return False, f"房间{room_id}不存在"
    
    room = rooms[room_id]
    # 检查玩家是否已在房间中
    player, player_index = find_player_in_room(room_id, player_id)
    # 检查房间是否已满
    max_players = room[RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber.value]
    # 如果玩家之前不在房间中，并且房间已经满了，无法加入
    if player is None and len(room[RoomKey.Players.value]) >= max_players:
        print(f"房间 {room_id} 已满，无法加入")
        return False, f"房间{room_id}已满，无法加入"

    # 玩家已存在，更新在线状态
    if player is not None:
        print(f"玩家 {username} 已存在，更新状态为观众，重置金币数")
        player[PlayerKey.Status.value] = PlayerStatus.Spectator.value
        player[PlayerKey.Username.value] = username
        player[PlayerKey.Coins.value] = room[RoomKey.Settings.value][RoomSettingKey.InitialCoins.value]
        player[PlayerKey.OnlineStatus.value] = True
        player[PlayerKey.Folded.value] = False
        return True, f"玩家 {username} 已存在，更新状态为观众，重置金币数"
    
    # 创建新玩家
    new_player = {
        PlayerKey.ID.value: player_id,
        PlayerKey.Username.value: username,
        PlayerKey.Coins.value: room[RoomKey.Settings.value][RoomSettingKey.InitialCoins.value],
        PlayerKey.Status.value: PlayerStatus.Spectator.value,
        PlayerKey.Avatar.value: None, #?,
        PlayerKey.OnlineStatus.value: True,
        PlayerKey.Folded.value: False,
    }
    
    # 添加玩家到房间
    room[RoomKey.Players.value].append(new_player)
    return True, f"玩家 {username} 已成功加入房间 {room_id}"


def leave_room(room_id, player_id)->tuple:
    """
    离开房间，
    返回是否成功离开
    """
    if room_id not in rooms:
        print(f"房间号{room_id}不存在")
        return False, f"房间号{room_id}不存在"
    
    room = rooms[room_id]
    
    # 查找玩家在列表中的位置
    player, player_index = find_player_in_room(room_id, player_id)
    
    # 检查玩家是否存在
    if player is None:
        print(f"玩家{player_id}不在房间{room_id}中")
        return False, f"玩家{player_id}不在房间{room_id}中"
        
    # 移除玩家
    room[RoomKey.Players.value].pop(player_index)
    
    # 如果房间为空，删除房间
    if not room[RoomKey.Players.value]:
        del rooms[room_id]
        return True, f"房间{room_id}已空，已删除"
        
    # 如果离开的是房主，转移房主身份
    if room[RoomKey.Owner.value] == player_id:
        # 选择第一个玩家作为新房主
        if room[RoomKey.Players.value]:
            room[RoomKey.Owner.value] = room[RoomKey.Players.value][0][PlayerKey.ID.value]
            print(f"房间{room_id}新房主为{room[RoomKey.Owner.value]}")
            
    return True, f"成功将用户{player_id}从房间{room_id}移除"


def update_player_online_status(room_id, player_id, is_online=True):
    """
    更新玩家在线状态
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        return False
        
    player[PlayerKey.OnlineStatus.value] = is_online
    return True


def update_player_coins(room_id, player_id, coins):
    """
    更新玩家金币
    """
    if room_id not in rooms:
        return False
    
    room = rooms[room_id]
    for player in room[RoomKey.Players.value]:
        if player[PlayerKey.ID.value] == player_id:
            player[PlayerKey.Coins.value] = coins
            return True
    return False


def update_player_avatar(room_id, player_id, avatar):
    """
    更新玩家头像
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        return False
        
    player[PlayerKey.Avatar.value] = avatar
    return True


def get_room_list():
    """
    获取房间列表，返回房间信息列表
    每个房间信息包括房间ID、房间名、玩家数量、最大玩家数、房间状态
    """
    room_list = []
    for room_id, room in rooms.items():
        # 获取房主信息
        owner_info = get_player_info_without_cards(room_id, room[RoomKey.Owner.value])
        
        room_info = {
            RoomKey.ID.value: room_id,
            RoomKey.Name.value: room[RoomKey.Name.value],
            RoomKey.PlayerCount.value: len(room[RoomKey.Players.value]),
            RoomKey.MaxPlayerNumber.value: room[RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber.value],
            RoomKey.Status.value: room[RoomKey.Status.value],
            RoomKey.Owner.value: owner_info[RoomKey.Owner.value]
        }
        room_list.append(room_info)
    return room_list


def get_room_details(room_id:str):
    """
    获取房间详细信息。
    返回房间的完整信息，包括房间中玩家的详细信息。
    """
    if room_id not in rooms:
        return None
        
    room = rooms[room_id].copy()
    # 因为房间信息中不包含房间ID，所以手动添加
    room[RoomKey.ID.value] = room_id
    
    # 转换玩家信息，不包括手牌（get_player_info_without_cards已返回新创建的字典副本）
    players_info = []
    for player in room[RoomKey.Players.value]:
        player_info = get_player_info_without_cards(room_id, player[PlayerKey.ID.value])
        players_info.append(player_info)
        
    room[RoomKey.Players.value] = players_info
    return room


def get_room_info(room_id):
    """
    获取房间信息，返回房间详细信息，包括玩家列表
    """
    if room_id not in rooms:
        return None
    
    room = rooms[room_id]
    
    room_info = {
        RoomKey.ID.value: room_id,
        RoomKey.Name.value: room[RoomKey.Name.value],
        RoomKey.Owner.value: room[RoomKey.Owner.value],
        RoomKey.Status.value: room[RoomKey.Status.value],
        RoomKey.GameStatus.value: room[RoomKey.GameStatus.value],
        RoomKey.Settings.value: room[RoomKey.Settings.value],
        RoomKey.Players.value: room[RoomKey.Players.value]  # 已经是列表类型
    }
    return room_info


def get_room_players(room_id):
    """
    获取房间玩家列表。对返回结果的修改会影响全局变量。如果找不到房间，返回空列表。
    """
    if room_id not in rooms:
        return []
    
    # 直接返回玩家列表
    return rooms[room_id][RoomKey.Players.value]


def get_player_count(room_id):
    """
    获取房间玩家数量
    """
    if room_id not in rooms:
        print(f"room, id: {room_id}, not exist")
        return 0
    
    return len(rooms[room_id][RoomKey.Players.value])


def is_room_full(room_id):
    """
    检查房间是否已满
    """
    if room_id not in rooms:
        print(f"room, id: {room_id}, not exist")
        return False
    
    room = rooms[room_id]
    max_players = room[RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber.value]
    return len(room[RoomKey.Players.value]) >= max_players


def update_room_settings(room_id, settings:dict):
    """
    更新房间设置。
    返回是否成功更新。
    """
    if room_id not in rooms:
        return False
        
    # 验证设置
    isDiffentSuit235GreaterThanThreeOfKing = settings.get(RoomSettingKey.IsDiffentSuit235GreaterThanThreeOfKing.value, None)
    isA23AsStraight = settings.get(RoomSettingKey.IsA23AsStraight.value, None)
    initialCoins = settings.get(RoomSettingKey.InitialCoins.value, 0)
    baseBet = settings.get(RoomSettingKey.BaseBet.value, 0)
    maxBet = settings.get(RoomSettingKey.MaxBet.value, 0)
    maxHands = settings.get(RoomSettingKey.MaxHands.value, 0)
    maxPotAmount = settings.get(RoomSettingKey.MaxPotAmount.value, 0)
    maxPlayers = settings.get(RoomSettingKey.MaxPlayerNumber.value, 0)
    if isDiffentSuit235GreaterThanThreeOfKing is None or isA23AsStraight is None:
        return False
    if initialCoins < 0 or baseBet < 0 or maxBet < 0 or maxHands < 0 or maxPotAmount < 0 or maxPlayers < 2:
        return False
    if initialCoins < baseBet or baseBet < maxBet or maxHands < 1 \
        or maxPotAmount < baseBet * maxPlayers \
        or maxPlayers > DEFAULT_ROOM_SETTINGS[RoomSettingKey.MaxPlayerNumber.value]:
        return False
            
    # 更新设置
    for key in DEFAULT_ROOM_SETTINGS.keys():
        if key in settings:
            rooms[room_id][RoomKey.Settings.value][key] = settings[key]
        else:
            rooms[room_id][RoomKey.Settings.value][key] = DEFAULT_ROOM_SETTINGS[key]
    
    update_room_by_room_setting(room_id, setting)
    update_players_by_room_setting(room_id, setting)

    return True

def update_room_by_room_setting(room_id:str, setting:dict):
    """
    根据房间设置更新房间状态
    """
    if room_id not in rooms:
        return False
    
    room = rooms[room_id]
    room[RoomKey.Seats.value] = setting[RoomSettingKey.MaxPlayerNumber.value] * [None]
    return True

def update_players_by_room_setting(room_id:str, setting:dict):
    """
    根据房间设置更新房间玩家信息
    """
    if room_id not in rooms:
        return False
    
    players = get_room_players(room_id)
    for player in players:
        player[PlayerKey.Coins.value] = setting[RoomSettingKey.InitialCoins.value]
        # 已经准备就绪的玩家会因为房间设置的改变而取消准备状态
        if player[PlayerKey.Status.value] == PlayerStatus.Ready.value:
            player[PlayerKey.Status.value] = PlayerStatus.Spectator.value
    return True

def get_room_owner(room_id):
    """
    获取房主信息
    """
    if room_id not in rooms:
        return None
        
    owner_id = rooms[room_id][RoomKey.Owner.value]
    return find_player_in_room(room_id, owner_id)[0]


def is_room_owner(room_id, player_id):
    """
    检查玩家是否是房主
    """
    if room_id not in rooms:
        return False
        
    return rooms[room_id][RoomKey.Owner.value] == player_id


def get_active_players(room_id):
    """
    获取房间中未弃牌的玩家列表
    """
    if room_id not in rooms:
        return []
        
    active_players = []
    for player in rooms[room_id][RoomKey.Players.value]:
        if not player[PlayerKey.Folded.value]:
            active_players.append(player)
            
    return active_players


def get_online_players(room_id):
    """
    获取房间中在线的玩家列表
    """
    if room_id not in rooms:
        return []
        
    online_players = []
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.OnlineStatus.value]:
            online_players.append(player)
            
    return online_players


def count_ready_players(room_id):
    """
    统计房间中准备好的玩家数量
    """
    if room_id not in rooms:
        return 0
        
    count = 0
    for player in rooms[room_id][RoomKey.Players.value]:
        if player[PlayerKey.Status.value] == PlayerStatus.Ready.value and player[PlayerKey.OnlineStatus.value]:
            count += 1
            
    return count


def add_game_log(room_id:str, message:str):
    """
    添加游戏日志
    room_id: 房间ID
    message: 日志消息
    """
    if room_id not in rooms:
        return
        
    rooms[room_id][RoomKey.GameLog.value].append({
        "message": message,
        "timestamp": int(time.time() * 1000),  # 使用当前时间的毫秒时间戳
    })
    
    # 限制日志长度
    if len(rooms[room_id][RoomKey.GameLog.value]) > 100:
        rooms[room_id][RoomKey.GameLog.value] = rooms[room_id][RoomKey.GameLog.value][-50:]