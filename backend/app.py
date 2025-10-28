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


from flask import Flask
from extensions import socketio

# Flask应用初始化
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # 应用密钥，用于会话安全
app.config["DEBUG"] = True  # 调试模式
app.config["UPLOAD_FOLDER"] = "static/avatars/"  # 头像上传目录

# 导入自定义模块（在app创建后导入，避免循环导入）
import controllers_common
import controllers_tuolaji

# 初始化SocketIO
socketio.init_app(app)


# 启动应用
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)