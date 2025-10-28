
import random
from game_enum import GameStatus, PlayerStatus, RoomKey, PlayerKey, OnlineStatus, RoomSettingKey, RoomStatus

MAX_ROOM_COUNT = 100
ROOM_ID_LENGHT = 4 # 房间号长度为4位数字，0000-9999
# 默认房间设置
DEFAULT_ROOM_SETTINGS = {
    RoomSettingKey.IsDiffentSuit235GreaterThanThreeOfAKind.value: True,
    RoomSettingKey.IsA23AsStraight.value: True,
    RoomSettingKey.InitialCoins.value: 1000,
    RoomSettingKey.BaseBet.value: 2,
    RoomSettingKey.MaxBet.value: 100,
    RoomSettingKey.MaxRounds.value: 10,
    RoomSettingKey.MaxPotAmount.value: 1500,
    RoomSettingKey.MaxPlayerNumber.value: 6,
}
# 存储服务器上所有房间信息的变量
rooms = {}
# 重连计时器，键是玩家ID，值是计时器引用
reconnect_timer = {}

def get_room_by_player_id(player_id):
    """
    根据玩家ID查找所在房间
    返回房间ID，如果玩家不在任何房间则返回None
    """
    for room_id, room in rooms.items():
        for player in room[RoomKey.Players.value]:
            if player[PlayerKey.ID.value] == player_id:
                return room_id
    return None


def update_player_online_status(room_id, player_id, online_status:OnlineStatus):
    """
    更新玩家在线状态
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        print(f"玩家{player_id}不在房间{room_id}中")
        return False
        
    player[PlayerKey.OnlineStatus.value] = online_status.value
    return True


def update_player_status(room_id:str, player_id:str, player_status:PlayerStatus):
    """
    更新玩家状态
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        print(f"玩家{player_id}不在房间{room_id}中")
        return False
        
    player[PlayerKey.Status.value] = player_status.value
    return True


def find_player_in_room(room_id:str, player_id:str)->tuple:
    """
    在房间中查找玩家，返回玩家对象和在Players数组中的索引，对返回玩家信息的修改会影响全局数据。
    如果找不到玩家，返回 (None, None)
    """
    if room_id not in rooms:
        return None, None
        
    for i, player in enumerate(rooms[room_id][RoomKey.Players.value]):
        if player[PlayerKey.ID.value] == player_id:
            return player, i
    return None, None


def get_player_info(room_id, player_id, contain_cards=False)->dict:
    """
    获取玩家信息的副本，
    如果contain_cards为True，则包括手牌
    """
    player, _ = find_player_in_room(room_id, player_id)
    if not player:
        return None
    
    player_copy = player.copy()
    if not contain_cards:
        del player_copy[PlayerKey.Cards.value]
    return player_copy


def get_room_list():
    """
    获取房间列表，返回房间信息列表
    每个房间信息包括房间ID、房间名、玩家数量、最大玩家数、房间状态
    """
    room_list = []
    for room_id, room in rooms.items():
        # 获取房主信息
        owner_info = get_player_info(room_id, room[RoomKey.Owner.value])
        
        room_info = {
            RoomKey.ID.value: room_id,
            RoomKey.Name.value: room[RoomKey.Name.value],
            RoomKey.Owner.value: owner_info[RoomKey.Owner.value],
            RoomKey.Settings.value: room[RoomKey.Settings.value],
            RoomKey.GameStatus.value: room[RoomKey.GameStatus.value],
            RoomKey.Status.value: room[RoomKey.Status.value],
            RoomKey.PlayerCount.value: len(room[RoomKey.Players.value]),
        }
        room_list.append(room_info)
    return room_list


def create_room(player_id:str, username:str, room_name:str=None)->str:
    """
    玩家创建新房间，初始化房间状态，
    返回房间ID（4位数字），如果没有可用的房间号则返回None
    """
    # 生成数字房间号
    # 尝试最多100次生成不重复的房间号
    max_attempts = MAX_ROOM_COUNT // 2
    
    # 检查是否还有可用的4位数字房间号
    if len(rooms) >= MAX_ROOM_COUNT:
        print("已达到最大房间数")
        return None
    
    room_id = None
    for _ in range(max_attempts):
        # 生成0000-9999之间的随机数
        candidate_id = str(random.randint(0, 10**ROOM_ID_LENGHT - 1)).zfill(ROOM_ID_LENGHT)
        # 检查是否已存在
        if candidate_id not in rooms:
            room_id = candidate_id
            break
    
    # 如果无法找到可用的房间号，返回None
    if room_id is None:
        return None
    
    # 创建新玩家
    new_player = {
        PlayerKey.ID.value: player_id,
        PlayerKey.Coins.value: DEFAULT_ROOM_SETTINGS[RoomSettingKey.InitialCoins.value], # 根据房间设置设置
        PlayerKey.Status.value: PlayerStatus.Spectator.value, # 根据房间设置设置
        PlayerKey.OnlineStatus.value: True,
        PlayerKey.CurrentBet.value: 0,
        # 与牌相关的三个状态变量，等发牌的时候设置
    }
    
    # 创建新房间
    rooms[room_id] = {
        RoomKey.Name.value: room_name or f"{username}的房间",  # 房间名称
        RoomKey.Players.value: [new_player],  # 使用列表存储玩家，保持顺序
        RoomKey.Seats.value: [None] * DEFAULT_ROOM_SETTINGS[RoomSettingKey.MaxPlayerNumber.value],  # 座位信息，根据房间设置设置
        RoomKey.Owner.value: player_id,  # 创建房间的人成为该房间的首任房主
        RoomKey.Settings.value: DEFAULT_ROOM_SETTINGS.copy(),  # 游戏设置
        RoomKey.GameStatus.value: GameStatus.Wating.value,  # 游戏状态
        RoomKey.LastWinner.value: None,  # 上一局的赢家ID，用于确定下一局的庄家
        RoomKey.GameLog.value: [],  # 游戏日志
        RoomKey.Status.value: RoomStatus.Normal.value,  # 房间状态
        RoomKey.Pot.value: 0,  # 当前游戏的总金额
        RoomKey.CurrentRound.value: 1,  # 当前游戏的轮数
        RoomKey.CurrentBet.value: DEFAULT_ROOM_SETTINGS[RoomSettingKey.BaseBet.value],  # 当前游戏的下注金额
    }
    
    return room_id


def get_room_info(room_id, contain_cards_user_id:str=None):
    """
    获取游戏信息，
    如果指定了contain_cards_user_id，则返回的该玩家的游戏信息中包括手牌。
    否则返回所有玩家的游戏信息，不包括手牌。
    """
    if room_id not in rooms:
        return None
    room = rooms[room_id].copy()
    room[RoomKey.ID.value] = room_id
    
    for player in room[RoomKey.Players.value]:
        if player[PlayerKey.ID.value] != contain_cards_user_id:
            player.pop(PlayerKey.Cards.value, None)
    
    return room


def join_room(room_id:str, player_id:str, username:str, avatar:str):
    """
    玩家新加入房间
    如果is_reconnect为True，则表示玩家断线重连，不更新在线状态
    否则表示玩家新加入房间，更新在线状态为Online
    """
    if room_id not in rooms:
        return False
    
    player = {
        PlayerKey.ID.value: player_id,
        #PlayerKey.Username.value: username,
        #PlayerKey.Avatar.value: avatar,
        PlayerKey.Coins.value: rooms[room_id][RoomKey.Settings.value][RoomSettingKey.InitialCoins.value],
        PlayerKey.Status.value: PlayerStatus.Spectator.value,
        PlayerKey.OnlineStatus.value: OnlineStatus.Online.value,
        PlayerKey.Cards.value: [],
        PlayerKey.HasLookedAtCards.value: False,
        #PlayerKey.Folded.value: False,
    }
    
    if rooms[room_id][RoomKey.Players.value] in None:
        rooms[room_id][RoomKey.Players.value] = []
    rooms[room_id][RoomKey.Players.value].append(player)
    print(f"玩家{player_id}数据已写入房间{room_id}")
    return True


def leave_room(room_id, player_id):
    """移除玩家在房间中的数据"""
    if room_id not in rooms:
        return False
        
    player, index = find_player_in_room(room_id, player_id)
    if not player:
        return False
    room = rooms[room_id]
    del room[RoomKey.Players.value][index]
    if player_id in room[RoomKey.Seats.value]:
        index = room[RoomKey.Seats.value].index(player_id)
        room[RoomKey.Seats.value][index] = None
    if room[RoomKey.Owner.value] == player_id:
        room[RoomKey.Owner.value] = room[RoomKey.Players.value][0][PlayerKey.ID.value]
    if room[RoomKey.LastWinner.value] == player_id:
        room[RoomKey.LastWinner.value] = None
    
    
    print(f"玩家{player_id}数据已从房间{room_id}中移除")
    return True


def is_game_started(room_id):
    """
    检查游戏是否已开始
    """
    if room_id not in rooms:
        return False
    return rooms[room_id][RoomKey.GameStatus.value] == GameStatus.Playing.value


def is_player_turn(room_id, player_id):
    """
    检查是否是玩家的回合
    """
    if room_id not in rooms:
        return False
        
    current_player_id = rooms[room_id][RoomKey.CurrentTurnPlayerID.value]
    if current_player_id is None:
        return False
        
    # 直接比较玩家ID
    return current_player_id == player_id


def seat_player(room_id:str, player:dict, new_seat_index:int=-1):
    """
    为玩家分配座位。如果new_seat_index小于0，则让玩家起立。会修改player中的状态。
    """
    if room_id not in rooms:
        return False
    
    seats = rooms[room_id][RoomKey.Seats.value]
    if new_seat_index >= len(seats):
        return False
    
    # 查看玩家是否已在座位上
    for seat_index, seated_player_id in enumerate(seats):
        if seated_player_id != player[PlayerKey.ID.value]:
            continue
        # 玩家已坐在某个座位上
        if seat_index == new_seat_index:# 玩家现在坐的位置和想要坐的位置一样
            # 玩家已在指定座位上
            print(f"玩家{player}已在座位{new_seat_index}上")
            return True
        else:# 玩家现在坐的位置和想要坐的位置不一样
            seats[seat_index] = None # 从原座位上离开
            if new_seat_index < 0:
                # 玩家要站起来
                print(f"玩家{player}要站起来")
                # 更新玩家状态
                player[PlayerKey.Status.value] = PlayerStatus.Spectator.value
                return True
            
            print(f"玩家{player}要坐到座位{new_seat_index}上，当前位置为{seat_index}")
            break
            
    seats[new_seat_index] = player[PlayerKey.ID.value]
    # 更新玩家状态
    player[PlayerKey.Status.value] = PlayerStatus.Seated.value
    return True


def is_room_owner(room_id, player_id):
    """
    检查玩家是否是房主
    """
    if room_id not in rooms:
        return False
        
    return rooms[room_id][RoomKey.Owner.value] == player_id


def update_room_settings(room_id, settings:dict)->tuple:
    """
    更新房间设置。
    返回是否成功更新，以及信息。
    """
    if room_id not in rooms:
        return False, f"房间{room_id}不存在"
        
    # 验证设置
    isDiffentSuit235GreaterThanThreeOfKing = settings.get(RoomSettingKey.IsDiffentSuit235GreaterThanThreeOfAKind.value, None)
    isA23AsStraight = settings.get(RoomSettingKey.IsA23AsStraight.value, None)
    initialCoins = settings.get(RoomSettingKey.InitialCoins.value, 0)
    baseBet = settings.get(RoomSettingKey.BaseBet.value, 0)
    maxBet = settings.get(RoomSettingKey.MaxBet.value, 0)
    maxHands = settings.get(RoomSettingKey.MaxRounds.value, 0)
    maxPotAmount = settings.get(RoomSettingKey.MaxPotAmount.value, 0)
    maxPlayers = settings.get(RoomSettingKey.MaxPlayerNumber.value, 0)
    if isDiffentSuit235GreaterThanThreeOfKing is None or isA23AsStraight is None:
        return False, "缺少必要的房间设置"
    if initialCoins < 0 or baseBet < 0 or maxBet < 0 or maxHands < 0 or maxPotAmount < 0 or maxPlayers < 2:
        return False, "房间设置值异常"
    if initialCoins < baseBet or baseBet < maxBet or maxHands < 1 \
        or maxPotAmount < baseBet * maxPlayers \
        or maxPlayers > DEFAULT_ROOM_SETTINGS[RoomSettingKey.MaxPlayerNumber.value]:
        return False, "房间设置值逻辑关系异常"
    
    room = rooms[room_id]
    # 如果最大玩家数改变了 并且 已经有玩家坐下，则不能改变最大玩家数
    if room[RoomKey.Settings.value][RoomSettingKey.MaxPlayerNumber] != maxPlayers \
        and len(room[RoomKey.Seats.value]) != 0:
        return False, "已经有玩家坐下，无法更改房间最大玩家数"

    _update_room_setting(room_id, settings)
    _update_players_by_room_setting(room_id, settings)

    return True, "房间设置更新成功"


def _update_room_setting(room_id:str, setting:dict):
    """
    根据房间设置更新房间状态
    """
    if room_id not in rooms:
        raise Exception(f"房间{room_id}不存在")
    
    room = rooms[room_id]

    # 更新设置
    for key in DEFAULT_ROOM_SETTINGS.keys():
        if key in settings:
            room[RoomKey.Settings.value][key] = settings[key]
        else:
            room[RoomKey.Settings.value][key] = DEFAULT_ROOM_SETTINGS[key]

    room[RoomKey.Seats.value] = setting[RoomSettingKey.MaxPlayerNumber.value] * [None]
    return True


def _update_players_by_room_setting(room_id:str, setting:dict):
    """
    根据房间设置更新房间玩家信息
    """
    if room_id not in rooms:
        raise Exception(f"房间{room_id}不存在")
    
    players = rooms[room_id][RoomKey.Players.value]

    for player in players:
        player[PlayerKey.Coins.value] = setting[RoomSettingKey.InitialCoins.value]
        # 已经准备就绪的玩家会因为房间设置的改变而取消准备状态
        if player[PlayerKey.Status.value] == PlayerStatus.Ready.value:
            player[PlayerKey.Status.value] = PlayerStatus.Seated.value
        else:
            print(f"修改房间设置时，玩家{player[PlayerKey.ID.value]}的状态为{player[PlayerKey.Status.value]}，不会因为房间设置的改变而取消准备状态")
    return True


def reset_room_when_game_end(room_id:str):
    """
    当一局游戏结束时，重置房间状态
    """
    if room_id not in rooms:
        return False
    room = rooms[room_id]
    room[RoomKey.CurrentTurnPlayerID.value] = None # 待开局时确定
    room[RoomKey.GameStatus.value] = GameStatus.Wating.value
    #room[RoomKey.Pot.value] = 0
    #room[RoomKey.CurrentRound.value] = 1
    #room[RoomKey.CurrentBet.value] = room[RoomKey.Settings.value][RoomSettingKey.BaseBet.value]
    # 重置所有玩家的状态
    for player in room[RoomKey.Players.value]:
        player[PlayerKey.Status.value] = PlayerStatus.Seated.value
        #player[PlayerKey.CurrentBet.value] = 0
        #player[PlayerKey.Cards.value] = None
        #player[PlayerKey.HasLookedAtCards.value] = False
    return True


def reset_room_for_new_game(room_id:str, continue_players:list, seats:list)->bool:
    """
    当所有玩家都同意继续游戏时，
    重置房间状态到初始状态，
    保留玩家信息和房间设置，但重置游戏相关状态
    """
    if room_id not in rooms:
        return False
    room = rooms[room_id]
    room[RoomKey.Players.value] = continue_players
    room[RoomKey.Owner.value] = room[RoomKey.Players.value][0][PlayerKey.ID.value]
    # 提取所有玩家ID到列表中
    player_ids = [player[PlayerKey.ID.value] for player in room[RoomKey.Players.value]]
    if not room[RoomKey.LastWinner.value] or room[RoomKey.LastWinner.value] not in player_ids:
         # 开始游戏时，last_winner_id为为庄家，如果last_winner_id为None，则将随机选择庄家
        room[RoomKey.LastWinner.value] = player_ids[random.randint(0, len(player_ids)-1)]
    room[RoomKey.Seats.value] = seats if seats else [None] * len(room[RoomKey.Players.value])
    room[RoomKey.GameLog.value] = []
    room[RoomKey.Pot.value] = 0
    room[RoomKey.CurrentTurnPlayerID.value] = None
    room[RoomKey.CurrentRound.value] = 1
    room[RoomKey.CurrentBet.value] = room[RoomKey.Settings.value][RoomSettingKey.BaseBet.value]
    
    # 重置所有玩家的状态
    for player in room[RoomKey.Players.value]:
        #player[PlayerKey.Folded.value] = False
        player[PlayerKey.Cards.value] = None
        player[PlayerKey.HasLookedAtCards.value] = False
        player[PlayerKey.CurrentBet.value] = 0
    # 这句代码是开关，当游戏主循环中检测到所有玩家都准备就绪后，游戏将开始，状态设置会被设置为Playing
    room[RoomKey.GameStatus.value] = GameStatus.AllReady.value
    return True


def clean_unready_players_from_seats(room_id:str):
    """
    将房间中未准备就绪的玩家移除座位，即将进行下一场游戏。
    """
    if room_id not in rooms:
        return False
    room = rooms[room_id]
    all_players = room[RoomKey.Players.value]
    for p in all_players:
        if p[PlayerKey.Status.value] != PlayerStatus.Ready.value:
            seat_index = room[RoomKey.Seats.value].index(p[PlayerKey.ID.value])
            room[RoomKey.Seats.value][seat_index] = None
    
    return True


def get_playing_players(players:list[dict])->list[dict]:
    """
    获取所有正在游戏中的玩家。返回的是玩家的引用，修改返回的列表会影响到原始玩家列表。
    """
    return [player for player in players if player[PlayerKey.Status.value] == PlayerStatus.Playing.value]

