from enum import Enum

class RoomKey(Enum):
    """房间键枚举"""
    Players = "players"  # 存储所有进入房间的玩家，类型：list，每个元素为玩家信息字典，字典键为PlayerKey中的值
    ReadyPlayers = "ready_players"  # 存储准备就绪的玩家，类型：set，存储玩家ID
    Owner = "owner"  # 房主ID，类型：str
    Settings = "settings"  # 游戏设置，类型：dict
    GameStatus = "game_status"  # 游戏状态，类型：str，值域：GameStatus
    Seats = "seats"  # 座位信息，类型：list，每个元素类型为str，为玩家ID或None
    LastSeatTime = "last_seat_time"  # 记录每个玩家最后一次坐下的时间，类型：dict，键为玩家ID，值为时间戳
    LastWinner = "last_winner"  # 上一局的赢家ID，用于确定下一局的庄家，类型：str
    GameData = "game_data"  # 游戏数据，存储当前游戏状态，类型：dict
    ContinueGameData = "continue_game_data"  # 继续游戏数据，类型：dict
    GameLog = "game_log"  # 游戏日志，类型：list
    Status = "status"  # 房间状态，类型：str，值域：RoomStatus
    Pot = "pot"  # 奖池金额，类型：int
    CurrentTurnPlayerID = "current_turn_player_id"  # 当前轮到行动的玩家ID，类型：str
    CurrentRound = "current_round"  # 当前回合数，类型：int
    CurrentBet = "current_bet"  # 当前下注金额，类型：int


    Name = "name"  # 房间名称，类型：str
    ID = "id" # 房间ID，类型：str
    PlayerCount = "player_count" # 房间当前玩家数，类型：int
    MaxPlayerNumber = "max_player_number" # 房间最大玩家数，类型：int


class PlayerKey(Enum):
    """玩家键枚举，对应Room中的Players字典"""
    ID = "id"  # 玩家ID
    Username = "username"  # 玩家用户名
    Coins = "coins"  # 玩家金币数
    Status = "status"  # 玩家状态，类型：str，值域：PlayerStatus
    Avatar = "avatar"  # 玩家头像URL，类型：str
    IsOnline = "is_online"  # 玩家是否在线，类型：bool，玩家恢复连接后设为True
    Cards = "cards"  # 玩家当前手牌，类型：list，每个元素为牌组中的牌元组（rank, suit）
    HasLookedAtCards = "has_looked_at_cards"  # 玩家是否看过牌，类型：bool

    Folded = "folded"  # 玩家是否弃牌，类型：bool

class PlayerStatus(Enum):
    """玩家状态枚举"""
    Spectator = "spectator"  # 观众状态
    Seated = "seated"  # 已坐下状态
    Ready = "ready"  # 已准备状态
    Playing = "playing"  # 正在游戏状态

class RoomSettingKey(Enum):
    """房间设置键枚举"""
    Is235GreaterThanThreeOfAKind = "is_235_greater_than_three_of_a_kind"
    InitialCoins = "initial_coins"  # 初始金币数
    BaseBet = "base_bet"  # 底注
    MaxBet = "max_bet"  # 单注封顶金币数
    MaxHands = "max_hands"  # 手数封顶数
    MaxPotAmount = "max_pot_amount"  # 当局底池最大数额
    MaxPlayerNumber = "max_player_number"  # 房主设置的房间最大人数

class GameStatus(Enum):
    """游戏状态枚举"""
    Wating = "waiting" # 等待玩家准备
    Playing = "playing" # 游戏进行中

class RoomStatus(Enum):
    """房间状态枚举"""
    Normal = "normal"  # 正常状态
    WaitingToDestroy = "waiting_to_destroy"  # 因为所有的玩家都离线了，等待结束游戏，销毁房间


class SessionKey(Enum):
    """会话键枚举"""
    UserID = "user_id"  # 玩家用户ID
    Username = "username"  # 玩家用户名

class ClientDataKey(Enum):
    """客户端传来的数据键枚举"""
    RoomID = "room_id"  # 房间ID，类型：str
    Ready = "ready"  # 准备状态，类型：bool
    Settings = "settings"  # 游戏设置，类型：dict
    PlayerID = "player_id"  # 玩家ID，类型：str
    Amount = "amount"  # 加注金额，类型：int
    ContinueGame = "continue"  # 继续游戏选择，类型：bool
    AvatarURL = "avatar_url"  # 玩家头像URL，类型：str


class EmitMessageType(Enum):
    """消息类型枚举"""
    Connected = "connected"  # 连接消息
    StartTurn = "start_turn"  # 开始回合消息
    GameInfo = "game_info"  # 游戏信息消息
    RoomUpdatedWithPlayerBets = "room_updated_with_player_bets"  # 房间更新玩家下注信息消息
    GameOver = "game_over"  # 游戏结束消息

class EmitDataKey(Enum):
    """消息键枚举"""
    PlayerID = "player_id"  # 玩家ID，类型：str
    PlayerName = "player_name"  # 玩家用户名，类型：str
    ActivePlayersCount = "active_players_count"  # 活动玩家数，类型：int
    RoomID = "room_id"  # 房间ID，类型：str
    Players = "players"  # 玩家信息列表，类型：list，每个元素为玩家信息字典，字典键为PlayerKey中的值
    CurrentTurnPlayerID = "current_turn_player_id"  # 当前轮到行动的玩家ID，类型：str
    Status = "status"  # 房间状态，类型：str，值域：RoomStatus
    Pot = "pot"  # 奖池金额，类型：int
    CurrentBet = "current_bet"  # 当前加注金额，类型：int
    CurrentRound = "current_round"  # 当前回合数，类型：int
    GameLog = "game_log"  # 游戏日志，类型：list
    Settings = "settings"  # 游戏设置，类型：dict
    Winner = "winner"  # 赢家ID，类型：str
    WinnerUsername = "winner_username"  # 赢家用户名，类型：str
    Reason = "reason"  # 游戏结束原因，类型：str

