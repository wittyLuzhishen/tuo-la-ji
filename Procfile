# Procfile配置说明
# web: 指定这是一个web进程
# gunicorn: 使用Gunicorn作为WSGI HTTP服务器
# -k eventlet: 使用eventlet工作模式，支持异步处理和WebSocket
# -w 1: 设置1个工作进程（对于WebSocket应用通常设置为1）
# app:app: 加载app模块中的app对象作为Flask应用实例
web: gunicorn -k eventlet -w 1 app:app