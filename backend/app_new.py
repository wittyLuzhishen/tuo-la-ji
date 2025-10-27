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

from extensions import socketio
import controllers_common
import controllers_tuolaji

# Flask应用初始化
app:Flask = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # 应用密钥，用于会话安全
app.config["DEBUG"] = True  # 调试模式
app.config["UPLOAD_FOLDER"] = "static/avatars/"  # 头像上传目录

# 初始化SocketIO
socketio.init_app(app)


# 启动应用
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)