# 使用更兼容配置的服务器启动脚本
from app_new import app, socketio
import sys

if __name__ == "__main__":
    """
    应用程序入口点
    - 处理命令行参数，设置服务器端口
    - 实现端口冲突处理机制，自动尝试使用其他可用端口
    - 启动SocketIO服务器，使用更兼容的配置
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
            # 启动SocketIO服务器，使用更兼容的配置
            socketio.run(
                app, 
                host="0.0.0.0", 
                port=port, 
                debug=False,  # 关闭调试模式
                use_reloader=False
            )
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