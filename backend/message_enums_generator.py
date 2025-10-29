#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
枚举生成器脚本
用于统一生成服务器端的Python枚举和客户端的JavaScript枚举，确保消息类型和数据键的一致性。
"""

import os
import json
from typing import List, Dict, Tuple, Any

# 枚举定义数据
ENUMS_DATA = {
    "ClientMessageType": {
        "description": "客户端消息类型枚举",
        "values": [
            ("Connect", "connect", "连接消息"),
            ("Disconnect", "disconnect", "断开连接消息"),
            ("ReconnectWithID", "reconnect_with_id", "重新连接消息"),
            ("GetRoomList", "get_room_list", "获取房间列表消息"),
            ("GetRoomDetails", "get_room_details", "获取房间详情消息"),
            ("CreateRoom", "create_room", "创建房间消息"),
            ("JoinRoom", "join_room", "加入房间消息"),
            ("LeaveRoom", "leave_room", "离开房间消息"),
            ("SitDown", "sit_down", "坐下消息"),
            ("StandUp", "stand_up", "站起消息"),
            ("Ready", "ready", "准备消息"),
            ("UpdateRoomSettings", "update_room_settings", "更新房间设置消息"),
            ("KickPlayer", "kick_player", "踢出玩家消息"),
            ("ContinueGame", "continue_game", "继续游戏消息"),
            ("SetUserInfo", "set_userinfo", "设置用户信息消息"),
            ("SetAvatar", "set_avatar", "设置玩家头像消息"),
            ("LookAtCards", "look_at_cards", "查看牌面消息"),
            ("Fold", "fold", "弃牌消息"),
            ("Call", "call", "调用消息"),
            ("Raise", "raise", "加注消息"),
            ("Showdown", "showdown", "开牌消息"),
        ]
    },
    "ClientDataKey": {
        "description": "客户端传来的数据键枚举",
        "values": [
            ("RoomID", "room_id", "房间ID，类型：str"),
            ("RoomName", "room_name", "房间名称，类型：str"),
            ("Ready", "ready", "准备状态，类型：bool"),
            ("Settings", "settings", "游戏设置，类型：dict"),
            ("UserID", "user_id", "玩家ID，类型：str"),
            ("AddAmount", "add_amount", "加注金额，类型：int"),
            ("ContinueGame", "continue_game", "继续游戏选择，类型：bool"),
            ("AvatarURL", "avatar_url", "玩家头像URL，类型：str"),
            ("Username", "username", "玩家用户名，类型：str"),
            ("SeatIndex", "seat_index", "玩家座位索引，类型：int"),
            ("PlayerIdToBeKicked", "player_id_to_be_kicked", "被踢出玩家ID，类型：str"),
            ("PlayerIdToBeShowdown", "player_id_to_be_showdown", "被开牌玩家ID，类型：str"),
        ]
    },
    "ServerMessageType": {
        "description": "服务器消息类型枚举",
        "values": [
            ("Connected", "connected", "连接/重连成功消息"),
            ("UserIDAssigned", "user_id_assigned", "用户ID分配消息"),
            ("LostConnection", "lost_connection", "玩家失去连接消息"),
            ("ReconnectRestore", "reconnect_restore", "重新加入房间、载入房间信息消息"),
            ("StartTurn", "start_turn", "开始回合消息"),
            ("GameInfo", "game_info", "游戏信息消息"),
            ("RoomUpdatedWithPlayerBets", "room_updated_with_player_bets", "房间更新玩家下注信息消息"),
            ("GameOver", "game_over", "游戏结束消息"),
            ("UserInfoUpdated", "user_info_updated", "用户信息更新消息"),
            ("Error", "error", "错误消息"),
            ("RoomCreated", "room_created", "房间创建消息"),
            ("RoomJoined", "room_joined", "房间加入消息"),
            ("RoomLeft", "room_left", "房间离开消息"),
            ("RoomList", "room_list", "房间列表消息"),
            ("RoomDetails", "room_details", "房间详情消息"),
            ("SettingsUpdated", "settings_updated", "房间设置更新消息"),
            ("PlayerKicked", "player_kicked", "玩家被踢出消息"),
            ("GameStarted", "game_started", "游戏开始消息"),
            ("ShowCards", "show_cards", "玩家看牌消息"),
            ("GameReset", "game_reset", "游戏重置消息"),
            ("PlayerLeaved", "player_leaved", "玩家离开消息"),
            ("RoomClosed", "room_closed", "房间关闭消息"),
            ("PlayerFolded", "player_folded", "玩家弃牌消息"),
            ("AvatarSet", "avatar_set", "玩家设置头像消息"),
        ]
    },
    "ServerDataKey": {
        "description": "服务器消息键枚举",
        "values": [
            ("UserID", "user_id", "玩家ID，类型：str"),
            ("UserName", "user_name", "用户名，类型：str"),
            ("ActivePlayersCount", "active_players_count", "活动玩家数，类型：int"),
            ("RoomID", "room_id", "房间ID，类型：str"),
            ("Room", "room", "房间信息，类型：dict"),
            ("Players", "players", "玩家信息列表，类型：list，每个元素为玩家信息字典，字典键为PlayerKey中的值"),
            ("Seats", "seats", "座位信息列表，类型：list，每个元素为座位信息字典，字典键为PlayerKey中的值"),
            ("Owner", "owner", "房主ID，类型：str，创建房间或有玩家离开时设置"),
            ("Settings", "settings", "游戏设置，类型：dict"),
            ("GameStatus", "game_status", "游戏状态，类型：str，值域：GameStatus，开始和结束游戏时设置"),
            ("LastWinner", "last_winner", "上一局的赢家ID，用于确定下一局的庄家，类型：str，游戏结束时设置"),
            ("GameLog", "game_log", "游戏日志，类型：list"),
            ("Status", "status", "房间状态，类型：str，值域：RoomStatus"),
            ("Pot", "pot", "奖池金额，类型：int"),
            ("CurrentTurnPlayerID", "current_turn_player_id", "当前轮到行动的玩家ID，类型：str"),
            ("CurrentRound", "current_round", "当前回合数，类型：int"),
            ("CurrentBet", "current_bet", "当前加注金额，类型：int"),
            ("Winner", "winner", "赢家ID，类型：str"),
            ("WinnerUsername", "winner_username", "赢家用户名，类型：str"),
            ("Reason", "reason", "游戏结束原因，类型：str"),
            ("Username", "username", "玩家用户名，类型：str"),
            ("AvatarURL", "avatar_url", "玩家头像URL，类型：str"),
            ("Message", "message", "消息内容，类型：str"),
            ("RoomList", "room_list", "房间列表消息，类型：list，每个元素为房间信息字典，字典键为RoomKey中的值"),
            ("Cards", "cards", "玩家手牌，类型：list，每个元素为牌组中的牌元组（rank, suit）"),
            ("CallAmount", "call_amount", "玩家加注金额，类型：int"),
            ("RaiseAmount", "raise_amount", "玩家选择加注，之后付出的注数，类型：int"),
        ]
    },
    
}


def generate_python_enums(output_file: str) -> None:
    """
    生成Python枚举文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 枚举定义文件\n# 由枚举生成器自动生成，请勿手动修改\n\n")
        
        f.write("from enum import Enum\n\n\n")
        
        for enum_name, enum_data in ENUMS_DATA.items():
            # 写入枚举描述
            if enum_data.get('description'):
                f.write(f"class {enum_name}(Enum):\n")
                f.write(f"    \"\"\"{enum_data['description']}\"\"\"\n")
            else:
                f.write(f"class {enum_name}(Enum):\n")
            
            # 写入枚举值
            for value_tuple in enum_data['values']:
                if len(value_tuple) >= 3:
                    name, value, comment = value_tuple[:3]
                    f.write(f"    {name} = \"{value}\"  # {comment}\n")
                else:
                    name, value = value_tuple[:2]
                    f.write(f"    {name} = \"{value}\"\n")
            
            f.write("\n\n")
    
    print(f"Python枚举文件已生成: {output_file}")


def generate_javascript_enums(output_file: str) -> None:
    """
    生成JavaScript枚举文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入文件头部注释
        f.write("/**\n * 枚举定义文件\n * 由枚举生成器自动生成，请勿手动修改\n */\n\n")
        
        # 只生成客户端需要的枚举（消息类型和数据键）
        client_enums = ["ClientMessageType", "ClientDataKey", "ServerMessageType", "ServerDataKey"]
        
        for enum_name, enum_data in ENUMS_DATA.items():
            if enum_name not in client_enums:
                continue
                
            # 写入枚举描述
            if enum_data.get('description'):
                f.write(f"// {enum_data['description']}\n")
            
            # 生成JavaScript枚举对象（添加ES6 export关键字）
            f.write(f"export const {enum_name} = {{\n")
            
            # 写入枚举值
            for value_tuple in enum_data['values']:
                if len(value_tuple) >= 3:
                    name, value, comment = value_tuple[:3]
                    f.write(f"    {name}: '{value}',  // {comment}\n")
                else:
                    name, value = value_tuple[:2]
                    f.write(f"    {name}: '{value}',\n")
            
            f.write("};")
            
            # 添加导出语句（用于模块化）
            f.write("\n// 导出枚举\ntry {\n")
            f.write(f"    module.exports = module.exports || {{}};\n    module.exports.{enum_name} = {enum_name};\n")
            f.write("} catch (e) {\n")
            f.write("    // 浏览器环境，挂载到window对象\n")
            f.write(f"    window.{enum_name} = {enum_name};\n")
            f.write("}\n\n")

    
    print(f"JavaScript枚举文件已生成: {output_file}")


def generate_json_schema(output_file: str) -> None:
    """
    生成JSON格式的枚举定义，便于其他工具使用
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ENUMS_DATA, f, ensure_ascii=False, indent=2)
    
    print(f"JSON枚举定义文件已生成: {output_file}")


def main() -> None:
    """
    主函数
    """
    # 定义输出路径 - 当前已经在backend目录下
    backend_dir = os.path.dirname(__file__)  # 获取当前脚本所在目录
    static_js_dir = os.path.join(backend_dir, 'static', 'js')
    
    # 确保目录存在
    os.makedirs(static_js_dir, exist_ok=True)
    
    # 生成文件
    generate_python_enums(os.path.join(backend_dir, 'message_enums.py'))
    generate_javascript_enums(os.path.join(static_js_dir, 'message_enums.js'))
    #generate_json_schema(os.path.join(backend_dir, 'message_enums_schema.json'))
    
    print("\n所有枚举文件生成完成！")


if __name__ == "__main__":
    main()