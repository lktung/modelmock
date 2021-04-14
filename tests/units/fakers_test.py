#!/usr/bin/env python3
import random
import unittest
import os, sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/../../src')

from modelmock.fakers import generate_agents, generate_contracts, generate_purchases


class generate_agents_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_default_subpath_ok(self):
        _agents = list(generate_agents(6, [
            {'level': 'A', 'count': 1},
            {'level': 'B', 'count': 2},
            {'level': 'C'}
        ]))
        self.assertEqual(len(_agents), 6)

        _counts = dict(A=0, B=0, C=0)
        for _agent in _agents:
            _counts[_agent['record']['level']] = _counts[_agent['record']['level']] + 1

        self.assertEqual(_counts, dict(A=1, B=2, C=3))

    def test_without_subpath_ok(self):
        _agents = list(generate_agents(6, [
            {'level': 'A', 'count': 2},
            {'level': 'B', 'count': 4},
            {'level': 'C'}
        ], subpath=None))
        self.assertEqual(len(_agents), 6)

        _counts = dict(A=0, B=0, C=0)
        for _agent in _agents:
            _counts[_agent['level']] = _counts[_agent['level']] + 1

        self.assertEqual(_counts, dict(A=2, B=4, C=0))


class generate_purchases_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_default_ok(self):
        _record = generate_purchases(10, 50, 2, 100)
        self.assertEqual(len(list(_record)), 50)

    def test_generate_purchases_with_value_of_totalcontracts_less_than_double_value_of_totalagents(self):
        errmsgs = 'variance must be greater than 0'
        check_num = 0

        for i in range(5):
            check_num += 1
            with self.assertRaises(Exception) as context:
                generate_purchases(10, random.randint(0, 19), 100, 10000000)
                self.assertEqual(errmsgs, context.exception)

        self.assertEqual(check_num, 5)

    def test_length_of_purchases_ids(self):
        _records = list(generate_purchases(10, 20, 50, 100000))
        _nameId = lambda x: 'id' if x == 'purchase' else 'agent_id'

        for name in ['purchase', 'agent']:
            check_num = 0
            check_bool = True

            for _record in _records:
                check_num += 1
                if not 12 == len(_record[_nameId(name)]):
                    check_bool = False

            self.assertEqual(check_bool, True)
            self.assertEqual(check_num, 20)


class generate_contracts_test(unittest.TestCase):

    def setUp(self):
        pass

    def test_defaul_ok(self):
        _records = generate_contracts(6, 100, 1000)
        self.assertEqual(len(list(_records)), 6)

    def test_value_of_contract_price_less_than_2(self):
        errclass = lambda n: \
            AssertionError if n == 0 else ValueError
        errmsgs = lambda n: \
            '[contract_price] must be a positive integer' if n == 0 else \
                'variance must be greater than 0'
        for num in [0, 1]:
            check_num = 0
            for i in range(5):
                check_num += 1
                with self.assertRaises(errclass(num)) as context:
                    print(errmsgs(num))
                    generate_contracts(8, num, 1000)
                    self.assertEqual(errmsgs(num), context.exception)
            self.assertEqual(check_num, 5)

    def test_sum_fyps_equal_multiple_totalagents_and_contract_price(self):
        _records = generate_contracts(10, 100, 1000)
        _total = sum([record['fyp'] for record in list(_records)])
        self.assertEqual(_total, 10 * 100 * 1000)

    def test_value_type(self):
        _records = generate_contracts(6, 9, 10000)
        _check = True

        for record in _records:
            _fields = list(record)
            _fields_type = []

            for i in _fields:
                if 'type' in i:
                    _fields_type.append(i)

            for field in _fields_type:
                _check = False if record[field] > 3 else True

        self.assertEqual(True, _check)
