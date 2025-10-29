from flask_socketio import SocketIO

# 允许跨域、指定使用eventlet作为异步模式
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",
    # 添加心跳检测参数，防止连接自动断开
    ping_interval=25,        # 心跳发送间隔（秒）
    ping_timeout=60,         # 心跳超时时间（秒）
    max_http_buffer_size=10*1024*1024,  # 最大消息大小（10MB）
    engineio_logger=False    # 禁用engineio日志
)