from game_enum import ServerMessageType, ServerDataKey, RoomKey, PlayerKey
from dao_room import rooms, get_player_info
from flask_socketio import emit

def broadcast_game_info(room_id):
    """
    向房间内所有玩家广播游戏信息
    """
    if room_id not in rooms:
        return
        
    room = rooms[room_id]
    players_info = []
    
    for player in room[RoomKey.Players.value]:
        player_info = get_player_info(room_id, player[PlayerKey.ID.value])
        players_info.append(player_info)
    
    emit(ServerMessageType.GameInfo.value, {
        ServerDataKey.RoomID.value: room_id,
        ServerDataKey.Players.value: players_info,
        ServerDataKey.Seats.value: room[RoomKey.Seats.value],
        ServerDataKey.Owner.value: room[RoomKey.Owner.value],
        ServerDataKey.Settings.value: room[RoomKey.Settings.value],
        ServerDataKey.GameStatus.value: room[RoomKey.GameStatus.value],
        ServerDataKey.LastWinner.value: room[RoomKey.LastWinner.value],
        ServerDataKey.GameLog.value: room[RoomKey.GameLog.value],
        ServerDataKey.Status.value: room[RoomKey.Status.value],
        ServerDataKey.Pot.value: room[RoomKey.Pot.value],
        ServerDataKey.CurrentTurnPlayerID.value: room[RoomKey.CurrentTurnPlayerID.value],
        ServerDataKey.CurrentRound.value: room[RoomKey.CurrentRound.value],
        ServerDataKey.CurrentBet.value: room[RoomKey.CurrentBet.value],
    }, room=room_id)