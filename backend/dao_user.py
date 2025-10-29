# 存储用户信息
users = {}

def get_user_info(user_id: str) -> dict:
    """
    获取用户信息的引用，直接修改返回结果会影响到存储的用户信息
    """
    return users.get(user_id, None)

def set_user_info(user_id: str, user_info: dict):
    """
    设置用户信息
    """
    users[user_id] = user_info