import time
from flask_socketio import emit
from dao_room import find_player_in_room, is_game_started, rooms
from game_enums import (RoomKey)
from message_enums import (ServerMessageType, ServerDataKey)


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

def common_check(user_id:str, room_id:str, should_game_started:bool=None)->dict:
    if not user_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "用户ID不能为空"})
        return None
        
    if not room_id:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "房间ID不能为空"})
        return None
        
    if room_id not in rooms:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"房间号{room_id}不存在"})
        return None
        
    if should_game_started is not None:
        if should_game_started and not is_game_started(room_id):
            emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏未开始，无法操作"})
            return None
        elif not should_game_started and is_game_started(room_id):
            emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: "游戏已开始，无法操作"})
            return None

    # 查找玩家
    player = find_player_in_room(room_id, user_id)[0]
    if not player:
        emit(ServerMessageType.Error.value, {ServerDataKey.Message.value: f"{user_id}不在房间{room_id}中"})
        return None
    
    return player