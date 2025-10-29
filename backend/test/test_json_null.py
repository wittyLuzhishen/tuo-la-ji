"""
测试JSON null值在Python中的转换行为

当客户端通过Socket.IO发送包含null值的JSON对象时，
Python端接收到的数据中，null会被转换为Python的None类型。
"""

# 模拟Socket.IO中的JSON解析过程
import json

# 模拟客户端发送的JSON字符串，包含null值
test_json = '{"user_id": null, "room_id": "room123", "settings": null}'

# 在Socket.IO中，这一步会自动完成（解析JSON字符串为Python对象）
data = json.loads(test_json)

# 打印解析后的数据类型
print("解析后的data对象:", data)
print("数据类型:", type(data))
print("\n各个字段的值和类型:")
for key, value in data.items():
    print(f"{key}: 值={value}, 类型={type(value)}")

# 测试在实际使用中的处理方式
print("\n在实际代码中的处理示例:")
# 方式1：直接使用if判断
user_id = data.get('user_id')
print(f"user_id = {user_id}")
print(f"if user_id: {bool(user_id)}")  # None在布尔上下文中为False

# 方式2：检查是否为None
print(f"user_id is None: {user_id is None}")

# 方式3：使用默认值
user_id_default = data.get('user_id', 'default_user')
print(f"使用默认值的user_id: {user_id_default}")

# 方式4：针对可能为None的字符串进行strip操作前的检查
if user_id is not None:
    print(f"user_id.strip() 会抛出异常，因为None没有strip方法")
else:
    print(f"正确处理None值，避免调用不存在的方法")

# 方式5：安全的字符串处理方式
safe_user_id = str(user_id).strip() if user_id is not None else ""
print(f"安全处理后的user_id: '{safe_user_id}'")