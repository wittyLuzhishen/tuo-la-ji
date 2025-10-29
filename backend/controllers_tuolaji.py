# -*- coding: utf-8 -*-
"""
拖拉机游戏控制器模块

此模块包含拖拉机纸牌游戏的核心Socket.IO事件处理函数，
主要负责游戏逻辑相关的操作，如看牌、弃牌、跟注、加注和开牌等。

每个事件处理函数都会接收客户端发送的数据，进行验证后
调用相应的业务逻辑处理函数来执行具体操作。
"""

from biz_tuolaji import handle_call, handle_fold, handle_raise_bet, handle_showdown, handle_look_at_cards
from extensions import socketio
from utils import require_data, get_logger, safe_get_string
from message_enums import (ClientMessageType, ClientDataKey)

# 获取模块日志器
logger = get_logger(__name__)


@socketio.on(ClientMessageType.LookAtCards.value)
@require_data
def look_at_cards(data):
    """
    处理玩家看牌事件
    
    当玩家请求查看自己的手牌时触发此事件
    
    Args:
        data (dict): 包含以下字段的数据字典
            - user_id (str, required): 用户ID
            - room_id (str, required): 房间ID
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    logger.debug(f"玩家看牌请求: 用户={user_id}, 房间={room_id}")
    handle_look_at_cards(user_id, room_id)


@socketio.on(ClientMessageType.Fold.value)
@require_data
def fold(data):
    """
    处理玩家弃牌事件
    
    当玩家决定弃牌时触发此事件，玩家将退出当前轮次
    
    Args:
        data (dict): 包含以下字段的数据字典
            - user_id (str, required): 用户ID
            - room_id (str, required): 房间ID
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    logger.info(f"玩家弃牌: 用户={user_id}, 房间={room_id}")
    handle_fold(user_id, room_id)


@socketio.on(ClientMessageType.Call.value)
@require_data
def call(data):
    """
    处理玩家跟注事件
    
    当玩家决定跟注时触发此事件，玩家需要投入与当前最高下注相等的筹码
    
    Args:
        data (dict): 包含以下字段的数据字典
            - user_id (str, required): 用户ID
            - room_id (str, required): 房间ID
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    logger.info(f"玩家跟注: 用户={user_id}, 房间={room_id}")
    handle_call(user_id, room_id)


@socketio.on(ClientMessageType.Raise.value)
@require_data
def raise_bet(data):
    """
    处理玩家加注事件
    
    当玩家决定加注时触发此事件，玩家需要增加底池中的筹码
    
    Args:
        data (dict): 包含以下字段的数据字典
            - user_id (str, required): 用户ID
            - room_id (str, required): 房间ID
            - amount (int, required): 要加注的金额
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    raise_amount = data.get(ClientDataKey.AddAmount.value, 0)
    logger.info(f"玩家加注: 用户={user_id}, 房间={room_id}, 金额={raise_amount}")
    handle_raise_bet(user_id, room_id, raise_amount)


@socketio.on(ClientMessageType.Showdown.value)
@require_data
def showdown(data):
    """
    处理玩家开牌（比牌）事件
    
    当玩家决定开牌（比牌）时触发此事件，需要指定要比较的对手
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    player_id_to_be_showdown = safe_get_string(data, ClientDataKey.PlayerIdToBeShowdown.value)
    logger.info(f"玩家开牌: 用户={user_id}, 房间={room_id}, 被开牌用户={player_id_to_be_showdown}")
    handle_showdown(user_id, room_id, player_id_to_be_showdown)
