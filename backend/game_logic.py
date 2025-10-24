# -*- coding: utf-8 -*-
"""
拖拉机纸牌游戏核心逻辑模块
包含牌型判断和牌型比较等功能
"""

from game_enum import RoomKey, RoomSettingKey

# 花色和牌面定义
SUITS = ["♥", "♦", "♠", "♣"]  # 扑克牌花色：红桃、方块、黑桃、梅花，红色>黑色，桃子大于方块或梅花
SUITS_ORDER = {"♥": 4, "♦": 3, "♠": 2, "♣": 1} # 花色顺序：红桃>方块>黑桃>梅花
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]  # 扑克牌面
# 牌面大小映射，用于排序和比较
RANK_ORDER = {rank: i+2 for i, rank in enumerate(RANKS)}  # 2->2, 3->3, ..., A->14


def is_straight_flush(hand, is_A23_as_straight=True):
    """
    判断是否为同花顺、清拖牌型
    条件：同时满足顺子和金花的条件
    返回：布尔值，表示是否为同花顺
    """
    # 判断是否为同花顺
    return is_straight(hand, is_A23_as_straight) and is_flush(hand)


def is_three_of_a_kind(hand):
    """
    判断是否为豹子牌型
    条件：三张牌的牌面数值完全相同
    返回：布尔值，表示是否为豹子
    """
    # 判断是否为豹子
    ranks = [card[0] for card in hand]
    return len(set(ranks)) == 1


def is_A23(hand):
    """
    判断是否为A23牌型
    条件：三张牌的牌面数值为A、2、3
    返回：布尔值，表示是否为A23
    """
    return set([card[0] for card in hand]) == {"A", "2", "3"}


def is_straight(hand, is_A23_as_straight=True):
    """
    判断是否为顺子、拖拉机牌型
    条件：三张牌的牌面数值连续
    特殊规则：
    - 235不视为顺子（视为特殊单牌）
    - A23肯能会被认为是最小的顺子
    返回：布尔值，表示是否为顺子
    """
    # 判断是否为顺子
    # 根据拖拉机游戏规则，顺子是三张连续的牌
    ranks = [card[0] for card in hand]

    rank_values = []

    for rank in ranks:
        rank_values.append(RANK_ORDER.get(rank))

    # 特殊情况：A23是最小的顺子
    if is_A23(hand):
        return is_A23_as_straight

    # 检查是否连续
    rank_values.sort()
    for i in range(2):
        if rank_values[i + 1] - rank_values[i] != 1:
            return False

    return True


def is_flush(hand):
    """
    判断是否为金花牌型，包含同花顺的情况
    条件：三张牌的花色完全相同
    返回：布尔值，表示是否为金花
    """
    suits = [card[1] for card in hand]
    return len(set(suits)) == 1


def is_pair(hand):
    """
    判断是否为对子牌型
    条件：三张牌中有两张牌面数值相同，另一张不同
    返回：布尔值，表示是否为对子
    """
    # 判断是否为对子
    ranks = [card[0] for card in hand]
    return len(set(ranks)) == 2

def is_235(hand):
    """
    判断是否为235牌型
    条件：三张牌的牌面数值为2、3、5
    返回：布尔值，表示是否为235
    """
    return set([card[0] for card in hand]) == {"2", "3", "5"}

def is_different_suits_235(hand):
    """
    判断是否为非同花235牌型
    条件：三张牌的花色不同，且牌面数值为2、3、5
    返回：布尔值，表示是否为非同花235
    """
    return is_235(hand) and not is_flush(hand)

def is_same_suit_235(hand):
    """
    判断是否为同花235牌型
    条件：三张牌的花色相同，且牌面数值为2、3、5
    返回：布尔值，表示是否为同花235
    """
    return is_235(hand) and is_flush(hand)

def is_same_suit_a23(hand):
    """
    判断是否为同花A23牌型
    条件：三张牌的花色相同，且牌面数值为A、2、3
    返回：布尔值，表示是否为同花A23
    """
    return is_A23(hand) and is_flush(hand)

def get_hand_level(hand, has_three_of_a_kind_in_any_hand=False, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True):
    """
    获取手牌的牌型等级
    牌型等级从低到高：
    1 - 单牌（包括非同花235）
    2 - 对子
    3 - 金花
    4 - 顺子
    5 - 同花顺
    6 - 豹子
    7 - 非同花235（当开启特殊规则时且手牌中有豹子时）

    返回：整数，表示牌型等级
    """
    # 检查手牌是否为空或数量不正确
    if not hand:
        raise ValueError("手牌不能为空")
    if len(hand) != 3:
        raise ValueError("手牌数量必须为3张")
    
    # 是否为非同花235
    if is_different_suits_235(hand):
        if has_three_of_a_kind_in_any_hand:
            return 7 if isDiffentSuit235GreaterThanThreeOfAKind else 1
        else:
            return 1
    if is_three_of_a_kind(hand):
        return 6  # 豹子
    elif is_straight_flush(hand, is_A23_as_straight):
        return 5  # 相同花色的顺子（同花顺）
    elif is_straight(hand, is_A23_as_straight):
        return 4  # 顺子、拖拉机
    elif is_flush(hand):
        return 3  # 相同花色的非顺子（金花）
    elif is_pair(hand):
        return 2  # 对子
    else:
        return 1  # 单牌（包括非同花235在未开启特殊规则时）


def get_sorted_hand(hand, is_A23_as_straight=True):
    """
    对手牌进行排序，按牌面数值和花色排序
    返回：排序后的手牌列表
    """
    # 检查手牌是否为空或数量不正确
    if not hand:
        raise ValueError("手牌不能为空")
    if len(hand) != 3:
        raise ValueError("手牌数量必须为3张")
    
    is_A_rank_1 = False
    if is_A23_as_straight and is_A23(hand):
        is_A_rank_1 = True

    def get_sort_key(num_suit_pair):
        card_num, suit = num_suit_pair
        rank_order = RANK_ORDER.copy()
        if is_A_rank_1:
            rank_order["A"] = 1
        # 转换为可比较的数字（如'Q'→12，'A'→14）
        real_num = rank_order.get(card_num)
        # 统计当前牌面在牌组中的出现次数（判断是否为对子）
        count = sum(1 for c in hand if c[0] == card_num)
        # 排序键：(是否对子, 数字大小, 花色大小)
        return (-1 if count == 2 else 0, -real_num, -SUITS_ORDER.get(suit))
    
    print(f"排序前：{hand}, is_A_rank_1={is_A_rank_1}")
    sorted_hand = sorted(hand, key=get_sort_key)
    print(f"排序后：{sorted_hand}, is_A_rank_1={is_A_rank_1}")
    return sorted_hand


def compare_same_level_hands(hand1, hand2, is_A23_as_straight=True):
    """
    比较两手牌相同牌型等级的情况
    返回：整数，表示两手牌的比较结果（1表示手1大于手2，-1表示手1小于手2，0表示两手牌相等）
    """
    
    # 牌型等级相同，按牌面数值和花色比较
    sorted_hand1 = get_sorted_hand(hand1, is_A23_as_straight)
    sorted_hand2 = get_sorted_hand(hand2, is_A23_as_straight)
    
    for i in range(len(sorted_hand1)):
        if sorted_hand1[i][0] != sorted_hand2[i][0]:
            # 此时如果存在手牌为32A的情况，也不需要把A的值换为1。
            # 因为如果另一手牌是比32A大的顺子，在比到第一位时就已经得到结果，轮不到最后一位的A；
            # 如果另一手牌也是32A，两手牌最后都是A，A的值无所谓了。
            return 1 if RANK_ORDER.get(sorted_hand1[i][0]) > RANK_ORDER.get(sorted_hand2[i][0]) else -1
        elif sorted_hand1[i][1] != sorted_hand2[i][1]:
            return 1 if SUITS_ORDER.get(sorted_hand1[i][1]) > SUITS_ORDER.get(sorted_hand2[i][1]) else -1
    
    return 0


def compare_two_hands(hand1, hand2, has_three_of_a_kind_in_any_hand, isDiffentSuit235GreaterThanThreeOfAKind, 
        is_A23_as_straight=True):

    level_hand1 = get_hand_level(hand1, 
        has_three_of_a_kind_in_any_hand=has_three_of_a_kind_in_any_hand, 
        isDiffentSuit235GreaterThanThreeOfAKind=isDiffentSuit235GreaterThanThreeOfAKind, 
        is_A23_as_straight=is_A23_as_straight)
    level_hand2 = get_hand_level(hand2, 
        has_three_of_a_kind_in_any_hand=has_three_of_a_kind_in_any_hand, 
        isDiffentSuit235GreaterThanThreeOfAKind=isDiffentSuit235GreaterThanThreeOfAKind, 
        is_A23_as_straight=is_A23_as_straight)
    
    # 添加调试信息
    print(f"手牌1: {hand1}, 等级: {level_hand1}")
    print(f"手牌2: {hand2}, 等级: {level_hand2}")
    
    if level_hand1 != level_hand2: # 如果等级不一样，按等级大小比较
        return level_hand1 - level_hand2
    else:# 如果等级一样，按牌型等级相同的规则比较
        return compare_same_level_hands(hand1, hand2, is_A23_as_straight=is_A23_as_straight)


def compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True):
    """
    比较多手牌的大小
    参数：至少需要两手牌作为参数

    特殊比较规则：
    - 235与豹子的比较可通过配置项控制
    - 235之间的比较按花色顺序（红桃 > 梅花 > 方块 > 黑桃）
    - 对于相同牌型，按牌面数值和花色进行比较

    返回：整数，表示最大手牌在参数中的索引位置
    """
    # 比较多个手牌的大小，至少需要2个参数
    if len(hands) < 2:
        raise ValueError("至少需要比较两手牌")

    # 检查所有手牌中是否存在豹子
    has_three_of_a_kind_in_any_hand = any(is_three_of_a_kind(hand) for hand in hands)

    # 如果只有两手牌，直接返回比较结果
    if len(hands) == 2:
        result = compare_two_hands(hands[0], hands[1], has_three_of_a_kind_in_any_hand, isDiffentSuit235GreaterThanThreeOfAKind, is_A23_as_straight)
        if result > 0:
            return 0
        elif result < 0:
            return 1
        else: # 两手牌相等，返回第一手牌的索引
            max_hand_index = None
            if raise_compare_hand_index == 0:
                max_hand_index = 1
            else:
                max_hand_index = 0
            print(f"两手牌相等：{hands[0]} 和 {hands[1]}, 发起比较的索引:{raise_compare_hand_index}, 判胜索引: {max_hand_index}")
            return max_hand_index
            

    # 处理多手牌比较的情况
    # 返回最大的手牌的索引
    max_hand_index = 0
    
    print(f"多手牌比较开始，共{len(hands)}手牌")
    for i in range(1, len(hands)):
        # 使用内部函数比较当前手牌与最大手牌，避免递归
        result = compare_two_hands(hands[i], hands[max_hand_index], has_three_of_a_kind_in_any_hand, 
            isDiffentSuit235GreaterThanThreeOfAKind, is_A23_as_straight)
        print(f"比较手牌{i} {hands[i]} 与当前最大手牌{max_hand_index} {hands[max_hand_index]}, 结果: {result}")
        if result > 0:
            max_hand_index = i
            print(f"更新最大手牌索引为: {max_hand_index}")
    # 返回最大的手牌索引
    print(f"最终最大手牌索引: {max_hand_index}, 手牌: {hands[max_hand_index]}")
    return max_hand_index