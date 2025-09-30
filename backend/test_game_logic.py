import unittest
from app import (
    is_straight_flush, is_three_of_a_kind, is_straight, is_flush, is_pair,
    get_hand_rank, compare_hands, room
)

class TestTractorGameLogic(unittest.TestCase):
    
    def setUp(self):
        # 保存原始设置，以便测试后恢复
        self.original_235_setting = room['settings']['is_235_greater_than_three_of_a_kind']
        
    def tearDown(self):
        # 恢复原始设置
        room['settings']['is_235_greater_than_three_of_a_kind'] = self.original_235_setting
    
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
        # 测试禁用235大于豹子的情况
        room['settings']['is_235_greater_than_three_of_a_kind'] = False
        
        # 同花顺（相同花色的顺子）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertEqual(get_hand_rank(straight_flush), 5)
        
        # 豹子
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertEqual(get_hand_rank(three_of_a_kind), 6)
        
        # 235（不同花色）
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        self.assertEqual(get_hand_rank(special_235), 1)  # 此时应视为单牌
        
        # 顺子（非同花顺）
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertEqual(get_hand_rank(straight), 4)
        
        # 金花（相同花色的非顺子）
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertEqual(get_hand_rank(flush), 3)
        
        # 对子
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertEqual(get_hand_rank(pair), 2)
        
        # 单牌
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]
        self.assertEqual(get_hand_rank(high_card), 1)
    
    def test_hand_rank_with_235_enabled(self):
        # 测试启用235大于豹子的情况
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        
        # 235（不同花色）- 现在始终被视为单牌
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        self.assertEqual(get_hand_rank(special_235), 1)  # 不同花色的235始终被视为单牌
        
        # 235（相同花色）- 此时应视为金花
        flush_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]
        self.assertEqual(get_hand_rank(flush_235), 3)  # 此时应视为金花
        
        # 豹子
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertEqual(get_hand_rank(three_of_a_kind), 6)
        
        # 同花顺（相同花色的顺子）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertEqual(get_hand_rank(straight_flush), 5)
    
    def test_compare_hands_different_types(self):
        # 测试不同牌型之间的比较
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        
        # 不同花色的235 > 豹子
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        self.assertGreater(compare_hands(special_235, three_of_a_kind), 0)
        self.assertLess(compare_hands(three_of_a_kind, special_235), 0)
        
        # 235 < 同花顺（因为235与非豹子比较时视为单牌）
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertLess(compare_hands(special_235, straight_flush), 0)
        
        # 235 < 顺子（因为235与非豹子比较时视为单牌）
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertLess(compare_hands(special_235, straight), 0)
        
        # 235 < 金花（因为235与非豹子比较时视为单牌）
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertLess(compare_hands(special_235, flush), 0)
        
        # 235 < 对子（因为235与非豹子比较时视为单牌）
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertLess(compare_hands(special_235, pair), 0)
        
        # 豹子 > 同花顺
        self.assertGreater(compare_hands(three_of_a_kind, straight_flush), 0)
        
        # 同花顺 > 顺子
        self.assertGreater(compare_hands(straight_flush, straight), 0)
        
        # 顺子 > 金花
        self.assertGreater(compare_hands(straight, flush), 0)
        
        # 金花 > 对子
        self.assertGreater(compare_hands(flush, pair), 0)
        
        # 对子 > 单牌
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]
        self.assertGreater(compare_hands(pair, high_card), 0)
    
    def test_compare_hands_same_types(self):
        # 测试相同牌型之间的比较
        
        # 相同牌型的顺子比较
        straight1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]  # 更大的顺子
        straight2 = [('J', '♥'), ('10', '♦'), ('9', '♣')]  # 更小的顺子
        self.assertGreater(compare_hands(straight1, straight2), 0)
        
        # 相同牌型的对子比较
        pair1 = [('A', '♥'), ('A', '♦'), ('5', '♣')]  # A对
        pair2 = [('K', '♥'), ('K', '♦'), ('10', '♣')]  # K对
        self.assertGreater(compare_hands(pair1, pair2), 0)
        
        # 相同牌型的单牌比较
        high_card1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]  # A-K-Q
        high_card2 = [('K', '♥'), ('Q', '♦'), ('J', '♣')]  # K-Q-J
        self.assertGreater(compare_hands(high_card1, high_card2), 0)
        
        # 完全相同的牌
        hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        self.assertEqual(compare_hands(hand1, hand2), 0)
    
    def test_235_rule_edge_cases(self):
        # 测试235规则的边界情况
        
        # 启用235大于豹子时
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        
        # 测试不同花色的235与最大的豹子比较
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        three_of_a_kind_ace = [('A', '♥'), ('A', '♦'), ('A', '♣')]  # A的豹子
        self.assertGreater(compare_hands(special_235, three_of_a_kind_ace), 0)
        
        # 测试相同花色的235（金花）与豹子比较
        flush_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]
        self.assertLess(compare_hands(flush_235, three_of_a_kind_ace), 0)  # 金花应小于豹子
        
    def test_235_as_high_card_against_non_three_of_a_kind(self):
        # 测试235与非豹子比较时视为单牌的逻辑
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        
        # 235 < 同花顺
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        self.assertLess(compare_hands(special_235, straight_flush), 0)
        
        # 235 < 顺子
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]
        self.assertLess(compare_hands(special_235, straight), 0)
        
        # 235 < 金花
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]
        self.assertLess(compare_hands(special_235, flush), 0)
        
        # 235 < 对子
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]
        self.assertLess(compare_hands(special_235, pair), 0)
        
        # 注意：235只有在与豹子比较时才有特殊地位
        # 在与非豹子的手牌比较时，235被视为单牌（根据compare_hands函数中的逻辑）
    
    def test_a23_smallest_straight(self):
        # 测试A23是最小的顺子
        a23 = [('A', '♥'), ('2', '♦'), ('3', '♣')]
        straight_234 = [('2', '♥'), ('3', '♦'), ('4', '♣')]
        
        self.assertTrue(is_straight(a23))
        self.assertTrue(is_straight(straight_234))
        
        # A23应小于234顺子
        self.assertLess(compare_hands(a23, straight_234), 0)
    
    def test_different_suits_235_comparison(self):
        # 测试多个玩家同时持有不同花色235时的比较逻辑
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        
        # 测试1: 牌面数值相同但花色不同的235
        # 不同花色的235 - 牌面相同但花色不同
        # 花色顺序: ♥ > ♣ > ♦ > ♠  (红桃>梅花>方块>黑桃)
        special_235_spade = [('2', '♠'), ('3', '♦'), ('5', '♠')]   # 包含黑桃和方块
        special_235_club = [('2', '♣'), ('3', '♦'), ('5', '♣')]    # 包含梅花和方块
        special_235_diamond = [('2', '♦'), ('3', '♠'), ('5', '♣')]  # 包含方块、黑桃、梅花
        special_235_heart = [('2', '♥'), ('3', '♣'), ('5', '♦')]   # 包含红桃、梅花、方块
        
        # 按数值顺序比较花色: 先比较5的花色，再比较3的花色，最后比较2的花色
        # 花色顺序: 红桃 > 梅花 > 方块 > 黑桃
        self.assertLess(compare_hands(special_235_heart, special_235_club), 0)   # 红桃235 < 梅花235 (因为红桃235中5的花色是方块，梅花235中5的花色是梅花)
        self.assertGreater(compare_hands(special_235_heart, special_235_spade), 0)   # 红桃235 > 黑桃235
        self.assertGreater(compare_hands(special_235_club, special_235_spade), 0)    # 梅花235 > 黑桃235
        
        # 测试2: 真正的不同花色组合比较
        # 创建明确不同花色组合的235手牌
        special_235_heart_club = [('2', '♥'), ('3', '♣'), ('5', '♦')]  # 红桃、梅花、方块
        special_235_heart_diamond = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 红桃、方块、黑桃
        special_235_club_diamond = [('2', '♣'), ('3', '♦'), ('5', '♠')]  # 梅花、方块、黑桃
        
        # 红桃是最大的花色，所以包含红桃的235大于不包含红桃的
        self.assertGreater(compare_hands(special_235_heart_club, special_235_club_diamond), 0)  # 红桃和梅花 > 梅花和方块
        self.assertGreater(compare_hands(special_235_heart_diamond, special_235_club_diamond), 0)  # 红桃和方块 > 梅花和方块
        
        # 当都包含红桃时，比较次大的花色（梅花 > 方块）
        self.assertGreater(compare_hands(special_235_heart_club, special_235_heart_diamond), 0)
        
        # 测试2: 花色相同但牌面不同位置的235
        # 235的数值顺序比较 - 为了确保相等，需要使用相同的花色组合
        special_235_1 = [('2', '♠'), ('3', '♥'), ('5', '♦')]  # 5在最后
        special_235_2 = [('3', '♥'), ('5', '♦'), ('2', '♠')]  # 5在中间
        special_235_3 = [('5', '♦'), ('2', '♠'), ('3', '♥')]  # 5在最前
        
        # 这三副手牌具有相同的花色组合，只是顺序不同，所以应该相等
        self.assertEqual(compare_hands(special_235_1, special_235_2), 0)
        self.assertEqual(compare_hands(special_235_2, special_235_3), 0)
        
        # 测试3: 验证235的特殊处理逻辑只在rank=7时生效
        # 禁用235大于豹子时，235应被视为普通顺子(rank=4)
        room['settings']['is_235_greater_than_three_of_a_kind'] = False
        
        # 在禁用235大于豹子的情况下，235之间的比较应该是顺子比较逻辑
        # 此时它们都是顺子，且牌面相同，所以应该相等
        self.assertEqual(compare_hands(special_235_spade, special_235_club), 0)

    def test_high_card_suit_comparison(self):
        # 测试普通单牌的花色比较逻辑
        # 当牌值相同时，应按数值优先级比较花色（红桃>梅花>方块>黑桃）
        
        # 测试1：牌值完全相同但花色不同
        # 红桃 > 梅花 > 方块 > 黑桃
        hand1 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]  # 全部红桃
        hand2 = [('A', '♣'), ('K', '♣'), ('Q', '♣')]  # 全部梅花
        hand3 = [('A', '♦'), ('K', '♦'), ('Q', '♦')]  # 全部方块
        hand4 = [('A', '♠'), ('K', '♠'), ('Q', '♠')]  # 全部黑桃
        
        self.assertGreater(compare_hands(hand1, hand2), 0)  # 红桃 > 梅花
        self.assertGreater(compare_hands(hand2, hand3), 0)  # 梅花 > 方块
        self.assertGreater(compare_hands(hand3, hand4), 0)  # 方块 > 黑桃
        
        # 测试2：按数值优先级比较花色
        # 牌值从大到小：A, K, Q
        # 先比较A的花色，再比较K的花色，最后比较Q的花色
        high_card_a_heart = [('A', '♥'), ('K', '♣'), ('Q', '♦')]  # A是红桃
        high_card_a_club = [('A', '♣'), ('K', '♥'), ('Q', '♥')]   # A是梅花
        
        self.assertGreater(compare_hands(high_card_a_heart, high_card_a_club), 0)  # A的花色决定结果
        
        # A花色相同，比较K的花色
        high_card_a_same_k_heart = [('A', '♥'), ('K', '♥'), ('Q', '♠')]  # A相同，K是红桃
        high_card_a_same_k_club = [('A', '♥'), ('K', '♣'), ('Q', '♥')]   # A相同，K是梅花
        
        self.assertGreater(compare_hands(high_card_a_same_k_heart, high_card_a_same_k_club), 0)  # K的花色决定结果
        
        # A和K花色都相同，比较Q的花色
        high_card_ak_same_q_heart = [('A', '♥'), ('K', '♥'), ('Q', '♥')]  # A和K相同，Q是红桃
        high_card_ak_same_q_club = [('A', '♥'), ('K', '♥'), ('Q', '♣')]   # A和K相同，Q是梅花
        
        self.assertGreater(compare_hands(high_card_ak_same_q_heart, high_card_ak_same_q_club), 0)  # Q的花色决定结果
        
        # 测试3：牌值排序后的花色比较
        # 先按牌值降序排序，再按花色降序排序
        mixed_cards1 = [('K', '♥'), ('A', '♣'), ('Q', '♦')]  # 排序后: A♣, K♥, Q♦
        mixed_cards2 = [('A', '♦'), ('K', '♥'), ('Q', '♣')]  # 排序后: A♦, K♥, Q♣
        
        # A的花色：♣ > ♦，所以mixed_cards1 > mixed_cards2
        self.assertGreater(compare_hands(mixed_cards1, mixed_cards2), 0)
        
        # 测试4：完全相同的牌
        identical_hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        identical_hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        
        self.assertEqual(compare_hands(identical_hand1, identical_hand2), 0)  # 完全相同的牌应该相等
        
    def test_multi_hands_comparison(self):
        # 测试3副牌及以上同时比较的逻辑（强制开牌时使用）
        
        # 测试1：3副牌比较 - 不同牌型
        straight_flush = [('A', '♥'), ('K', '♥'), ('Q', '♥')]  # 同花顺
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]  # 豹子
        straight = [('10', '♥'), ('J', '♦'), ('Q', '♣')]  # 顺子
        
        # 根据get_hand_rank的实现，牌型等级：豹子(6) > 同花顺(5) > 顺子(4)
        max_index = compare_hands(straight_flush, three_of_a_kind, straight)
        self.assertEqual(max_index, 1)
        
        # 测试2：3副牌比较 - 相同牌型（单牌）
        # 按花色顺序：红桃 > 梅花 > 方块
        high_card_heart = [('A', '♥'), ('K', '♦'), ('Q', '♣')]  # 最大花色是红桃
        high_card_club = [('A', '♣'), ('K', '♥'), ('Q', '♠')]   # 最大花色是红桃
        high_card_diamond = [('A', '♦'), ('K', '♣'), ('Q', '♠')]  # 最大花色是梅花
        
        # 这里需要比较具体的花色优先级，high_card_heart中的A是红桃，high_card_club中的A是梅花，所以high_card_heart更大
        max_index = compare_hands(high_card_heart, high_card_club, high_card_diamond)
        self.assertEqual(max_index, 0)
        
        # 测试3：4副牌比较 - 混合牌型
        flush = [('2', '♠'), ('5', '♠'), ('10', '♠')]  # 金花
        pair = [('A', '♥'), ('A', '♦'), ('5', '♣')]  # 对子
        special_235 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 235
        high_card = [('3', '♥'), ('7', '♦'), ('K', '♠')]  # 单牌
        
        # 启用235大于豹子时，235与非豹子比较时视为单牌，所以牌型顺序为：同花顺 > 豹子 > 顺子 > 金花 > 对子 > 单牌
        # 这里special_235与非豹子比较，所以视为单牌
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        max_index = compare_hands(flush, pair, special_235, high_card)
        self.assertEqual(max_index, 0)  # 金花最大
        
        # 测试4：5副牌比较 - 全部是235但花色不同
        # 按数值顺序比较花色: 先比较5的花色，再比较3的花色，最后比较2的花色
        special_235_heart = [('2', '♥'), ('3', '♣'), ('5', '♦')]  # 5是方块
        special_235_club = [('2', '♣'), ('3', '♦'), ('5', '♣')]   # 5是梅花
        special_235_diamond = [('2', '♦'), ('3', '♠'), ('5', '♦')]  # 5是方块
        special_235_spade = [('2', '♠'), ('3', '♥'), ('5', '♠')]  # 5是黑桃
        special_235_mixed = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 5是黑桃
        
        # 梅花235（5是梅花）应该最大
        max_index = compare_hands(special_235_heart, special_235_club, special_235_diamond, special_235_spade, special_235_mixed)
        self.assertEqual(max_index, 1)
        
        # 测试5：存在多个豹子的情况
        # 不同数值的豹子，数值大的豹子更大
        three_of_a_kind_A = [('A', '♥'), ('A', '♦'), ('A', '♣')]  # A的豹子
        three_of_a_kind_K = [('K', '♥'), ('K', '♦'), ('K', '♣')]  # K的豹子
        three_of_a_kind_Q = [('Q', '♥'), ('Q', '♦'), ('Q', '♣')]  # Q的豹子
        
        # A的豹子应该最大
        max_index = compare_hands(three_of_a_kind_K, three_of_a_kind_A, three_of_a_kind_Q)
        self.assertEqual(max_index, 1)
        
        # 测试6：存在多个相同数值豹子的情况（通过花色比较），由于只有一副牌，所以这个情况不会出现
        # 相同数值的豹子，按花色优先级比较最大的那张牌
        # 这里提供了3副不同花色组合的豹子牌
        three_of_a_kind_heart = [('J', '♥'), ('J', '♦'), ('J', '♣')]  # 包含红桃J
        three_of_a_kind_club = [('J', '♣'), ('J', '♦'), ('J', '♠')]   # 包含梅花J
        three_of_a_kind_diamond = [('J', '♦'), ('J', '♠'), ('J', '♣')]  # 包含方块J
        
        # 按花色优先级：红桃 > 梅花 > 方块 > 黑桃，包含红桃J的豹子应该最大
        max_index = compare_hands(three_of_a_kind_club, three_of_a_kind_heart, three_of_a_kind_diamond)
        self.assertEqual(max_index, 1)
        
        # 测试7：多种235的情况（不同花色的235和同花235）
        # 确保在测试7时，235大于豹子的设置为False
        room['settings']['is_235_greater_than_three_of_a_kind'] = False
        
        # 不同花色的235
        mixed_suit_235_1 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 5是黑桃
        mixed_suit_235_2 = [('2', '♣'), ('3', '♥'), ('5', '♦')]  # 5是方块
        
        # 同花235（非同花顺）
        same_suit_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]  # 全红桃235
        
        # 重要说明：根据app.py中的逻辑，只有不同花色的235会被识别为235特殊牌型（等级1）
        # 同花的235不会被识别为235特殊牌型，而是被评估为金花（等级3）
        # 所以同花235大于非同花235的原因是：金花（等级3）大于单牌（等级1）
        max_index = compare_hands(mixed_suit_235_1, mixed_suit_235_2, same_suit_235)
        self.assertEqual(max_index, 2)
        
        # 测试8：豹子与多种235的混合比较
        # 当235大于豹子设置启用时
        room['settings']['is_235_greater_than_three_of_a_kind'] = True
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]  # 豹子
        mixed_suit_235_1 = [('2', '♥'), ('3', '♦'), ('5', '♠')]  # 不同花色235
        same_suit_235 = [('2', '♥'), ('3', '♥'), ('5', '♥')]   # 同花235
        mixed_suit_235_2 = [('2', '♥'), ('3', '♣'), ('5', '♠')]  # 不同花色235
        
        # 测试非同花235、同花235和豹子的比较顺序
        # 当启用非同花235大于豹子时：非同花235 > 同花235 > 豹子
        max_index = compare_hands(three_of_a_kind, mixed_suit_235_1, same_suit_235, mixed_suit_235_2)
        self.assertEqual(max_index, 3)  # 非同花235 > 同花235 > 豹子
        
        # 当235小于豹子设置禁用时
        room['settings']['is_235_greater_than_three_of_a_kind'] = False
        
        # 豹子应该大于235
        max_index = compare_hands(three_of_a_kind, mixed_suit_235_1, same_suit_235)
        self.assertEqual(max_index, 0)

    def test_multi_hands_edge_cases(self):
        # 测试多手牌比较的边界情况
        
        # 测试1：所有手牌完全相同
        identical_hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        identical_hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        identical_hand3 = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        
        # 应该返回第一个最大手牌的索引
        max_index = compare_hands(identical_hand1, identical_hand2, identical_hand3)
        self.assertEqual(max_index, 0)
        
        # 测试2：多个相同最大牌型的手牌
        # 两个相同的同花顺
        straight_flush1 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        straight_flush2 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        three_of_a_kind = [('J', '♥'), ('J', '♦'), ('J', '♣')]
        
        # 根据get_hand_rank的实现，豹子(6) > 同花顺(5)，所以应该返回豹子的索引
        max_index = compare_hands(straight_flush1, three_of_a_kind, straight_flush2)
        self.assertEqual(max_index, 1)
        
        # 测试3：空手牌列表
        with self.assertRaises(ValueError):
            compare_hands()
            
        # 测试4：只有一副手牌
        hand = [('A', '♥'), ('K', '♦'), ('Q', '♣')]
        # 根据compare_hands的实现，至少需要比较两手牌，所以应该抛出ValueError
        with self.assertRaises(ValueError):
            compare_hands(hand)

if __name__ == '__main__':
    unittest.main()