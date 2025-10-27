from extensions import socketio

@socketio.on("start_game")
def start_game(data):
    """处理开始游戏事件（仅房主可操作）"""
    handle_start_game(data)

@socketio.on("look_at_cards")
def look_at_cards(data):
    """处理玩家看牌事件"""
    handle_look_at_cards(data)

@socketio.on("fold")
def fold(data):
    """处理玩家弃牌事件"""
    handle_fold(data)

@socketio.on("call")
def call(data):
    """处理玩家跟注事件"""
    handle_call(data)

@socketio.on("raise")
def raise_bet(data):
    """处理玩家加注事件"""
    handle_raise(data)

@socketio.on("showdown")
def showdown(data):
    """处理玩家开牌事件"""
    handle_showdown(data)
