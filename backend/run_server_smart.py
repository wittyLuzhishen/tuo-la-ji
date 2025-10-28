#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
兼容Python 3.13的启动脚本
使用threading模式启动Socket.IO，但保留协程功能
"""

import sys
import time
import platform

# 检查Python版本
print(f"当前Python版本: {platform.python_version()}")

# 为了在Python 3.13中支持协程，我们创建一个智能的sleep函数
def smart_sleep(seconds=0):
    """
    智能睡眠函数，尝试使用eventlet.sleep，失败则回退到time.sleep
    """
    try:
        import eventlet
        eventlet.sleep(seconds)
        return True
    except ImportError:
        time.sleep(seconds)
        return False
    except Exception:
        time.sleep(seconds)
        return False

# 将smart_sleep注入到全局命名空间，供其他模块使用
import builtins
builtins.smart_sleep = smart_sleep
print("已注册smart_sleep函数以支持协程功能")

# 现在导入应用模块
from app import app
from extensions import socketio

if __name__ == "__main__":
    print("服务器启动中...")
    
    # 从命令行参数获取端口号，默认为5000
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"无效的端口号: {sys.argv[1]}，使用默认端口5000")
    
    print(f"使用threading模式在端口 {port} 启动服务器...")
    print(f"服务器地址: http://0.0.0.0:{port}")
    print("按 Ctrl+C 停止服务器")
    
    # 使用threading模式启动，避免eventlet的兼容性问题
    # 但通过smart_sleep函数保留协程功能的部分优势
    # 添加allow_unsafe_werkzeug=True以支持在Render等平台部署
    print("注意: 生产环境强烈建议使用Gunicorn或uWSGI而非直接使用Werkzeug")
    print("示例: gunicorn --worker-class eventlet -w 1 app:app")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)