# -*- coding: utf-8 -*-
"""
测试 compare_two_hands 函数的测试用例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game_logic import compare_two_hands
import unittest


class TestCompareTwoHands(unittest.TestCase):
    """测试compare_two_hands函数"""
    
    def test_compare_different_levels(self):
        """测试不同等级的手牌比较"""
        # 豹子 > 同花顺 > 同花 > 顺子 > 对子 > 单牌
        # 豹子 vs 同花顺
        hand1 = [('A', '♥'), ('A', '♦'), ('A', '♠')]
        hand2 = [('K', '♥'), ('Q', '♥'), ('J', '♥')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，等级差为6-5=1
        
        # 同花顺 vs 同花
        hand1 = [('K', '♥'), ('Q', '♥'), ('J', '♥')]
        hand2 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, -1)  # hand2 赢，同等级，但hand2有A
        
        # 同花顺 vs 顺子
        hand1 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，等级差为5-4=1
        
        # 顺子 vs 对子
        hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        hand2 = [('A', '♥'), ('A', '♦'), ('K', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 2)  # hand1 赢，等级差为4-2=2
        
        # 对子 vs 顺子
        hand1 = [('A', '♥'), ('A', '♦'), ('K', '♠')]
        hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, -2)  # hand2 赢，等级差为2-4=-2
    
    def test_compare_same_hands(self):
        """测试相同手牌的比较"""
        hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        hand2 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 0)  # 平局
        
        hand1 = [('A', '♥'), ('A', '♦'), ('K', '♠')]
        hand2 = [('A', '♥'), ('A', '♦'), ('K', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 0)  # 平局
    
    def test_compare_same_level_straight_flush(self):
        """测试同等级同花顺的比较"""
        # 不同点数的同花顺
        hand1 = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        hand2 = [('K', '♠'), ('Q', '♠'), ('J', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为A > K
        
        # 相同点数不同花色的同花顺
        hand1 = [('K', '♥'), ('Q', '♥'), ('J', '♥')]
        hand2 = [('K', '♠'), ('Q', '♠'), ('J', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为红桃 > 黑桃
    
    def test_compare_same_level_straight(self):
        """测试同等级顺子的比较"""
        # 不同点数的顺子
        hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        hand2 = [('K', '♥'), ('Q', '♦'), ('J', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为A > K
        
        # 相同点数不同花色的顺子
        hand1 = [('K', '♥'), ('Q', '♥'), ('J', '♦')]
        hand2 = [('K', '♠'), ('Q', '♠'), ('J', '♣')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为红桃 > 黑桃
        
        # A23特殊顺子比较
        hand1 = [('A', '♥'), ('2', '♥'), ('3', '♥')]
        hand2 = [('2', '♠'), ('3', '♠'), ('4', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, -1)  # hand2 赢，因为4 > A(作为1)
    
    def test_compare_same_level_flush(self):
        """测试同等级同花的比较"""
        # 不同点数的同花
        hand1 = [('A', '♥'), ('K', '♥'), ('J', '♥')]
        hand2 = [('K', '♠'), ('Q', '♠'), ('J', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, -2)  # hand2 赢，等级差为3-5=-2
        
        # 相同点数不同花色的同花
        hand1 = [('K', '♥'), ('Q', '♥'), ('J', '♥')]
        hand2 = [('K', '♠'), ('Q', '♠'), ('J', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，相同等级，相同牌面，红桃 > 黑桃
    
    def test_compare_same_level_pair(self):
        """测试同等级对子的比较"""
        # 不同点数的对子
        hand1 = [('A', '♥'), ('A', '♦'), ('K', '♠')]
        hand2 = [('K', '♥'), ('K', '♦'), ('Q', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为A > K
        
        # 相同点数不同花色的对子
        hand1 = [('K', '♥'), ('K', '♦'), ('Q', '♠')]
        hand2 = [('K', '♠'), ('K', '♣'), ('Q', '♥')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为红桃 > 黑桃
    
    def test_compare_same_level_single(self):
        """测试同等级单牌的比较"""
        # 不同点数的单牌
        hand1 = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        hand2 = [('K', '♥'), ('Q', '♦'), ('J', '♠')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为A > K
        
        # 相同点数不同花色的单牌
        hand1 = [('K', '♥'), ('Q', '♦'), ('J', '♠')]
        hand2 = [('K', '♠'), ('Q', '♣'), ('J', '♥')]
        result = compare_two_hands(hand1, hand2, False, False)
        self.assertEqual(result, 1)  # hand1 赢，因为红桃 > 黑桃
    
    def test_compare_special_cases(self):
        """测试特殊情况"""
        # 235 vs 三条的特殊规则
        hand1 = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        hand2 = [('3', '♥'), ('3', '♦'), ('3', '♠')]
        result = compare_two_hands(hand1, hand2, True, False)  # 235 < 三条
        self.assertEqual(result, -5)  # hand2 赢，等级差为1-6=-5
        
        result = compare_two_hands(hand1, hand2, False, False)  # 235 < 三条
        self.assertEqual(result, -5)  # hand2 赢，等级差为1-6=-5

if __name__ == '__main__':
    unittest.main()