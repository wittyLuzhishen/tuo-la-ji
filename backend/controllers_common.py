# -*- coding: utf-8 -*-
"""
通用控制器模块

此模块包含游戏的通用Socket.IO事件处理函数，如连接、房间管理、玩家状态更新等。
所有Socket.IO事件处理函数都接收客户端发送的数据，进行验证后调用相应的业务逻辑处理函数。

模块功能：
- 处理客户端连接和断开事件
- 房间管理（创建、加入、离开、获取列表等）
- 玩家状态管理（准备、坐下、站起等）
- 房间设置管理
- 头像上传和获取功能
- 文件上传验证工具
- 日志文件下载接口
"""

import os
import uuid
import logging
from flask import jsonify, render_template, request, send_from_directory, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from app import app
from message_enums import (ClientMessageType, ClientDataKey, ServerDataKey)
from extensions import socketio
from utils import require_data, get_logger, safe_get_string
from biz_common import (handle_connect, handle_continue_game, handle_create_room, 
    handle_get_room_details, handle_get_room_list, handle_join_room, handle_kick_player, 
    handle_leave_room, handle_disconnect, handle_ready, handle_set_userinfo, 
    handle_sit_down, handle_stand_up, handle_update_settings, handle_reconnect
)

# 获取模块日志器
logger = get_logger(__name__)


# 路由定义
@app.route("/")
def lobby():
    """
    大厅页面路由
    返回房间列表页面HTML模板
    
    Returns:
        str: HTML模板渲染结果
    """
    logger.debug("访问游戏大厅页面")
    return render_template("lobby.html")


@app.route("/room")
def room():
    """
    游戏房间页面路由
    返回游戏房间页面HTML模板
    
    Returns:
        str: HTML模板渲染结果
    """
    logger.debug("访问游戏房间页面")
    return render_template("room.html")

# 注册Socket.IO事件处理函数
@socketio.on(ClientMessageType.Connect.value)
def connect():
    """
    处理客户端连接/重连事件
    
    注意：Socket.IO的connect事件默认不会接收客户端数据，除非客户端特别发送
    这里移除了require_data装饰器，因为connect事件默认可能没有data参数
    """
    # 记录日志，使用socket_id作为标识
    socket_id = request.sid
    logger.info(f"客户端连接事件: 会话ID={socket_id}")
    
    # 处理连接，只建立基础连接
    # 不再立即分配或发送user_id，等待客户端可能的reconnect_with_id请求
    handle_connect()


@socketio.on(ClientMessageType.ReconnectWithID.value)
@require_data
def reconnect_with_id(data):
    """
    处理客户端重连时提供的user_id
    
    客户端在连接后会发送之前保存的user_id，用于服务器识别重连的用户
    如果未提供user_id或重连失败，则分配新的user_id

    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    # 调用handle_reconnect处理重连或新连接逻辑
    handle_reconnect(user_id)


@socketio.on(ClientMessageType.Disconnect.value)
def disconnect():
    """
    处理客户端断开连接事件
    
    关键点：在这个应用中，用户的user_id被直接用作Socket.IO的会话ID(sid)
    这样我们可以通过request.sid直接获取断开连接的用户ID
    
    Args:
        data (str, optional): 断开连接的原因字符串或自定义数据
    """
    
    # 获取logger
    logger = logging.getLogger(__name__)
    
    # 关键：使用request.sid获取断开连接的会话ID，在这个应用中它等于user_id
    user_id = request.sid
    reason = request.args.get("reason", "")
    
    logger.info(f"客户端断开连接: 用户={user_id}, 原因={reason}")
    
    handle_disconnect(reason, user_id)


@socketio.on(ClientMessageType.GetRoomList.value)
def get_room_list():
    """
    处理获取房间列表事件
    
    客户端请求获取所有可用的游戏房间列表
    """
    logger.debug("请求获取房间列表")
    handle_get_room_list()


@socketio.on(ClientMessageType.GetRoomDetails.value)
@require_data
def get_room_details(data):
    """
    处理获取房间详情事件
    """
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, '未知房间')
    logger.debug(f"请求获取房间详情: {room_id}")
    handle_get_room_details(room_id)


@socketio.on(ClientMessageType.CreateRoom.value)
@require_data
def create_room(data):
    """
    处理创建房间事件

    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value)
    logger.info(f"创建房间: 用户={user_id}")
    # 安全地获取room_name，处理可能的null值
    room_name = safe_get_string(data, ClientDataKey.RoomName.value)
    # 调用业务逻辑创建房间，传入用户ID和房间名称
    handle_create_room(user_id, room_name)


@socketio.on(ClientMessageType.JoinRoom.value)
@require_data
def join_room(data):
    """
    处理加入房间事件

    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value)
    room_id = safe_get_string(data, ClientDataKey.RoomID.value)
    handle_join_room(user_id, room_id)


@socketio.on(ClientMessageType.LeaveRoom.value)
@require_data
def leave_room(data):
    """
    处理离开房间事件

    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    handle_leave_room(user_id, room_id)


@socketio.on(ClientMessageType.SitDown.value)
@require_data
def sit_down(data):
    """
    处理玩家坐下事件

    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    seat_index = int(data.get(ClientDataKey.SeatIndex.value, -1))
    handle_sit_down(user_id, room_id, seat_index)


@socketio.on(ClientMessageType.StandUp.value)
@require_data
def stand_up(data):
    """
    处理玩家站起事件
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    logger.debug(f"玩家站起: 用户={user_id}, 房间={room_id}")
    handle_stand_up(user_id, room_id)


@socketio.on(ClientMessageType.Ready.value)
@require_data
def toggle_ready(data):
    """
    处理玩家准备/取消准备事件
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    turn_ready = data.get(ClientDataKey.Ready.value, True)
    logger.debug(f"玩家准备状态变更: 用户={user_id}, 房间={room_id}, 准备={turn_ready}")
    handle_ready(user_id, room_id, turn_ready)


@socketio.on(ClientMessageType.UpdateRoomSettings.value)
@require_data
def update_settings(data):
    """
    处理更新房间设置事件（仅房主可操作）
    """

    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    settings = data.get(ClientDataKey.Settings.value, None)
    logger.info(f"更新房间设置: 用户={user_id}, 房间={room_id}")
    handle_update_settings(user_id, room_id, settings)


@socketio.on(ClientMessageType.KickPlayer.value)
@require_data
def kick_player(data):
    """
    处理踢出玩家事件（仅房主可操作）
    
    即便玩家已经就绪也可以踢出，可以踢出不喜欢的玩家。
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    to_be_kicked_user_id = safe_get_string(data, ClientDataKey.PlayerIdToBeKicked.value, "")
    logger.info(f"踢出玩家: 发起用户={user_id}, 房间={room_id}, 被踢出玩家={to_be_kicked_user_id}")
    handle_kick_player(user_id, room_id, to_be_kicked_user_id)


@socketio.on(ClientMessageType.ContinueGame.value)
@require_data
def continue_game(data):
    """
    处理游戏继续/退出选择
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    room_id = safe_get_string(data, ClientDataKey.RoomID.value, "")
    continue_game = data.get(ClientDataKey.ContinueGame.value, False)
    logger.debug(f"游戏继续选择: 用户={user_id}, 房间={room_id}, 选择继续={continue_game}")
    handle_continue_game(user_id, room_id, continue_game)


@socketio.on(ClientMessageType.SetUserInfo.value)
@require_data
def set_userinfo(data):
    """
    处理设置用户信息事件
    """
    user_id = safe_get_string(data, ClientDataKey.UserID.value, "")
    username = safe_get_string(data, ClientDataKey.Username.value, "")
    avatar_url = safe_get_string(data, ClientDataKey.AvatarURL.value, "")
    logger.info(f"设置用户信息: 用户ID={user_id}, 用户名={username}, 头像地址：{avatar_url}")
    handle_set_userinfo(user_id, username, avatar_url)


@app.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    """
    处理头像上传路由
    接收前端上传的头像文件，验证后保存到服务器
    
    支持的文件类型: PNG, JPG, JPEG, GIF, WEBP
    
    Returns:
        JSON: 包含头像URL或错误信息的响应
    """
    try:
        if "file" not in request.files:
            logger.warning("上传头像时没有文件部分")
            return jsonify({"error": "没有文件部分"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            logger.warning("上传头像时没有选择文件")
            return jsonify({"error": "没有选择文件"}), 400
        
        if file and app_allowed_file(file.filename):
            # 安全处理文件名
            filename = secure_filename(file.filename)
            # 添加UUID前缀避免文件名冲突
            filename = f"{uuid.uuid4().hex}_{filename}"
            
            # 确保上传目录存在
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            
            # 返回文件访问URL
            file_url = f"/static/avatars/{filename}"
            logger.info(f"头像上传成功: {filename}")
            return jsonify({ServerDataKey.AvatarURL.value: file_url})
        
        logger.warning(f"不支持的文件类型: {file.filename}")
        return jsonify({"error": "不支持的文件类型"}), 400
    except Exception as e:
        logger.exception(f"头像上传失败: {str(e)}")
        return jsonify({"error": "文件上传失败，请稍后重试"}), 500


# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def app_allowed_file(filename):
    """
    检查文件扩展名是否被允许
    
    Args:
        filename: 文件名
    
    Returns:
        bool: 如果文件扩展名允许，返回True，否则返回False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/static/avatars/<filename>")
def get_avatar(filename):
    """
    获取头像文件路由
    提供头像文件的访问接口
    
    Args:
        filename: 头像文件名
    
    Returns:
        文件响应: 头像文件内容
    """
    logger.debug(f"请求头像文件: {filename}")
    try:
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    except Exception as e:
        logger.exception(f"获取头像失败: {filename} - {str(e)}")
        return jsonify({"error": "头像文件不存在或无法访问"}), 404


@app.route("/download_log", methods=["GET"])
def download_log():
    """
    下载日志文件接口
    
    提供服务器日志文件的下载功能，用于问题排查和监控。
    支持下载当前日志和历史日志备份。
    
    Query Parameters:
        backup: 可选参数，指定备份日志文件索引（0-4）
        
    Returns:
        文件响应: 日志文件内容
    """
    try:
        # 获取logs目录
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        
        # 检查backup参数
        backup = request.args.get('backup', None)
        if backup is not None:
            try:
                backup_index = int(backup)
                if 0 <= backup_index <= 4:
                    log_filename = f'app.log.{backup_index}'
                else:
                    logger.warning(f"无效的备份索引: {backup}")
                    return jsonify({"error": "无效的备份索引，应为0-4"}), 400
            except ValueError:
                logger.warning(f"备份索引不是数字: {backup}")
                return jsonify({"error": "备份索引必须是数字"}), 400
        else:
            log_filename = 'app.log'
        
        log_path = os.path.join(logs_dir, log_filename)
        
        # 检查文件是否存在
        if not os.path.exists(log_path):
            logger.warning(f"日志文件不存在: {log_filename}")
            return jsonify({"error": f"日志文件 {log_filename} 不存在"}), 404
        
        # 检查文件大小，避免下载过大文件
        file_size = os.path.getsize(log_path)
        if file_size > 50 * 1024 * 1024:  # 50MB限制
            logger.warning(f"日志文件过大: {file_size} bytes")
            return jsonify({"error": "日志文件过大，无法下载"}), 413
        
        logger.info(f"下载日志文件: {log_filename}")
        return send_file(log_path, as_attachment=True, download_name=f'tuolaji_log_{log_filename}')
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"下载日志文件失败: {str(e)}")
        return jsonify({"error": "下载日志文件失败，请稍后重试"}), 500


# 全局异常处理器
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """
    处理HTTP异常
    
    Args:
        e: HTTP异常对象
    
    Returns:
        JSON响应：包含错误码和错误消息
    """
    if e.code == 404:
        logger.error(f"HTTP异常: {e.name} ({e.code}) - {e.description} - 未匹配的URL: {request.path}")
    else:
        logger.error(f"HTTP异常: {e.name} ({e.code}) - {e.description}")
    response = {
        "error": True,
        "code": e.code,
        "message": e.name,
        "description": e.description
    }
    return jsonify(response), e.code


@app.errorhandler(Exception)
def handle_general_exception(e):
    """
    处理一般异常（非HTTP异常）
    
    Args:
        e: 异常对象
    
    Returns:
        JSON响应：包含错误码和错误消息
    """
    logger.exception(f"未捕获的异常: {str(e)}")
    response = {
        "error": True,
        "code": 500,
        "message": "服务器内部错误",
        "description": "发生了未预期的服务器错误，请稍后再试"
    }
    return jsonify(response), 500


@app.errorhandler(413)
def request_entity_too_large(e):
    """
    处理文件过大异常
    
    Args:
        e: 异常对象
    
    Returns:
        JSON响应：包含错误码和错误消息
    """
    logger.warning(f"文件过大异常: {str(e)}")
    response = {
        "error": True,
        "code": 413,
        "message": "请求实体过大",
        "description": f"上传的文件超过了最大限制"
    }
    return jsonify(response), 413
