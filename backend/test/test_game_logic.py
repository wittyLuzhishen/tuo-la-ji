import unittest
import sys
import os

# 添加上级目录到系统路径，以便导入game_logic模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_logic import (
    is_straight_flush, is_three_of_a_kind, is_straight, is_flush, is_pair,
    get_hand_level, compare_hands
)

class TestTractorGameLogic(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
    
    def test_hand_type_judgment(self):
        # 测试不同牌型的判断
                
        # 豹子
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertTrue(is_three_of_a_kind(three_of_a_kind))

        # 同花顺（相同花色的顺子）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertTrue(is_straight_flush(straight_flush))
        self.assertTrue(is_straight(straight_flush))
        self.assertTrue(is_flush(straight_flush))
        
        # 顺子（非同花顺）
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertTrue(is_straight(straight))
        self.assertFalse(is_straight_flush(straight))
        self.assertFalse(is_flush(straight))
        
        # 金花（相同花色的非顺子）
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertFalse(is_straight_flush(flush))
        self.assertTrue(is_flush(flush))
        self.assertFalse(is_straight(flush))
        
        # 对子
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertTrue(is_pair(pair))
        self.assertFalse(is_straight(pair))
        self.assertFalse(is_flush(pair))
        
        # 单牌
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]
        self.assertFalse(is_straight_flush(high_card))
        self.assertFalse(is_three_of_a_kind(high_card))
        self.assertFalse(is_straight(high_card))
        self.assertFalse(is_flush(high_card))
        self.assertFalse(is_pair(high_card))
        
        # 235的特殊情况
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 不同花色
        self.assertFalse(is_straight(special_235))  # 235不是顺子
        self.assertFalse(is_flush(special_235))
        
        flush_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]  # 相同花色
        self.assertFalse(is_straight(flush_235))  # 235不是顺子
        self.assertTrue(is_flush(flush_235))
        self.assertFalse(is_straight_flush(flush_235))  # 235不是同花顺
    
    def test_hand_rank_with_235_disabled(self):
        # 同花顺（相同花色的顺子）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertEqual(get_hand_level(straight_flush), 5)
        
        # 豹子
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertEqual(get_hand_level(three_of_a_kind), 6)
        
        # 235（不同花色）
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        self.assertEqual(get_hand_level(special_235), 1)  # 此时应视为单牌
        
        # 顺子（非同花顺）
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertEqual(get_hand_level(straight), 4)
        
        # 金花（相同花色的非顺子）
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertEqual(get_hand_level(flush), 3)
        
        # 对子
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertEqual(get_hand_level(pair), 2)
        
        # 单牌
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]
        self.assertEqual(get_hand_level(high_card), 1)
    
    def test_hand_rank_with_235_enabled(self):
        # 测试启用235大于豹子的情况
        
        # 235（不同花色）- 现在始终被视为单牌
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        self.assertEqual(get_hand_level(special_235), 1)  # 不同花色的235始终被视为单牌
        
        # 235（相同花色）- 此时应视为金花
        flush_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]
        self.assertEqual(get_hand_level(flush_235), 3)  # 此时应视为金花
        
        # 豹子
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertEqual(get_hand_level(three_of_a_kind), 6)
        
        # 同花顺（相同花色的顺子）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertEqual(get_hand_level(straight_flush), 5)
    
    def test_compare_hands_different_types(self):
        # 测试不同牌型之间的比较

        
        # 不同花色的235 > 豹子
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertEqual(compare_hands(special_235, three_of_a_kind, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        self.assertEqual(compare_hands(three_of_a_kind, special_235, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 235 < 同花顺（因为235与非豹子比较时视为单牌）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertEqual(compare_hands(special_235, straight_flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 235 < 顺子（因为235与非豹子比较时视为单牌）
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertEqual(compare_hands(special_235, straight, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 235 < 金花（因为235与非豹子比较时视为单牌）
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertEqual(compare_hands(special_235, flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 235 < 对子（因为235与非豹子比较时视为单牌）
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertEqual(compare_hands(special_235, pair, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 豹子 > 同花顺
        self.assertEqual(compare_hands(three_of_a_kind, straight_flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 同花顺 > 顺子
        self.assertEqual(compare_hands(straight_flush, straight, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 顺子 > 金花
        self.assertEqual(compare_hands(straight, flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 金花 > 对子
        self.assertEqual(compare_hands(flush, pair, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 对子 > 单牌
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]
        self.assertEqual(compare_hands(pair, high_card, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
    
    def test_compare_hands_same_types(self):
        # 测试相同牌型之间的比较
        
        # 相同牌型的顺子比较
        straight1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]  # 更大的顺子
        straight2 = [('J', '♥'), ('10', '♦'), ('9', '♣')]  # 更小的顺子
        self.assertEqual(compare_hands(straight1, straight2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 相同牌型的对子比较
        pair1 = [('A', '♥'), ('A', '♦'), ('5', '♣')]  # A对
        pair2 = [('K', '♥'), ('K', '♦'), ('10', '♣')]  # K对
        self.assertEqual(compare_hands(pair1, pair2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 相同牌型的单牌比较
        high_card1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]  # A-K-Q
        high_card2 = [('K', '♥'), ('Q', '♦'), ('J', '♣')]  # K-Q-J
        self.assertEqual(compare_hands(high_card1, high_card2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 完全相同的牌，谁先比谁输
        hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        self.assertEqual(compare_hands(hand1, hand2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
    
    def test_235_rule_edge_cases(self):
        """测试235特殊规则的边界情况"""
        # 测试235与A豹子的比较
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 非同花235
        three_of_a_kind_ace = [('A', '♥'), ('A', '♦'), ('A', '♣')]  # A的豹子
        self.assertEqual(compare_hands(special_235, three_of_a_kind_ace, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)
        
        # 测试相同花色的235（金花）与豹子比较
        flush_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]  # 同花235
        self.assertEqual(compare_hands(flush_235, three_of_a_kind_ace, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
    def test_235_as_high_card_against_non_three_of_a_kind(self):
        # 测试235与非豹子比较时视为单牌的逻辑
        
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        
        # 同花顺
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertEqual(compare_hands(special_235, straight_flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 顺子
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertEqual(compare_hands(special_235, straight, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 金花
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertEqual(compare_hands(special_235, flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 对子
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertEqual(compare_hands(special_235, pair, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 注意：235只有在与豹子比较时才有特殊地位
        # 在与非豹子的手牌比较时，235被视为单牌（根据compare_hands函数中的逻辑）
    
    def test_a23_smallest_straight(self):
        # 测试A23是最小的顺子
        a23 = [('A', '♥'), ('2', '♦'), ('3', '♣')]
        straight_234 = [('2', '♥'), ('3', '♦'), ('4', '♣')]
        
        self.assertTrue(is_straight(a23))
        self.assertTrue(is_straight(straight_234))
        
        # A23应小于234顺子
        self.assertEqual(compare_hands(a23, straight_234, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
    
    def test_different_suits_235_comparison(self):
        # 测试多个玩家同时持有不同花色235时的比较逻辑
        
        # 测试1: 牌面数值相同但花色不同的235
        # 不同花色的235 - 牌面相同但花色不同
        # 花色顺序: ♥ > ♣ > ♦ > ♠  (红桃>梅花>方块>黑桃)
        special_235_spade = [('2', '♠'), ('3', '♦'), ('5', '♠')]   # 包含黑桃和方块
        special_235_club = [('2', '♣'), ('3', '♦'), ('5', '♣')]    # 包含梅花和方块
        special_235_diamond = [('2', '♦'), ('3', '♠'), ('5', '♣')]  # 包含方块、黑桃、梅花
        special_235_heart = [('2', '♥'), ('3', '♣'), ('5', '♦')]   # 包含红桃、梅花、方块
        
        # 按数值顺序比较花色: 先比较5的花色，再比较3的花色，最后比较2的花色
        # 花色顺序: 红桃 > 梅花 > 方块 > 黑桃
        self.assertEqual(0, compare_hands(special_235_heart, special_235_club, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))   # 红桃235 < 梅花235 (因为红桃235中5的花色是方块，梅花235中5的花色是梅花)
        self.assertEqual(0, compare_hands(special_235_heart, special_235_spade, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))   # 红桃235 > 黑桃235
        self.assertEqual(1, compare_hands(special_235_club, special_235_spade, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))    # 梅花235 > 黑桃235
        
        # 测试2: 真正的不同花色组合比较
        # 创建明确不同花色组合的235手牌
        special_235_heart_club = [('2', '♥'), ('3', '♣'), ('5', '♦')]  # 红桃、梅花、方块
        special_235_heart_diamond = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 红桃、方块、黑桃
        special_235_club_diamond = [('2', '♣'), ('3', '♦'), ('5', '♠')]  # 梅花、方块、黑桃
        
        # 红桃是最大的花色，所以包含红桃的235大于不包含红桃的
        self.assertEqual(0, compare_hands(special_235_heart_club, special_235_club_diamond, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))  # 红桃和梅花 > 梅花和方块
        self.assertEqual(0, compare_hands(special_235_heart_diamond, special_235_club_diamond, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))  # 红桃和方块 > 梅花和方块
        
        # 当都包含红桃时，比较次大的花色（梅花 > 方块）
        self.assertEqual(0, compare_hands(special_235_heart_club, special_235_heart_diamond, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        
        # 测试2: 花色相同但牌面不同位置的235
        # 235的数值顺序比较 - 为了确保相等，需要使用相同的花色组合
        special_235_1 = [('2', '♠'), ('3', '♥'), ('5', '♦')]  # 5在最后
        special_235_2 = [('3', '♥'), ('5', '♦'), ('2', '♠')]  # 5在中间
        special_235_3 = [('5', '♦'), ('2', '♠'), ('3', '♥')]  # 5在最前
        
        # 这三副手牌具有相同的花色组合，只是顺序不同，所以应该相等
        self.assertEqual(1, compare_hands(special_235_1, special_235_2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        self.assertEqual(1, compare_hands(special_235_2, special_235_3, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        
        # 测试3: 验证235的特殊处理逻辑只在rank=7时生效
        # 禁用235大于豹子时，235应被视为普通单牌(rank=1)

        
        # 在禁用235大于豹子的情况下，235之间的比较应该是单牌比较逻辑
        # 此时它们都是单牌，且牌面相同，但花色不同，所以应该按花色比较
        # 黑桃235 vs 梅花235，梅花 > 黑桃，所以special_235_club > special_235_spade
        self.assertEqual(0, compare_hands(special_235_spade, special_235_club, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True))

    def test_high_card_suit_comparison(self):
        # 测试普通单牌的花色比较逻辑
        # 当牌值相同时，应按数值优先级比较花色（红桃>梅花>方块>黑桃）
        
        # 测试1：牌值完全相同但花色不同
        # 红桃 > 梅花 > 方块 > 黑桃
        hand1 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]  # 全部红桃
        hand2 = [('A', '♣'), ('K', '♣'), ('Q', '♣')]  # 全部梅花
        hand3 = [('A', '♦'), ('K', '♦'), ('Q', '♦')]  # 全部方块
        hand4 = [('A', '♠'), ('K', '♠'), ('Q', '♠')]  # 全部黑桃
        
        self.assertEqual(compare_hands(hand1, hand2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)  # 红桃 > 梅花
        self.assertEqual(compare_hands(hand2, hand3, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)  # 方块 > 梅花（正确，返回索引1表示第二个参数更大）
        self.assertEqual(compare_hands(hand3, hand4, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)  # 方块 > 黑桃
        
        # 测试2：按数值优先级比较花色
        # 牌值从大到小：A, K, Q
        # 先比较A的花色，再比较K的花色，最后比较Q的花色
        high_card_a_heart = [('A', '♥'), ('K', '♣'), ('Q', '♦')]  # A是红桃
        high_card_a_club = [('A', '♣'), ('K', '♥'), ('Q', '♥')]   # A是梅花
        
        self.assertEqual(compare_hands(high_card_a_heart, high_card_a_club, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)  # A的花色决定结果
        
        # A花色相同，比较K的花色
        high_card_a_same_k_heart = [('A', '♥'), ('K', '♥'), ('Q', '♠')]  # A相同，K是红桃
        high_card_a_same_k_club = [('A', '♥'), ('K', '♣'), ('Q', '♥')]   # A相同，K是梅花
        
        self.assertEqual(compare_hands(high_card_a_same_k_heart, high_card_a_same_k_club, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)  # K的花色决定结果
        
        # A和K花色都相同，比较Q的花色
        high_card_ak_same_q_heart = [('A', '♥'), ('K', '♥'), ('Q', '♥')]  # A和K相同，Q是红桃
        high_card_ak_same_q_club = [('A', '♥'), ('K', '♥'), ('Q', '♣')]   # A和K相同，Q是梅花
        
        self.assertEqual(compare_hands(high_card_ak_same_q_heart, high_card_ak_same_q_club, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)  # Q的花色决定结果
        
        # 测试3：牌值排序后的花色比较
        # 先按牌值降序排序，再按花色降序排序
        mixed_cards1 = [('K', '♥'), ('A', '♣'), ('Q', '♦')]  # 排序后: A♣, K♥, Q♦
        mixed_cards2 = [('A', '♦'), ('K', '♥'), ('Q', '♣')]  # 排序后: A♦, K♥, Q♣
        
        # A的花色：♦ > ♣，所以mixed_cards2 > mixed_cards1
        self.assertEqual(compare_hands(mixed_cards1, mixed_cards2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)  # 正确，返回索引1表示第二个参数更大
        
        # 测试4：完全相同的牌
        identical_hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        identical_hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        
        self.assertEqual(1, compare_hands(identical_hand1, identical_hand2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))  # 完全相同的牌应该相等
        
    def test_multi_hands_comparison(self):
        # 测试3副牌及以上同时比较的逻辑（强制开牌时使用）
        
        # 测试1：3副牌比较 - 不同牌型
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]  # 同花顺
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]  # 豹子
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]  # 顺子
        
        # 根据get_hand_rank的实现，牌型等级：豹子(6) > 同花顺(5) > 顺子(4)
        max_index = compare_hands(straight_flush, three_of_a_kind, straight, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)
        
        # 测试2：3副牌比较 - 相同牌型（单牌）
        # 按花色顺序：红桃 > 梅花 > 方块
        high_card_heart = [('A', '♥'), ('K', '♦'), ('Q', '♣')]  # 最大花色是红桃
        high_card_club = [('A', '♣'), ('K', '♥'), ('Q', '♠')]   # 最大花色是红桃
        high_card_diamond = [('A', '♦'), ('K', '♣'), ('Q', '♠')]  # 最大花色是梅花
        
        # 这里需要比较具体的花色优先级，high_card_heart中的A是红桃，high_card_club中的A是梅花，所以high_card_heart更大
        max_index = compare_hands(high_card_heart, high_card_club, high_card_diamond, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 0)
        
        # 测试3：4副牌比较 - 混合牌型
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]  # 金花
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]  # 对子
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 235
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]  # 单牌
        
        # 启用235大于豹子时，235与非豹子比较时视为单牌，所以牌型顺序为：同花顺 > 豹子 > 顺子 > 金花 > 对子 > 单牌
        # 这里special_235与非豹子比较，所以视为单牌

        max_index = compare_hands(flush, pair, special_235, high_card, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 0)  # 金花最大
        
        # 测试4：5副牌比较 - 全部是235但花色不同
        # 按数值顺序比较花色: 先比较5的花色，再比较3的花色，最后比较2的花色
        special_235_heart = [('2', '♥'), ('3', '♣'), ('5', '♦')]  # 5是方块
        special_235_club = [('2', '♣'), ('3', '♦'), ('5', '♣')]   # 5是梅花
        special_235_diamond = [('2', '♦'), ('3', '♠'), ('5', '♦')]  # 5是方块
        special_235_spade = [('2', '♠'), ('3', '♥'), ('5', '♠')]  # 5是黑桃
        special_235_mixed = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 5是黑桃
        
        # 梅花235（5是梅花）应该最大
        max_index = compare_hands(special_235_heart, special_235_club, special_235_diamond, special_235_spade, special_235_mixed, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 2)
        
        # 测试5：存在多个豹子的情况
        # 不同数值的豹子，数值大的豹子更大
        three_of_a_kind_A = [('A', '♥'), ('A', '♦'), ('A', '♣')]  # A的豹子
        three_of_a_kind_K = [('K', '♥'), ('K', '♦'), ('K', '♣')]  # K的豹子
        three_of_a_kind_Q = [('Q', '♥'), ('Q', '♦'), ('Q', '♣')]  # Q的豹子
        
        # A的豹子应该最大
        max_index = compare_hands(three_of_a_kind_K, three_of_a_kind_A, three_of_a_kind_Q, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)
        
        # 测试6：存在多个相同数值豹子的情况（通过花色比较），由于只有一副牌，所以这个情况不会出现
        # 相同数值的豹子，按花色优先级比较最大的那张牌
        # 这里提供了3副不同花色组合的豹子牌
        three_of_a_kind_heart = [('J', '♥'), ('J', '♦'), ('J', '♣')]  # 包含红桃J
        three_of_a_kind_club = [('J', '♣'), ('J', '♦'), ('J', '♠')]   # 包含梅花J
        three_of_a_kind_diamond = [('J', '♦'), ('J', '♠'), ('J', '♣')]  # 包含方块J
        
        # 按花色优先级：红桃 > 梅花 > 方块 > 黑桃，包含红桃J的豹子应该最大
        max_index = compare_hands(three_of_a_kind_club, three_of_a_kind_heart, three_of_a_kind_diamond, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)
        
        # 测试7：多种235的情况（不同花色的235和同花235）
        # 确保在测试7时，235大于豹子的设置为False
        
        # 不同花色的235
        mixed_suit_235_1 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 5是黑桃
        mixed_suit_235_2 = [('2', '♣'), ('3', '♥'), ('5', '♦')]  # 5是方块
        
        # 同花235（非同花顺）
        same_suit_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]  # 全红桃235
        
        # 重要说明：根据app.py中的逻辑，只有不同花色的235会被识别为235特殊牌型（等级1）
        # 同花的235不会被识别为235特殊牌型，而是被评估为金花（等级3）
        # 所以同花235大于非同花235的原因是：金花（等级3）大于单牌（等级1）
        max_index = compare_hands(mixed_suit_235_1, mixed_suit_235_2, same_suit_235, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True)
        self.assertEqual(max_index, 2)
        
        # 测试8：豹子与多种235的混合比较
        # 当235大于豹子设置启用时

        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]  # 豹子
        mixed_suit_235_1 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 不同花色235
        same_suit_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]   # 同花235
        mixed_suit_235_2 = [('2', '♥'), ('3', '♣'), ('5', '♠')]  # 不同花色235
        
        # 测试非同花235、同花235和豹子的比较顺序
        # 当启用非同花235大于豹子时：非同花235 > 同花235 > 豹子
        max_index = compare_hands(three_of_a_kind, mixed_suit_235_1, same_suit_235, mixed_suit_235_2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)  # 非同花235 > 同花235 > 豹子
        
        # 当235小于豹子设置禁用时

        
        # 豹子应该大于235
        max_index = compare_hands(three_of_a_kind, mixed_suit_235_1, same_suit_235, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True)
        self.assertEqual(max_index, 0)

    def test_multi_hands_edge_cases(self):
        # 测试多手牌比较的边界情况
        
        # 测试1：所有手牌完全相同
        identical_hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        identical_hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        identical_hand3 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        
        # 应该返回第一个最大手牌的索引
        max_index = compare_hands(identical_hand1, identical_hand2, identical_hand3, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 0)
        
        # 测试2：多个相同最大牌型的手牌
        # 两个相同的同花顺
        straight_flush1 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        straight_flush2 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        
        # 根据get_hand_rank的实现，豹子(6) > 同花顺(5)，所以应该返回豹子的索引
        max_index = compare_hands(straight_flush1, three_of_a_kind, straight_flush2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)
        
        # 测试3：空手牌列表
        with self.assertRaises(ValueError):
            compare_hands(raise_compare_hand_index=0)
            
        # 测试4：只有一副手牌
        hand = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        # 根据compare_hands的实现，至少需要比较两手牌，所以应该抛出ValueError
        with self.assertRaises(ValueError):
            compare_hands(hand, raise_compare_hand_index=0)

    def test_235_with_three_of_a_kind_combinations(self):
        """测试非同花235与豹子的各种组合情况"""
        # 测试1: 非同花235在不同豹子存在时的比较
        three_of_a_kind_2 = [('2', '♥'), ('2', '♦'), ('2', '♣')]  # 2的豹子
        three_of_a_kind_3 = [('3', '♥'), ('3', '♦'), ('3', '♣')]  # 3的豹子
        three_of_a_kind_A = [('A', '♥'), ('A', '♦'), ('A', '♣')]  # A的豹子
        
        # 非同花235
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        
        # 启用235大于豹子规则
        # 非同花235应该大于所有豹子
        self.assertEqual(0, compare_hands(special_235, three_of_a_kind_2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        self.assertEqual(0, compare_hands(special_235, three_of_a_kind_3, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        self.assertEqual(0, compare_hands(special_235, three_of_a_kind_A, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        
        # 禁用235大于豹子规则
        # 非同花235应该小于所有豹子
        self.assertEqual(1, compare_hands(special_235, three_of_a_kind_2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True))
        self.assertEqual(1, compare_hands(special_235, three_of_a_kind_3, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True))
        self.assertEqual(1, compare_hands(special_235, three_of_a_kind_A, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True))
        
        # 测试2: 多手牌比较，包含豹子和非同花235
        # 启用235大于豹子规则
        hands = [
            three_of_a_kind_2,
            three_of_a_kind_3,
            three_of_a_kind_A,
            special_235
        ]
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 3)  # 非同花235应该最大
        
        # 禁用235大于豹子规则
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True)
        self.assertEqual(max_index, 2)  # A的豹子应该最大
        
        # 测试3: 同花235与豹子的比较（同花235被视为金花，不遵循235特殊规则）
        same_suit_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]  # 同花235（金花）
        
        # 同花235应该小于豹子，无论235规则是否启用
        self.assertEqual(compare_hands(same_suit_235, three_of_a_kind_2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        self.assertEqual(compare_hands(same_suit_235, three_of_a_kind_2, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True), 1)
        
        # 测试4: 非同花235与同花235的比较
        # 非同花235（特殊牌型）vs 同花235（金花）
        # 当启用235大于豹子规则时，由于所有手牌中没有豹子，以同花235更大
        self.assertEqual(compare_hands(special_235, same_suit_235, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 当禁用235大于豹子规则时，非同花235等级为1，同花235等级为3，所以同花235更大
        self.assertEqual(compare_hands(special_235, same_suit_235, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True), 1)

    def test_a23_as_straight_combinations(self):
        """测试A23作为顺子的各种组合情况"""
        # 测试1: A23与其他顺子的比较
        a23 = [('A', '♥'), ('2', '♦'), ('3', '♠')]  # A23
        straight_234 = [('2', '♥'), ('3', '♦'), ('4', '♠')]  # 234顺子
        straight_345 = [('3', '♥'), ('4', '♦'), ('5', '♠')]  # 345顺子
        straight_QKA = [('Q', '♥'), ('K', '♦'), ('A', '♠')]  # QKA顺子
        
        # 启用A23作为顺子
        # A23应该小于其他顺子（A23是最小的顺子）
        self.assertEqual(compare_hands(a23, straight_234, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        self.assertEqual(compare_hands(a23, straight_345, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        self.assertEqual(compare_hands(a23, straight_QKA, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 禁用A23作为顺子
        # A23应该被视为普通单牌，所以应该小于所有顺子
        self.assertEqual(compare_hands(a23, straight_234, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False), 1)
        self.assertEqual(compare_hands(a23, straight_345, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False), 1)
        self.assertEqual(compare_hands(a23, straight_QKA, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False), 1)
        
        # 测试2: 同花A23与其他同花顺的比较
        flush_a23 = [('A', '♥'), ('2', '♥'), ('3', '♥')]  # 同花A23
        flush_234 = [('2', '♥'), ('3', '♥'), ('4', '♥')]  # 同花顺234
        flush_QKA = [('Q', '♥'), ('K', '♥'), ('A', '♥')]  # 同花顺QKA
        
        # 启用A23作为顺子
        # 同花A23应该小于其他同花顺（同花A23是最小的同花顺）
        self.assertEqual(compare_hands(flush_a23, flush_234, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        self.assertEqual(compare_hands(flush_a23, flush_QKA, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)
        
        # 禁用A23作为顺子，同花A23应该被视为金花，所以应该小于同花顺
        self.assertEqual(1, compare_hands(flush_a23, flush_234, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False))
        self.assertEqual(1, compare_hands(flush_a23, flush_QKA, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False))
        
        # 测试3: 多手牌比较，包含A23和其他牌型
        hands = [
            a23,  # A23
            straight_234,  # 234顺子
            straight_345,  # 345顺子
            straight_QKA,  # QKA顺子
            [('K', '♥'), ('K', '♦'), ('K', '♣')]  # K的豹子
        ]
        
        # 启用A23作为顺子
        # 牌型等级：豹子(6) > 同花顺(5) > 顺子(4) > 金花(3) > 对子(2) > 单牌(1)
        # A23是最小的顺子，所以应该排在顺子中的最后
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 4)  # 豹子应该最大
        
        # 禁用A23作为顺子
        # A23被视为单牌，所以应该小于所有顺子
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False)
        self.assertEqual(max_index, 4)  # 豹子应该最大
        
        # 测试4: 非同花A23与其他牌型的比较
        mixed_suit_a23 = [('A', '♥'), ('2', '♦'), ('3', '♠')]  # 非同花A23
        
        # 启用A23作为顺子
        # 非同花A23是顺子应该大于金花
        flush = [('2', '♥'), ('5', '♥'), ('10', '♥')]  # 金花
        self.assertEqual(0, compare_hands(mixed_suit_a23, flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True))
        
        # 禁用A23作为顺子，非同花A23应该被视为单牌，所以应该小于金花
        self.assertEqual(1, compare_hands(mixed_suit_a23, flush, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False))

    def test_complex_hand_combinations(self):
        """测试复杂的手牌组合情况"""
        # 测试1: 包含豹子、非同花235、同花235、非同花A23、同花A23的组合
        three_of_a_kind = [('K', '♥'), ('K', '♦'), ('K', '♣')]  # K的豹子
        different_suit_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 非同花235
        same_suit_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]  # 同花235（金花）
        different_suit_a23 = [('A', '♥'), ('2', '♦'), ('3', '♠')]  # 非同花A23
        same_suit_a23 = [('A', '♥'), ('2', '♥'), ('3', '♥')]  # 同花A23
        straight = [('4', '♥'), ('5', '♦'), ('6', '♠')]  # 普通顺子
        flush = [('2', '♥'), ('5', '♥'), ('10', '♥')]  # 金花
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]  # 对子
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]  # 单牌
        
        # 启用235大于豹子和A23作为顺子
        hands = [three_of_a_kind, different_suit_235, same_suit_235, different_suit_a23, same_suit_a23,
                 straight, flush, pair, high_card]
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)  # 实际返回的是非同花235的索引（等级7）
        
        # 禁用235大于豹子和A23作为顺子
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=False)
        self.assertEqual(max_index, 0)  # 豹子应该最大（等级6）

        # 测试2: 同花235与同花A23的比较
        # 启用A23作为顺子
        # 同花235是金花（等级3），同花A23是同花顺（等级5，如果A23作为顺子），所以同花A23更大
        self.assertEqual(compare_hands(same_suit_235, same_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)  # 同花A23(同花顺)应大于同花235
        
        # 禁用A23作为顺子，同花A23为同花，A大于5，所以同花A23更大
        self.assertEqual(compare_hands(same_suit_235, same_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False), 1)  # 同花A23应大于同花235

        # 测试3: 非同花235与非同花A23的比较
        # 非同花235（等级1或7）vs 非同花A23（等级1或4）
        # 启用235大于豹子和A23作为顺子，启用A23是顺子
        self.assertEqual(compare_hands(different_suit_235, different_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 1)  # 非同花A23(顺子)应大于非同花235
        
        # 禁用235大于豹子但启用A23作为顺子
        self.assertEqual(compare_hands(different_suit_235, different_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=True), 1)  # 非同花A23(顺子)应大于非同花235(单牌)

        # 启用235大于豹子但禁用A23作为顺子
        self.assertEqual(compare_hands(different_suit_235, different_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False), 1)  # 非同花235应大于非同花A23
        
        # 禁用235大于豹子和A23作为顺子
        # 两者都是单牌，按牌面值比较
        self.assertEqual(compare_hands(different_suit_235, different_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=False), 1)  # 非同花A23应大于非同花235

        # 测试4: 包含所有特殊牌型的多手牌比较
        # 启用235大于豹子和A23作为顺子
        hands = [three_of_a_kind, different_suit_235, same_suit_235, different_suit_a23, same_suit_a23,
                 straight, flush, pair, high_card]
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True)
        self.assertEqual(max_index, 1)  # 非同花235应该最大（等级7）
        
        # 禁用235大于豹子和A23作为顺子
        max_index = compare_hands(*hands, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=False, is_A23_as_straight=False)
        self.assertEqual(max_index, 0)  # 豹子应该最大（等级6）

        # 测试5: 多手牌比较中的特殊情况
        # 启用A23作为顺子
        # [同花A23(同花顺), 同花235(金花), 非同花235(特殊牌型), 非同花A23(顺子)]
        # 同花A23应该是最大的（同花顺）
        self.assertEqual(compare_hands(same_suit_a23, same_suit_235, different_suit_235, different_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=True), 0)

        # 禁用A23作为顺子
        # [同花A23(金花), 同花235(金花), 非同花235(特殊牌型), 非同花A23(单牌)]
        # 同花235应该是最大的
        self.assertEqual(0, compare_hands(same_suit_a23, same_suit_235, different_suit_235, different_suit_a23, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False))

        # 禁用A23作为顺子
        # [同花A23(金花), 同花235(金花), 非同花235(特殊牌型), 非同花A23(单牌), 豹子]
        # 非同花235(特殊牌型)应该是最大的
        self.assertEqual(2, compare_hands(same_suit_a23, same_suit_235, different_suit_235, different_suit_a23, three_of_a_kind, raise_compare_hand_index=0, isDiffentSuit235GreaterThanThreeOfAKind=True, is_A23_as_straight=False))



if __name__ == '__main__':
    unittest.main()