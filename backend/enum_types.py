from enum import Enum

class MessageType(Enum):
    """消息类型枚举"""
    RoomUpdated = "room_updated"
    UserNameError = "username_error"
    SettingsUpdated = "settings_updated"  # 游戏设置更新
    RoomSettings = "room_settings"  # 房间设置
    RoomSettingsError = "room_settings_error"  # 房间设置错误
    ContinueGameReady = "continue_game_ready"  # 已有足够玩家准备继续游戏
    GameEnded = "game_ended"  # 当一局结束后，没有足够的玩家选择继续，则游戏结束
    GameOver = "game_over"  # 游戏结束广播
    GameStart = "game_start"  # 游戏开始广播
    StartTurn = "start_turn"  # 开始新回合广播
    ShowCards = "show_cards"  # 显示玩家手牌广播
    PlayerLookedCards = "player_looked_cards"  # 玩家已看牌广播

class BroadcastDataKey(Enum):
    """广播数据键枚举"""
    Hand = "hand"  # 玩家手牌
    PlayerID = "player_id"  # 玩家ID
    PlayerName = "player_name"  # 玩家用户名

    Cards = "cards"  # 玩家手牌
    LookedCards = "looked_cards"  # 已看牌玩家列表

class RoomKey(Enum):
    """房间状态枚举"""
    Players = "players"  # 存储所有玩家
    MaxPlayers = "max_players"  # 房间最大人数
    ReadyPlayers = "ready_players"  # 准备就绪的玩家
    Owner = "owner"  # 房主
    Settings = "settings"  # 游戏设置
    GameState = "game_state"  # 游戏状态：waiting, ready, playing
    Seats = "seats"  # 座位信息
    LastSeatTime = "last_seat_time"  # 记录每个玩家最后一次坐下的时间
    LastWinner = "last_winner"  # 上一局的赢家ID，用于确定下一局的庄家
    GameData = "game_data"  # 游戏数据，存储当前游戏状态
    ContinueGameData = "continue_game_data"  # 继续游戏数据

class PlayerKey(Enum):
    """玩家数据键枚举"""
    ID = "id"  # 玩家ID
    Username = "username"  # 玩家用户名
    Coins = "coins"  # 玩家金币数
    Status = "status"  # 玩家状态：active, inactive
    Avatar = "avatar"  # 玩家头像URL

class GameStatus(Enum):
    """游戏状态枚举"""
    Waiting = "waiting"  # 等待玩家加入
    Ready = "ready"  # 等待玩家准备
    Playing = "playing"  # 游戏进行中

class PlayerStatus(Enum):
    """玩家状态枚举"""
    Spectator = "spectator"  # 观众状态
    Seated = "seated"  # 已坐下状态

    Playing = "playing"  # 正在游戏状态

class RoomSettingKey(Enum):
    """房间设置枚举"""
    Is235GreaterThanThreeOfAKind = "is_235_greater_than_three_of_a_kind"  # 235是否大于豹子
    InitialCoins = "initial_coins"  # 初始金币数
    BaseBet = "base_bet"  # 底注
    MaxBet = "max_bet"  # 单注封顶金币数
    MaxHands = "max_hands"  # 手数封顶数
    MaxPotAmount = "max_pot_amount"  # 当局底池最大数额

class GameState(Enum):
    """游戏状态枚举"""
    Waiting = "waiting"  # 等待玩家加入
    Ready = "ready"  # 等待玩家准备
    Playing = "playing"  # 游戏进行中

class GameDataKey(Enum):
    """游戏数据枚举"""
    PlayersInGame = "players_in_game"  # 本局参与游戏的玩家
    FoldedPlayers = "folded_players"  # 本局已弃牌的玩家
    PlayerBets = "player_bets"  # 本局玩家下注信息
    Pot = "pot"  # 本局底池金额
    Hands = "hands"  # 本局已玩手数
    CurrentBet = "current_bet"  # 当前下注金额
    CurrentTurn = "current_turn"  # 当前回合玩家索引
    LookedCards = "looked_cards"  # 记录已看牌的玩家

    SeatedPlayers = "seated_players"  # 本局已坐下的玩家
    Banker = "banker"  # 本局庄家ID
    BankerName = "banker_name"  # 本局庄家名称
    LookedCards = "looked_cards"  # 本局已看牌的玩家
    PlayerID = "player_id"  # 玩家ID
    PlayerName = "player_name"  # 玩家用户名
    ActivePlayersCount = "active_players_count"  # 本局还没有弃牌的玩家数
    

class ContinueGameDataKey(Enum):
    """继续游戏数据枚举"""
    PlayersContinue = "players_continue"  # 继续游戏的玩家
    PlayersQuit = "players_quit"  # 退出游戏的玩家

# data["seat_index"]
# data["player_id"]
class ClientDataKey(Enum):
    """客户端数据键枚举"""
    SeatIndex = "seat_index"  # 玩家座位索引
    PlayerID = "player_id"  # 玩家ID
    Username = PlayerKey.Username.value  # 玩家用户名
    Is235GreaterThanThreeOfAKind = RoomSettingKey.Is235GreaterThanThreeOfAKind.value  # 235是否大于豹子
    InitalCoins = RoomSettingKey.InitialCoins.value  # 初始金币数
    BaseBet = RoomSettingKey.BaseBet.value  # 底注
    MaxBet = RoomSettingKey.MaxBet.value  # 单注封顶金币数
    MaxHands = RoomSettingKey.MaxHands.value  # 手数封顶数
    MaxPotAmount = RoomSettingKey.MaxPotAmount.value  # 当局底池最大数额
    AvatarURL = "avatar_url"  # 玩家头像URL
    Continue = "continue"  # 是否继续游戏

