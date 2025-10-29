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


import os
from flask import Flask
from extensions import socketio
from utils import setup_logging

# 初始化日志系统
logger = setup_logging()
logger.info("启动拖拉机纸牌游戏后端服务...")

# Flask应用初始化
app = Flask(__name__)

# 基本配置
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")  # 从环境变量获取密钥
app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")  # 从环境变量控制调试模式
app.config["UPLOAD_FOLDER"] = "static/avatars/"  # 头像上传目录

# 文件上传限制配置，这是Flask框架的配置系统的一部分
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 最大上传文件大小：1MB
# 确保上传目录存在
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 导入自定义模块（在app创建后导入，避免循环导入）
import controllers_common
import controllers_tuolaji

# 初始化SocketIO
socketio.init_app(app)


# 启动应用
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"在端口 {port} 启动服务器...")
    socketio.run(app, debug=app.config["DEBUG"], host="0.0.0.0", port=port)