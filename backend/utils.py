# 工具函数模块
import logging
import os
from logging.handlers import RotatingFileHandler

def safe_get_string(data, key, default=""):
    """
    安全地从数据字典中获取字符串值，并处理可能的None值
    
    Args:
        data (dict): 数据字典
        key (str): 要获取的键
        default (str, optional): 默认值，默认为空字符串
    
    Returns:
        str: 处理后的值
    """
    if not data or not key:
        return default
    value = data.get(key)
    if value is None:
        return default
    return str(value).strip()


def require_data(func):
    """
    检查Socket.IO事件处理器的data参数是否为None的装饰器
    如果data为None，则不继续执行处理函数
    """
    def wrapper(data=None):
        print(f"事件 {func.__name__} 收到数据: {data}")
        logger = get_logger()
        if data is None:
            logger.warning(f"事件没有收到数据: {func.__name__}")
            return
        # 确保data是字典格式
        if not isinstance(data, dict):
            logger.warning(f"事件 {func.__name__} 收到的数据不是字典格式：{data}")
            return
        return func(data)
    # 保留原始函数的名称和文档字符串
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def setup_logging(level=logging.INFO):
    """
    配置日志系统
    - 设置日志级别
    - 配置控制台输出
    - 配置文件输出（带轮转）
    """
    # 创建logs目录（如果不存在）
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 创建主日志器
    logger = logging.getLogger()
    logger.setLevel(level)  # 设置主日志器级别
    
    # 清除已存在的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 配置文件处理器（带轮转）
    log_file = os.path.join(logs_dir, 'app.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5  # 保留5个备份文件
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def get_logger(name=None):
    """
    获取指定名称的日志器
    如果name为None，返回根日志器
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()