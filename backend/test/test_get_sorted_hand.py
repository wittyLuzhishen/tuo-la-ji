# -*- coding: utf-8 -*-
"""
测试 get_sorted_hand 函数的测试用例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from game_logic import get_sorted_hand

class TestGetSortedHand(unittest.TestCase):
    """测试get_sorted_hand函数"""
    
    def test_sort_by_rank(self):
        """测试按牌面数值排序"""
        # 不同牌面数值的牌应该按数值从大到小排序
        hand = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('K', '♦'), ('Q', '♠')])
        
        hand = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('5', '♠'), ('3', '♦'), ('2', '♥')])
        
        hand = [('10', '♥'), ('J', '♦'), ('Q', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('Q', '♠'), ('J', '♦'), ('10', '♥')])
    
    def test_sort_by_suit(self):
        """测试按花色排序"""
        # 相同牌面数值不同花色的牌应该按花色从大到小排序
        hand = [('A', '♥'), ('A', '♦'), ('A', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♦'), ('A', '♠')])
        
        hand = [('K', '♣'), ('K', '♠'), ('K', '♥')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('K', '♥'), ('K', '♠'), ('K', '♣')])
    
    def test_sort_pair(self):
        """测试对子排序"""
        # 对子中的两张牌应该排在前面，单牌排在后面
        hand = [('A', '♥'), ('A', '♦'), ('5', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♦'), ('5', '♠')])
        
        hand = [('5', '♠'), ('A', '♥'), ('A', '♦')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♦'), ('5', '♠')])
        
        hand = [('A', '♦'), ('5', '♠'), ('A', '♥')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♦'), ('5', '♠')])
    
    def test_sort_a23_as_straight(self):
        """测试A23作为顺子时的排序"""
        # A23作为顺子时，A应该被视为1
        hand = [('A', '♥'), ('2', '♦'), ('3', '♠')]
        sorted_hand = get_sorted_hand(hand, is_A23_as_straight=True)
        self.assertEqual(sorted_hand, [('3', '♠'), ('2', '♦'), ('A', '♥')])
        
        # A23不作为顺子时，A应该被视为14
        sorted_hand = get_sorted_hand(hand, is_A23_as_straight=False)
        self.assertEqual(sorted_hand, [('A', '♥'), ('3', '♠'), ('2', '♦')])
    
    def test_sort_complex_hand(self):
        """测试复杂手牌排序"""
        # 混合不同牌面数值和花色的牌
        hand = [('2', '♥'), ('A', '♦'), ('K', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♦'), ('K', '♠'), ('2', '♥')])
        
        hand = [('10', '♣'), ('J', '♥'), ('Q', '♦')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('Q', '♦'), ('J', '♥'), ('10', '♣')])
    
    def test_sort_same_rank_different_suits(self):
        """测试相同牌面数值不同花色的排序"""
        # 相同牌面数值不同花色的牌应该按花色从大到小排序
        hand = [('A', '♣'), ('A', '♠'), ('A', '♥')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♠'), ('A', '♣')])
        
        hand = [('K', '♦'), ('K', '♥'), ('K', '♣')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('K', '♥'), ('K', '♦'), ('K', '♣')])
    
    def test_sort_mixed_pairs_and_singles(self):
        """测试混合对子和单牌的排序"""
        # 混合对子和单牌的排序
        hand = [('A', '♥'), ('K', '♦'), ('K', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('K', '♦'), ('K', '♠'), ('A', '♥')])
        
        hand = [('A', '♥'), ('A', '♦'), ('K', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♦'), ('K', '♠')])
    
    def test_sort_with_duplicates(self):
        """测试有重复牌的排序"""
        # 有重复牌的排序
        hand = [('A', '♥'), ('A', '♥'), ('K', '♠')]
        sorted_hand = get_sorted_hand(hand)
        self.assertEqual(sorted_hand, [('A', '♥'), ('A', '♥'), ('K', '♠')])
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 空手牌
        with self.assertRaises(Exception):
            get_sorted_hand([])
        
        # 手牌数量不正确
        with self.assertRaises(Exception):
            get_sorted_hand([('A', '♥'), ('K', '♦')])
        
        with self.assertRaises(Exception):
            get_sorted_hand([('A', '♥'), ('K', '♦'), ('Q', '♠'), ('J', '♥')])

if __name__ == '__main__':
    unittest.main()