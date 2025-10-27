from flask_socketio import SocketIO

# 允许跨域、指定使用threading作为异步模式
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")