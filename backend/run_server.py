import eventlet

# 在导入任何其他模块之前先执行monkey_patch
eventlet.monkey_patch()

# 然后再导入Flask应用
from app import app, socketio
import sys

if __name__ == "__main__":
    """
    应用程序入口点
    - 处理命令行参数，设置服务器端口
    - 实现端口冲突处理机制，自动尝试使用其他可用端口
    - 启动SocketIO服务器
    """
    print("服务器启动中...")
    
    # 从命令行参数获取端口号，默认为5000
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"无效的端口号: {sys.argv[1]}，使用默认端口5000")
    
    # 尝试启动服务器，处理端口冲突
    max_attempts = 5  # 最大尝试端口数量
    attempts = 0
    
    while attempts < max_attempts:
        try:
            print(f"尝试在端口 {port} 启动服务器...")
            # 启动SocketIO服务器
            # - host='0.0.0.0'：监听所有网络接口
            # - debug=True：启用调试模式
            # - use_reloader=False：禁用自动重载，避免多进程问题
            socketio.run(app, host="0.0.0.0", port=port, debug=True, use_reloader=False)
            break  # 如果启动成功，跳出循环
        except OSError as e:
            # 处理Windows平台端口被占用的错误
            if "[WinError 10048]" in str(e):
                attempts += 1
                port += 1
                print(f"端口 {port-1} 已被占用，尝试使用端口 {port}")
            else:
                # 处理其他可能的错误
                print(f"启动服务器时出错: {e}")
                break
    
    if attempts >= max_attempts:
        # 所有尝试的端口都被占用，输出错误信息
        print(f"无法找到可用端口，尝试了端口 {port - max_attempts} 到 {port-1}")