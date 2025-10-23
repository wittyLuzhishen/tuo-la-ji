# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏房间管理模块
包含房间状态管理和玩家信息管理等功能
"""

from enum import Enum
from typing import Dict, List, Any, Optional
import uuid
import time
from flask import session
from flask_socketio import emit
from game_enum import GameStatus, RoomKey, PlayerKey, PlayerStatus, RoomSettingKey, RoomStatus

# 服务器设置的房间座位数
ROOM_SEAT_NUMBER = 6

# 导入全局变量和常量
rooms = {}

# 默认房间设置
DEFAULT_ROOM_SETTINGS = {
    RoomSettingKey.Is235GreaterThanThreeOfAKind.value: False,
    RoomSettingKey.InitialCoins.value: 1000,
    RoomSettingKey.BaseBet.value: 2,
    RoomSettingKey.MaxBet.value: 100,
    RoomSettingKey.MaxHands.value: 10,
    RoomSettingKey.MaxPotAmount.value: 1500,
    RoomSettingKey.MaxPlayerNumber.value: ROOM_SEAT_NUMBER,
}

def find_player_in_room(room_id, player_id):
    """
    在房间中查找玩家，返回玩家对象和索引
    如果找不到玩家，返回 (None, None)
    """
    if room_id not in rooms:
        return None, None
        
    for i, player in enumerate(rooms[room_id][RoomKey.Players.value]):
        if player[PlayerKey.ID.value] == player_id:
            return player, i
    return None, None

# TODO
def reset_room_for_new_game(room_id):
    """
    当所有玩家都同意继续游戏时，
    重置房间状态到初始状态，
    保留玩家信息和房间设置，但重置游戏相关状态
    """
    if room_id not in rooms:
        return False
        
    room = rooms[room_id]
    room[RoomKey.GameStatus.value] = GameStatus.Wating.value
    room[RoomKey.ReadyPlayers.value] = set()
    room[RoomKey.Seats.value] = [None] * room[RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber.value]
    room[RoomKey.LastSeatTime.value] = {}
    room[RoomKey.GameData.value] = {}
    room[RoomKey.ContinueGameData.value] = {}
    room[RoomKey.GameLog.value] = []
    
    # 重置所有玩家的状态
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Folded.value] = False
        #player[PlayerKey.Status.value] = PlayerStatus.Seated.value  # 重置为就座状态
    
    return True


def get_player_info_without_cards(room_id, player_id):
    """
    获取玩家信息，
    返回玩家信息的字典，不包括手牌
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        return None
        
    return {
        PlayerKey.ID.value: player[PlayerKey.ID.value],
        PlayerKey.Username.value: player[PlayerKey.Username.value],
        PlayerKey.Coins.value: player[PlayerKey.Coins.value],
        PlayerKey.Status.value: player[PlayerKey.Status.value],
        PlayerKey.Avatar.value: player[PlayerKey.Avatar.value],
        PlayerKey.IsOnline.value: player[PlayerKey.IsOnline.value],
        PlayerKey.Folded.value: player[PlayerKey.Folded.value],
    }


def create_room(player_id, username, room_name=None):
    """
    玩家创建了新房间，初始化房间状态，
    返回房间ID
    """
    room_id = str(uuid.uuid4())
    
    # 创建新玩家
    new_player = {
        PlayerKey.ID.value: player_id,
        PlayerKey.Username.value: username,
        PlayerKey.Coins.value: DEFAULT_ROOM_SETTINGS[RoomSettingKey.InitialCoins.value],
        PlayerKey.Status.value: PlayerStatus.Spectator.value,
        PlayerKey.Avatar.value: None, #?,
        PlayerKey.IsOnline.value: True,
        PlayerKey.Folded.value: False,
    }
    
    # 创建新房间
    rooms[room_id] = {
        RoomKey.Name.value: room_name or f"{username}的房间",  # 房间名称
        RoomKey.Players.value: [new_player],  # 使用列表存储玩家，保持顺序
        RoomKey.ReadyPlayers.value: set(),  # 准备就绪的玩家
        RoomKey.Owner.value: player_id,  # 创建房间的人成为该房间的首任房主
        RoomKey.Settings.value: DEFAULT_ROOM_SETTINGS.copy(),  # 游戏设置
        RoomKey.GameStatus.value: GameStatus.Wating.value,  # 游戏状态
        RoomKey.Status.value: RoomStatus.Normal.value,  # 房间状态?
        RoomKey.Seats.value: [None] * DEFAULT_ROOM_SETTINGS[RoomSettingKey.MaxPlayerNumber.value],  # 座位信息
        RoomKey.LastSeatTime.value: {},  # 记录每个玩家最后一次坐下的时间
        RoomKey.LastWinner.value: None,  # 上一局的赢家ID，用于确定下一局的庄家
        RoomKey.GameData.value: None,  # 游戏数据，存储当前游戏状态
        RoomKey.ContinueGameData.value: None,  # 继续游戏数据
        RoomKey.GameLog.value: [],  # 游戏日志
    }
    
    return room_id


def join_room(room_id, player_id, username):
    """
    加入房间，
    返回是否成功加入
    """
    if room_id not in rooms:
        return False
    
    room = rooms[room_id]
    # 检查房间是否已满
    max_players = room[RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber.value]
    if len(room[RoomKey.Players.value]) >= max_players:
        print(f"房间 {room_id} 已满，无法加入")
        return False
        
    # 检查玩家是否已在房间中
    player, player_index = find_player_in_room(room_id, player_id)
    
    if player is not None:
        # 玩家已存在，更新在线状态
        print(f"玩家 {username} 已存在，更新状态为观众，重置金币数")
        player[PlayerKey.Status.value] = PlayerStatus.Spectator.value
        player[PlayerKey.Username.value] = username
        player[PlayerKey.Coins.value] = room[RoomKey.Settings.value][RoomSettingKey.InitialCoins.value]
        player[PlayerKey.IsOnline.value] = True
        player[PlayerKey.Folded.value] = False
        return True
    
    # 创建新玩家
    new_player = {
        PlayerKey.ID.value: player_id,
        PlayerKey.Username.value: username,
        PlayerKey.Coins.value: room[RoomKey.Settings.value][RoomSettingKey.InitialCoins.value],
        PlayerKey.Status.value: PlayerStatus.Spectator.value,
        PlayerKey.Avatar.value: None, #?,
        PlayerKey.IsOnline.value: True,
        PlayerKey.Folded.value: False,
    }
    
    # 添加玩家到房间
    room[RoomKey.Players.value].append(new_player)
    return True


def leave_room(room_id, player_id):
    """
    离开房间，
    返回是否成功离开
    """
    if room_id not in rooms:
        print(f"room, id: {room_id}, not exist")
        return False
    
    room = rooms[room_id]
    
    # 查找玩家在列表中的位置
    player, player_index = find_player_in_room(room_id, player_id)
    
    # 检查玩家是否存在
    if player is None:
        print(f"player, id: {player_id}, not exist in room, id: {room_id}")
        return False
        
    # 移除玩家
    room[RoomKey.Players.value].pop(player_index)
    
    # 如果房间为空，删除房间
    if not room[RoomKey.Players.value]:
        del rooms[room_id]
        return True
        
    # 如果离开的是房主，转移房主身份
    if room[RoomKey.Owner.value] == player_id:
        # 选择第一个玩家作为新房主
        if room[RoomKey.Players.value]:
            room[RoomKey.Owner.value] = room[RoomKey.Players.value][0][PlayerKey.ID.value]
            
    return True


def update_player_online_status(room_id, player_id, is_online=True):
    """
    更新玩家在线状态
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        return False
        
    player[PlayerKey.IsOnline.value] = is_online
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


def get_room_details(room_id):
    """
    获取房间详细信息
    返回房间的完整信息，包括玩家详细信息
    """
    if room_id not in rooms:
        return None
        
    room = rooms[room_id].copy()
    room[RoomKey.ID.value] = room_id
    
    # 转换玩家信息，不包括手牌
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
    获取房间玩家列表
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


def update_room_settings(room_id, settings):
    """
    更新房间设置
    返回是否成功更新
    """
    if room_id not in rooms:
        return False
        
    # 验证设置
    if RoomSettingKey.MinPlayers.value in settings and settings[RoomSettingKey.MinPlayers.value] < 2:
        return False
        
    if RoomSettingKey.MaxPlayers.value in settings and settings[RoomSettingKey.MaxPlayers.value] > 4:
        return False
        
    if RoomSettingKey.MinPlayers.value in settings and RoomSettingKey.MaxPlayers.value in settings:
        if settings[RoomSettingKey.MinPlayers.value] > settings[RoomSettingKey.MaxPlayers.value]:
            return False
            
    # 更新设置
    for key, value in settings.items():
        if key in DEFAULT_ROOM_SETTINGS:
            rooms[room_id][RoomKey.Settings.value][key] = value
            
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
        if player[PlayerKey.IsOnline.value]:
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
        if player[PlayerKey.Status.value] == PlayerStatus.Ready.value and player[PlayerKey.IsOnline.value]:
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