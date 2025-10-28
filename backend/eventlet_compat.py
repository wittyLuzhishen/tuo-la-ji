#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Eventlet兼容层
为Python 3.13提供eventlet.sleep功能的替代实现
"""

import time

# 模拟eventlet.sleep函数
def sleep(seconds=0):
    """替代eventlet.sleep的函数，使用time.sleep实现"""
    time.sleep(seconds)