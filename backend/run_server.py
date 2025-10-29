#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器启动脚本
强制使用eventlet模式启动Socket.IO，确保所有I/O操作非阻塞
"""

import sys
import platform
import os
import eventlet

# 在导入任何其他模块之前先执行monkey_patch
print("正在执行eventlet.monkey_patch()...")
eventlet.monkey_patch()
print("已启用eventlet.monkey_patch，确保所有I/O操作非阻塞")

# 检查Python版本
print(f"当前Python版本: {platform.python_version()}")
print("已导入eventlet模块")

# 现在导入应用模块
from app import app
from extensions import socketio

if __name__ == "__main__":
    print("服务器启动中...")
    
    # 优先从环境变量获取端口号，其次是命令行参数，最后使用默认值
    port = int(os.getenv("PORT", 5000))
    
    # 如果提供了命令行参数，则覆盖环境变量设置的端口
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            print(f"使用命令行参数指定的端口: {port}")
        except ValueError:
            print(f"无效的端口号: {sys.argv[1]}，使用环境变量或默认端口 {port}")
    
    print(f"尝试使用eventlet模式在端口 {port} 启动服务器...")
    print(f"服务器地址: http://0.0.0.0:{port}")
    print("按 Ctrl+C 停止服务器")
    
    # 强制使用eventlet模式启动，与Procfile配置保持一致
    # 添加allow_unsafe_werkzeug=True以支持在Render等平台部署
    print("注意: 生产环境强烈建议使用Gunicorn或uWSGI而非直接使用Werkzeug")
    print("示例: gunicorn --worker-class eventlet -w 1 app:app")
    
    # 使用eventlet模式（在extensions.py中设置）运行Socket.IO服务器
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)