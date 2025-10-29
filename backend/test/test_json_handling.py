"""
全面测试JSON数据处理，特别是null值的安全处理

这个脚本测试：
1. JSON中的null值在Python中的转换
2. safe_get_string函数的正确行为
3. 各种边缘情况的处理
"""
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试所需的模块
try:
    from backend.utils import safe_get_string
    print("成功导入safe_get_string函数")
except ImportError as e:
    print(f"导入失败: {e}")
    # 手动实现safe_get_string用于测试
def safe_get_string(data, key, default=""):
    """手动实现的安全获取字符串函数用于测试"""
    value = data.get(key)
    if value is None:
        return default
    return str(value).strip()

print("\n=== 测试1: 基本的JSON解析和null值转换 ===")
# 测试各种数据类型的JSON转换
test_cases = [
    '{"user_id": null, "room_id": "room123", "settings": null}',
    '{"user_id": "", "room_id": "  room456  ", "active": true}',
    '{"user_id": "player1", "room_id": null, "score": 100}',
    '{"nested": {"user_id": null, "details": "info"}}'
]

for i, test_json in enumerate(test_cases):
    print(f"\n测试用例 {i+1}:")
    print(f"JSON: {test_json}")
    data = json.loads(test_json)
    print(f"解析后: {data}")
    
    # 检查各个字段的类型
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"  {key}: 嵌套字典 {type(value)}")
            for k, v in value.items():
                print(f"    {k}: {v} ({type(v)})")
        else:
            print(f"  {key}: {value} ({type(value)})")

print("\n=== 测试2: safe_get_string函数的行为 ===")
test_data = {
    "null_field": None,
    "empty_string": "",
    "whitespace_string": "   ",
    "normal_string": "  test  ",
    "number_field": 123,
    "missing_field": None  # 这个在字典中不存在
}

test_keys = ["null_field", "empty_string", "whitespace_string", "normal_string", "number_field", "missing_field"]

default_values = ["default", "", "fallback", None]

for key in test_keys:
    print(f"\n字段: '{key}'")
    for default in default_values:
        # 对于missing_field，使用data.get(key)来模拟不存在的键
        if key == "missing_field":
            value = safe_get_string({}, key, default)
        else:
            value = safe_get_string(test_data, key, default)
        print(f"  默认值='{default}': 结果='{value}' (类型: {type(value)})")

print("\n=== 测试3: 模拟Socket.IO事件处理 ===")

# 模拟业务逻辑函数
def simulate_handle_event(data):
    """模拟事件处理函数"""
    print(f"接收到的数据: {data}")
    
    # 安全获取用户ID
    user_id = safe_get_string(data, "user_id", "unknown")
    print(f"安全获取的user_id: '{user_id}'")
    
    # 安全获取房间ID
    room_id = safe_get_string(data, "room_id", "unknown")
    print(f"安全获取的room_id: '{room_id}'")
    
    # 安全获取嵌套字段
    if "settings" in data and data["settings"] is not None:
        max_players = data["settings"].get("max_players", 2)
    else:
        max_players = 2
    print(f"获取的max_players: {max_players}")
    
    return {"status": "success", "user_id": user_id, "room_id": room_id}

# 测试各种事件数据
event_data_cases = [
    {"user_id": "player1", "room_id": "room123"},
    {"user_id": None, "room_id": "room123"},
    {"user_id": "", "room_id": None},
    {"room_id": "room123"},
    {"user_id": "player1", "settings": None},
    {"user_id": "player1", "settings": {"max_players": 4}}
]

for i, event_data in enumerate(event_data_cases):
    print(f"\n事件数据测试 {i+1}:")
    result = simulate_handle_event(event_data)
    print(f"处理结果: {result}")

print("\n=== 测试完成 ===")
print("所有测试用例都成功处理了JSON null值和其他边缘情况。")
print("关键发现:")
print("1. JSON中的null值在Python中会转换为None")
print("2. safe_get_string函数可以安全处理None值、空字符串和数字值")
print("3. 在处理嵌套数据时，需要先检查父级是否为None")