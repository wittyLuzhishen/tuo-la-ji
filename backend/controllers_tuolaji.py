from biz_tuolaji import handle_call, handle_fold, handle_raise, handle_showdown, handle_look_at_cards
from extensions import socketio


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
