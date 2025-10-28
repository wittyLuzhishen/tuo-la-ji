from enum import Enum

class RoomKey(Enum):
    """房间键枚举"""
    Players = "players"  # 存储所有进入房间的玩家，类型：list，每个元素为玩家信息字典，字典键为PlayerKey中的值
    Seats = "seats"  # 座位信息，类型：list，每个元素类型为str，为玩家ID或None
    Owner = "owner"  # 房主ID，类型：str，创建房间或有玩家离开时设置
    Settings = "settings"  # 游戏设置，类型：dict
    GameStatus = "game_status"  # 游戏状态，类型：str，值域：GameStatus，开始和结束游戏时设置
    LastWinner = "last_winner"  # 上一局的赢家ID，用于确定下一局的庄家，类型：str，游戏结束时设置
    GameLog = "game_log"  # 游戏日志，类型：list
    Status = "status"  # 房间状态，类型：str，值域：RoomStatus，开始游戏和结束游戏时设置
    Pot = "pot"  # 奖池金额，类型：int
    CurrentTurnPlayerID = "current_turn_player_id"  # 当前轮到行动的玩家ID，类型：str
    CurrentRound = "current_round"  # 当前回合数，类型：int
    CurrentBet = "current_bet"  # 当前房间下注金额，类型：int
    ID = "id" # 房间ID，类型：str
    Name = "name"  # 房间名称，类型：str
    PlayerCount = "player_count" # 房间当前玩家数，类型：int

    #ReadyPlayers = "ready_players"  # 存储准备就绪的玩家，类型：set，存储玩家ID
    #LastSeatTime = "last_seat_time"  # 记录每个玩家最后一次坐下的时间，类型：dict，键为玩家ID，值为时间戳
    #GameData = "game_data"  # 游戏数据，存储当前游戏状态，类型：dict
    #ContinueGameData = "continue_game_data"  # 继续游戏数据，类型：dict


class PlayerKey(Enum):
    """玩家键枚举，对应Room中的Players字典"""
    ID = "id"  # 玩家ID
    #Username = "username"  # 玩家用户名
    #Avatar = "avatar"  # 玩家头像URL，类型：str
    Status = "status"  # 玩家状态，类型：str，值域：PlayerStatus
    OnlineStatus = "online_status"  # 玩家在线类型，类型：str，值域：OnlineStatus
    CurrentBet = "current_bet"  # 玩家当前累计下注金额，类型：int
    Coins = "coins"  # 玩家金币数，类型：int
    Cards = "cards"  # 玩家当前手牌，类型：list，每个元素为牌组中的牌元组（rank, suit）
    HasLookedAtCards = "has_looked_at_cards"  # 玩家是否看过牌，类型：bool
    #Folded = "folded"  # 玩家是否弃牌，类型：bool

class UserKey(Enum):
    """用户键枚举"""
    ID = "id"  # 用户ID
    Username = "username"  # 用户名
    AvatarURL = "avatar_url"  # 头像URL

class PlayerStatus(Enum):
    """玩家状态枚举"""
    Spectator = "spectator"  # 观众状态
    Seated = "seated"  # 已坐下状态
    Ready = "ready"  # 已准备状态
    Playing = "playing"  # 正在游戏状态
    Folded = "folded"  # 弃牌状态

class OnlineStatus(Enum):
    """玩家在线状态枚举"""
    Online = "online"  # 在线状态
    LostConnection = "lost_connection"  # 失去连接状态
    Offline = "offline"  # 离线状态，用于指示用户在游戏中主动断开连接的状态

class RoomSettingKey(Enum):
    """房间设置键枚举"""
    IsDiffentSuit235GreaterThanThreeOfAKind = "is_diffent_suit_235_greater_than_three_of_a_kind" # 是否不同花色235大于豹子（在存在豹子的情况下）
    IsA23AsStraight = "is_a23_as_straight"  # 是否将A23作为顺子
    InitialCoins = "initial_coins"  # 初始金币数
    BaseBet = "base_bet"  # 底注
    MaxBet = "max_bet"  # 单注封顶金币数
    MaxRounds = "max_rounds"  # 手数封顶数
    MaxPotAmount = "max_pot_amount"  # 当局底池最大数额
    MaxPlayerNumber = "max_player_number"  # 房主设置的房间最大人数

class GameStatus(Enum):
    """游戏状态枚举"""
    Wating = "waiting" # 等待玩家准备
    AllReady = "all_ready" # 所有玩家都已准备就绪，即将开始
    Playing = "playing" # 游戏进行中

class RoomStatus(Enum):
    """房间状态枚举"""
    Normal = "normal"  # 正常状态
    WaitingToDestroy = "waiting_to_destroy"  # 因为所有的玩家都离线了，等待结束游戏，销毁房间

class SessionKey(Enum):
    """会话键枚举"""
    #UserID = "user_id"  # 玩家用户ID
    #Username = "username"  # 玩家用户名

class ClientDataKey(Enum):
    """客户端传来的数据键枚举"""
    RoomID = "room_id"  # 房间ID，类型：str
    Ready = "ready"  # 准备状态，类型：bool
    Settings = "settings"  # 游戏设置，类型：dict
    PlayerID = "player_id"  # 玩家ID，类型：str
    AddAmount = "add_amount"  # 加注金额，类型：int
    ContinueGame = "continue"  # 继续游戏选择，类型：bool
    AvatarURL = "avatar_url"  # 玩家头像URL，类型：str
    Username = "username"  # 玩家用户名，类型：str
    SeatIndex = "seat_index"  # 玩家座位索引，类型：int
    PlayerIdToBeKicked = "player_id_to_be_kicked"  # 被踢出玩家ID，类型：str
    PlayerIdToBeShowdown = "player_id_to_be_showdown"  # 被开牌玩家ID，类型：str


class ServerMessageType(Enum):
    """服务器消息类型枚举"""
    Connected = "connected"  # 连接/重连成功消息
    LostConnection = "lost_connection"  # 玩家失去连接消息
    ReconnectRestore = "reconnect_restore"  # 重新加入房间、载入房间信息消息
    StartTurn = "start_turn"  # 开始回合消息
    GameInfo = "game_info"  # 游戏信息消息
    RoomUpdatedWithPlayerBets = "room_updated_with_player_bets"  # 房间更新玩家下注信息消息
    GameOver = "game_over"  # 游戏结束消息
    UserInfoUpdated = "user_info_updated"  # 用户信息更新消息
    Error = "error"  # 错误消息
    RoomCreated = "room_created"  # 房间创建消息
    RoomJoined = "room_joined"  # 房间加入消息
    RoomLeft = "room_left"  # 房间离开消息
    RoomList = "room_list"  # 房间列表消息
    RoomDetails = "room_details"  # 房间详情消息
    SettingsUpdated = "settings_updated"  # 房间设置更新消息
    PlayerKicked = "player_kicked"  # 玩家被踢出消息
    GameStarted = "game_started"  # 游戏开始消息
    ShowCards = "show_cards"  # 玩家看牌消息
    GameReset = "game_reset"  # 游戏重置消息
    PlayerLeaved = "player_leaved"  # 玩家离开消息
    RoomClosed = "room_closed"  # 房间关闭消息
    PlayerFolded = "player_folded"  # 玩家弃牌消息
    AvatarSet = "avatar_set"  # 玩家设置头像消息

class ServerDataKey(Enum):
    """服务器消息键枚举"""
    PlayerID = "player_id"  # 玩家ID，类型：str
    PlayerName = "player_name"  # 玩家用户名，类型：str
    ActivePlayersCount = "active_players_count"  # 活动玩家数，类型：int
    RoomID = "room_id"  # 房间ID，类型：str
    Room = "room" # 房间信息，类型：dict
    Players = "players"  # 玩家信息列表，类型：list，每个元素为玩家信息字典，字典键为PlayerKey中的值
    Seats = "seats"  # 座位信息列表，类型：list，每个元素为座位信息字典，字典键为PlayerKey中的值
    Owner = "owner"  # 房主ID，类型：str，创建房间或有玩家离开时设置
    Settings = "settings"  # 游戏设置，类型：dict
    GameStatus = "game_status"  # 游戏状态，类型：str，值域：GameStatus，开始和结束游戏时设置
    LastWinner = "last_winner"  # 上一局的赢家ID，用于确定下一局的庄家，类型：str，游戏结束时设置
    GameLog = "game_log"  # 游戏日志，类型：list
    Status = "status"  # 房间状态，类型：str，值域：RoomStatus
    Pot = "pot"  # 奖池金额，类型：int
    CurrentTurnPlayerID = "current_turn_player_id"  # 当前轮到行动的玩家ID，类型：str
    CurrentRound = "current_round"  # 当前回合数，类型：int
    CurrentBet = "current_bet"  # 当前加注金额，类型：int
    Winner = "winner"  # 赢家ID，类型：str
    WinnerUsername = "winner_username"  # 赢家用户名，类型：str
    Reason = "reason"  # 游戏结束原因，类型：str
    Username = "username"  # 玩家用户名，类型：str
    AvatarURL = "avatar_url"  # 玩家头像URL，类型：str
    Message = "message"  # 消息内容，类型：str
    RoomList = "room_list"  # 房间列表消息，类型：list，每个元素为房间信息字典，字典键为RoomKey中的值
    Cards = "cards"  # 玩家手牌，类型：list，每个元素为牌组中的牌元组（rank, suit）
    CallAmount = "call_amount"  # 玩家加注金额，类型：int
    RaiseAmount = "raise_amount"  # 玩家选择加注，之后付出的注数，类型：int