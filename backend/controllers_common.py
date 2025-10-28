import os
import uuid
from flask import jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from app import app
from extensions import socketio
from biz_common import (allowed_file, handle_connect, handle_continue_game, handle_create_room, 
    handle_get_room_details, handle_get_room_list, handle_join_room, handle_kick_player, 
    handle_leave_room, handle_disconnect, handle_ready, handle_set_avatar, handle_set_userinfo, 
    handle_sit_down, handle_stand_up, handle_update_settings
)

# 路由定义
@app.route("/")
def lobby():
    """
    大厅页面路由
    返回房间列表页面HTML模板
    """
    return render_template("lobby.html")

@app.route("/room")
def room():
    """
    游戏房间页面路由
    返回游戏房间页面HTML模板
    """
    return render_template("room.html")

# 注册Socket.IO事件处理函数
@socketio.on("connect")
def connect(data):
    """处理客户端连接/重连事件"""
    handle_connect(data)


@socketio.on("disconnect")
def disconnect(data):
    """处理客户端断开连接事件，接收断开原因参数"""
    handle_disconnect(request.args.get("reason", ""), data)


@socketio.on("set_userinfo")
def set_userinfo(data):
    """处理设置用户信息事件"""
    handle_set_userinfo(data)


@socketio.on("get_room_list")
def get_room_list():
    """处理获取房间列表事件"""
    handle_get_room_list()


@socketio.on("get_room_details")
def get_room_details(data):
    """处理获取房间详情事件"""
    handle_get_room_details(data)


@socketio.on("create_room")
def create_room(data):
    """处理创建房间事件"""
    handle_create_room(data)


@socketio.on("join_room")
def join_room(data):
    """处理加入房间事件"""
    handle_join_room(data)


@socketio.on("leave_room")
def leave_room(data):
    """处理离开房间事件"""
    handle_leave_room(data)


@socketio.on("sit_down")
def sit_down(data):
    """处理玩家坐下事件"""
    handle_sit_down(data)


@socketio.on("stand_up")
def stand_up(data):
    """处理玩家站起事件"""
    handle_stand_up(data)


@socketio.on("ready")
def toggle_ready(data):
    """处理玩家准备/取消准备事件"""
    handle_ready(data)


@socketio.on("update_settings")
def update_settings(data):
    """处理更新房间设置事件（仅房主可操作）"""
    handle_update_settings(data)


@socketio.on("kick_player")
def kick_player(data):
    """处理踢出玩家事件（仅房主可操作）。即便玩家已经就绪也可以踢出，可以踢出不喜欢的玩家。"""
    handle_kick_player(data)


@socketio.on("continue_game")
def continue_game(data):
    """处理游戏继续/退出选择"""
    handle_continue_game(data)


@socketio.on("set_avatar")
def set_avatar(data):
    """处理设置头像事件"""
    handle_set_avatar(data)


@app.route("/upload_avatar", methods=["POST"])
def upload_avatar():
    """
    处理头像上传路由
    接收前端上传的头像文件，验证后保存到服务器
    """
    if "file" not in request.files:
        return jsonify({"error": "没有文件部分"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "没有选择文件"}), 400
    
    if file and allowed_file(file.filename):
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
        return jsonify({"url": file_url})
    
    return jsonify({"error": "不支持的文件类型"}), 400


@app.route("/static/avatars/<filename>")
def get_avatar(filename):
    """
    获取头像文件路由
    提供头像文件的访问接口
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
