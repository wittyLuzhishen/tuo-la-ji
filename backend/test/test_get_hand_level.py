# -*- coding: utf-8 -*-
"""
测试 get_hand_level 函数的测试用例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game_logic import get_hand_level
import unittest

class TestGetHandLevel(unittest.TestCase):
    """测试get_hand_level函数"""
    
    def test_three_of_a_kind(self):
        """测试豹子牌型"""
        # 豹子应该返回6
        hand = [('A', '♥'), ('A', '♦'), ('A', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 6)
        
        hand = [('K', '♥'), ('K', '♦'), ('K', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 6)
        
        hand = [('2', '♥'), ('2', '♦'), ('2', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 6)
    
    def test_straight_flush(self):
        """测试同花顺牌型"""
        # 同花顺应该返回5
        hand = [('A', '♥'), ('K', '♥'), ('Q', '♥')]
        level = get_hand_level(hand)
        self.assertEqual(level, 5)
        
        hand = [('K', '♦'), ('Q', '♦'), ('J', '♦')]
        level = get_hand_level(hand)
        self.assertEqual(level, 5)
        
        hand = [('10', '♠'), ('9', '♠'), ('8', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 5)
        
        # A23特殊顺子，当is_A23_as_straight=True时应该返回5
        hand = [('A', '♥'), ('2', '♥'), ('3', '♥')]
        level = get_hand_level(hand, is_A23_as_straight=True)
        self.assertEqual(level, 5)
        
        # A23不作为顺子时，应该返回3（金花）
        level = get_hand_level(hand, is_A23_as_straight=False)
        self.assertEqual(level, 3)
    
    def test_straight(self):
        """测试顺子牌型"""
        # 顺子应该返回4
        hand = [('A', '♥'), ('K', '♦'), ('Q', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 4)
        
        hand = [('K', '♥'), ('Q', '♦'), ('J', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 4)
        
        hand = [('10', '♥'), ('9', '♦'), ('8', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 4)
        
        # A23特殊顺子，当is_A23_as_straight=True时应该返回4
        hand = [('A', '♥'), ('2', '♦'), ('3', '♠')]
        level = get_hand_level(hand, is_A23_as_straight=True)
        self.assertEqual(level, 4)
        
        # A23不作为顺子时，应该返回1（单牌）
        level = get_hand_level(hand, is_A23_as_straight=False)
        self.assertEqual(level, 1)
    
    def test_flush(self):
        """测试金花牌型"""
        # 金花应该返回3
        hand = [('A', '♥'), ('K', '♥'), ('5', '♥')]
        level = get_hand_level(hand)
        self.assertEqual(level, 3)
        
        hand = [('K', '♦'), ('Q', '♦'), ('3', '♦')]
        level = get_hand_level(hand)
        self.assertEqual(level, 3)
        
        # A23不作为顺子时，同花A23应该返回3（金花）
        hand = [('A', '♥'), ('2', '♥'), ('3', '♥')]
        level = get_hand_level(hand, is_A23_as_straight=False)
        self.assertEqual(level, 3)
    
    def test_pair(self):
        """测试对子牌型"""
        # 对子应该返回2
        hand = [('A', '♥'), ('A', '♦'), ('5', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 2)
        
        hand = [('K', '♥'), ('K', '♦'), ('3', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 2)
        
        hand = [('2', '♥'), ('2', '♦'), ('5', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 2)
    
    def test_single_card(self):
        """测试单牌牌型"""
        # 单牌应该返回1
        hand = [('A', '♥'), ('K', '♦'), ('5', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 1)
        
        hand = [('K', '♥'), ('Q', '♦'), ('3', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 1)
        
        hand = [('2', '♥'), ('3', '♦'), ('5', '♠')]
        level = get_hand_level(hand)
        self.assertEqual(level, 1)
        
        # A23不作为顺子时，非同花A23应该返回1（单牌）
        hand = [('A', '♥'), ('2', '♦'), ('3', '♠')]
        level = get_hand_level(hand, is_A23_as_straight=False)
        self.assertEqual(level, 1)
    
    def test_different_suit_235(self):
        """测试非同花235牌型"""
        # 非同花235默认应该返回等级1
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♦'), ('5', '♠')]), 1)
        
        # 当有豹子且开启特殊规则时，非同花235应该返回等级7
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♦'), ('5', '♠')], has_three_of_a_kind_in_any_hand=True, isDiffentSuit235GreaterThanThreeOfAKind=True), 7)
        
        # 当有豹子但未开启特殊规则时，非同花235仍返回等级1
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♦'), ('5', '♠')], has_three_of_a_kind_in_any_hand=True, isDiffentSuit235GreaterThanThreeOfAKind=False), 1)
        
        # 当没有豹子时，无论是否开启特殊规则，非同花235都返回等级1
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♦'), ('5', '♠')], has_three_of_a_kind_in_any_hand=False, isDiffentSuit235GreaterThanThreeOfAKind=True), 1)
    
    def test_same_suit_235(self):
        """测试同花235牌型"""
        # 同花235应该返回3（金花），不受特殊规则影响
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♥'), ('5', '♥')]), 3)
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♥'), ('5', '♥')], has_three_of_a_kind_in_any_hand=True, isDiffentSuit235GreaterThanThreeOfAKind=True), 3)
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♥'), ('5', '♥')], has_three_of_a_kind_in_any_hand=True, isDiffentSuit235GreaterThanThreeOfAKind=False), 3)
        self.assertEqual(get_hand_level([('2', '♥'), ('3', '♥'), ('5', '♥')], has_three_of_a_kind_in_any_hand=False, isDiffentSuit235GreaterThanThreeOfAKind=True), 3)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 空手牌
        with self.assertRaises(Exception):
            get_hand_level([])
        
        # 手牌数量不正确
        with self.assertRaises(Exception):
            get_hand_level([('A', '♥'), ('K', '♦')])
        
        with self.assertRaises(Exception):
            get_hand_level([('A', '♥'), ('K', '♦'), ('Q', '♠'), ('J', '♥')])

if __name__ == '__main__':
    unittest.main()