# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏后端服务
基于Flask和SocketIO实现的实时多人在线扑克游戏
功能说明：
- 支持多人在线实时对战
- 实现拖拉机纸牌游戏规则
- 提供用户管理、房间管理、游戏逻辑等完整功能
- 支持头像上传和个性化设置
"""

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import uuid

# 导入自定义模块
from event_handlers import (
    handle_connect, handle_disconnect, handle_set_username,
    handle_create_room, handle_join_room, handle_leave_room,
    handle_get_room_list, handle_get_room_details,
    handle_sit_down, handle_stand_up, handle_ready,
    handle_update_settings, handle_kick_player,
    handle_start_game, handle_look_at_cards, handle_fold,
    handle_call, handle_raise, handle_showdown, handle_continue_game,
    handle_set_avatar
)
from utils import allowed_file

# Flask应用初始化
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # 应用密钥，用于会话安全
app.config["DEBUG"] = True  # 调试模式
app.config["UPLOAD_FOLDER"] = "static/avatars/"  # 头像上传目录

# 初始化SocketIO，指定使用threading作为异步模式
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# 注册Socket.IO事件处理函数
@socketio.on("connect")
def connect():
    """处理客户端连接/重连事件"""
    handle_connect()

@socketio.on("disconnect")
def disconnect(reason):
    """处理客户端断开连接事件，接收断开原因参数"""
    handle_disconnect(reason)

@socketio.on("set_username")
def set_username(data):
    """处理设置用户名事件"""
    handle_set_username(data)

@socketio.on("create_room")
def create_room():
    """处理创建房间事件"""
    handle_create_room()

@socketio.on("join_room")
def join_room(data):
    """处理加入房间事件"""
    handle_join_room(data)

@socketio.on("leave_room")
def leave_room():
    """处理离开房间事件"""
    handle_leave_room()

@socketio.on("get_room_list")
def get_room_list():
    """处理获取房间列表事件"""
    handle_get_room_list()

@socketio.on("get_room_details")
def get_room_details(data):
    """处理获取房间详情事件"""
    handle_get_room_details(data)

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

@socketio.on("continue_game")
def continue_game(data):
    """处理游戏继续/退出选择"""
    handle_continue_game(data)

@socketio.on("set_avatar")
def set_avatar(data):
    """处理设置头像事件"""
    handle_set_avatar(data)


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


# 启动应用
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)