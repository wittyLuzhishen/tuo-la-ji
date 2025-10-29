/**
 * 枚举定义文件
 * 由枚举生成器自动生成，请勿手动修改
 */

// 客户端消息类型枚举
export const ClientMessageType = {
    Connect: 'connect',  // 连接消息
    Disconnect: 'disconnect',  // 断开连接消息
    ReconnectWithID: 'reconnect_with_id',  // 重新连接消息
    GetRoomList: 'get_room_list',  // 获取房间列表消息
    GetRoomDetails: 'get_room_details',  // 获取房间详情消息
    CreateRoom: 'create_room',  // 创建房间消息
    JoinRoom: 'join_room',  // 加入房间消息
    LeaveRoom: 'leave_room',  // 离开房间消息
    SitDown: 'sit_down',  // 坐下消息
    StandUp: 'stand_up',  // 站起消息
    Ready: 'ready',  // 准备消息
    UpdateRoomSettings: 'update_room_settings',  // 更新房间设置消息
    KickPlayer: 'kick_player',  // 踢出玩家消息
    ContinueGame: 'continue_game',  // 继续游戏消息
    SetUserInfo: 'set_userinfo',  // 设置用户信息消息
    SetAvatar: 'set_avatar',  // 设置玩家头像消息
    LookAtCards: 'look_at_cards',  // 查看牌面消息
    Fold: 'fold',  // 弃牌消息
    Call: 'call',  // 调用消息
    Raise: 'raise',  // 加注消息
    Showdown: 'showdown',  // 开牌消息
};
// 导出枚举
try {
    module.exports = module.exports || {};
    module.exports.ClientMessageType = ClientMessageType;
} catch (e) {
    // 浏览器环境，挂载到window对象
    window.ClientMessageType = ClientMessageType;
}

// 客户端传来的数据键枚举
export const ClientDataKey = {
    RoomID: 'room_id',  // 房间ID，类型：str
    RoomName: 'room_name',  // 房间名称，类型：str
    Ready: 'ready',  // 准备状态，类型：bool
    Settings: 'settings',  // 游戏设置，类型：dict
    UserID: 'user_id',  // 玩家ID，类型：str
    AddAmount: 'add_amount',  // 加注金额，类型：int
    ContinueGame: 'continue_game',  // 继续游戏选择，类型：bool
    AvatarURL: 'avatar_url',  // 玩家头像URL，类型：str
    Username: 'username',  // 玩家用户名，类型：str
    SeatIndex: 'seat_index',  // 玩家座位索引，类型：int
    PlayerIdToBeKicked: 'player_id_to_be_kicked',  // 被踢出玩家ID，类型：str
    PlayerIdToBeShowdown: 'player_id_to_be_showdown',  // 被开牌玩家ID，类型：str
};
// 导出枚举
try {
    module.exports = module.exports || {};
    module.exports.ClientDataKey = ClientDataKey;
} catch (e) {
    // 浏览器环境，挂载到window对象
    window.ClientDataKey = ClientDataKey;
}

// 服务器消息类型枚举
export const ServerMessageType = {
    Connected: 'connected',  // 连接/重连成功消息
    UserIDAssigned: 'user_id_assigned',  // 用户ID分配消息
    LostConnection: 'lost_connection',  // 玩家失去连接消息
    ReconnectRestore: 'reconnect_restore',  // 重新加入房间、载入房间信息消息
    StartTurn: 'start_turn',  // 开始回合消息
    GameInfo: 'game_info',  // 游戏信息消息
    RoomUpdatedWithPlayerBets: 'room_updated_with_player_bets',  // 房间更新玩家下注信息消息
    GameOver: 'game_over',  // 游戏结束消息
    UserInfoUpdated: 'user_info_updated',  // 用户信息更新消息
    Error: 'error',  // 错误消息
    RoomCreated: 'room_created',  // 房间创建消息
    RoomJoined: 'room_joined',  // 房间加入消息
    RoomLeft: 'room_left',  // 房间离开消息
    RoomList: 'room_list',  // 房间列表消息
    RoomDetails: 'room_details',  // 房间详情消息
    SettingsUpdated: 'settings_updated',  // 房间设置更新消息
    PlayerKicked: 'player_kicked',  // 玩家被踢出消息
    GameStarted: 'game_started',  // 游戏开始消息
    ShowCards: 'show_cards',  // 玩家看牌消息
    GameReset: 'game_reset',  // 游戏重置消息
    PlayerLeaved: 'player_leaved',  // 玩家离开消息
    RoomClosed: 'room_closed',  // 房间关闭消息
    PlayerFolded: 'player_folded',  // 玩家弃牌消息
    AvatarSet: 'avatar_set',  // 玩家设置头像消息
};
// 导出枚举
try {
    module.exports = module.exports || {};
    module.exports.ServerMessageType = ServerMessageType;
} catch (e) {
    // 浏览器环境，挂载到window对象
    window.ServerMessageType = ServerMessageType;
}

// 服务器消息键枚举
export const ServerDataKey = {
    UserID: 'user_id',  // 玩家ID，类型：str
    UserName: 'user_name',  // 用户名，类型：str
    ActivePlayersCount: 'active_players_count',  // 活动玩家数，类型：int
    RoomID: 'room_id',  // 房间ID，类型：str
    Room: 'room',  // 房间信息，类型：dict
    Players: 'players',  // 玩家信息列表，类型：list，每个元素为玩家信息字典，字典键为PlayerKey中的值
    Seats: 'seats',  // 座位信息列表，类型：list，每个元素为座位信息字典，字典键为PlayerKey中的值
    Owner: 'owner',  // 房主ID，类型：str，创建房间或有玩家离开时设置
    Settings: 'settings',  // 游戏设置，类型：dict
    GameStatus: 'game_status',  // 游戏状态，类型：str，值域：GameStatus，开始和结束游戏时设置
    LastWinner: 'last_winner',  // 上一局的赢家ID，用于确定下一局的庄家，类型：str，游戏结束时设置
    GameLog: 'game_log',  // 游戏日志，类型：list
    Status: 'status',  // 房间状态，类型：str，值域：RoomStatus
    Pot: 'pot',  // 奖池金额，类型：int
    CurrentTurnPlayerID: 'current_turn_player_id',  // 当前轮到行动的玩家ID，类型：str
    CurrentRound: 'current_round',  // 当前回合数，类型：int
    CurrentBet: 'current_bet',  // 当前加注金额，类型：int
    Winner: 'winner',  // 赢家ID，类型：str
    WinnerUsername: 'winner_username',  // 赢家用户名，类型：str
    Reason: 'reason',  // 游戏结束原因，类型：str
    Username: 'username',  // 玩家用户名，类型：str
    AvatarURL: 'avatar_url',  // 玩家头像URL，类型：str
    Message: 'message',  // 消息内容，类型：str
    RoomList: 'room_list',  // 房间列表消息，类型：list，每个元素为房间信息字典，字典键为RoomKey中的值
    Cards: 'cards',  // 玩家手牌，类型：list，每个元素为牌组中的牌元组（rank, suit）
    CallAmount: 'call_amount',  // 玩家加注金额，类型：int
    RaiseAmount: 'raise_amount',  // 玩家选择加注，之后付出的注数，类型：int
};
// 导出枚举
try {
    module.exports = module.exports || {};
    module.exports.ServerDataKey = ServerDataKey;
} catch (e) {
    // 浏览器环境，挂载到window对象
    window.ServerDataKey = ServerDataKey;
}

