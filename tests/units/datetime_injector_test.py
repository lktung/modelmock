import datetime
import os
import random
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/../../src')

from modelmock.injectors import DateTimeInjector, DateTimeRandomizer

DELTA_UNITS = ['weeks', 'days', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds']


class DatetimeInjectorTest(unittest.TestCase):
    def setUp(self) -> None:
        num_injectors = random.randint(1, 50)
        self.__steps = list(range(num_injectors))
        self.__field_names = [str(i).zfill(6) for i in self.__steps]

        descriptors = []
        for i in random.sample(self.__steps, num_injectors):
            descriptors.append({'field_name': self.__field_names[i],
                                'delta_unit': 'days',
                                'delta_min': 0,
                                'delta_max': 5,
                                'format': '%d/%m/%Y',
                                'step': i})
        self.__datetime_injector = DateTimeInjector(10, descriptors=descriptors)

    # checking whether the non-iterable data has full of events
    def test_noniterable_data_has_full_fields(self):
        for _ in range(10):
            data = self.__datetime_injector.inject(data={})
            for field_name in self.__field_names:
                self.assertTrue(field_name in data)

    # checking whether the iterable data has full of events
    def test_iterable_data_has_full_fields(self):
        for _ in range(10):
            data = self.__datetime_injector.inject(data=[{} for _ in range(random.randint(1, 20))])
            for field_name in self.__field_names:
                for elem in data:
                    self.assertTrue(field_name in elem)

    # checking whether all events is in order
    def test_all_events_in_order(self):
        data = self.__datetime_injector.inject(data={})
        for before_field, after_field in zip(self.__field_names[:-1], self.__field_names[1:]):
            self.assertTrue(
                datetime.strptime(data[before_field], '%d/%m/%Y') <= datetime.strptime(data[after_field], '%d/%m/%Y')
            )


class DatetimeRandomizerTest(unittest.TestCase):
    # the random_time must be in the range between current_time+min_delta and current_time+max_delta
    def test_random_time_is_in_delta(self):
        for _ in range(10):
            min_delta, max_delta, unit_delta = self.__create_random_deltas()
            min_time, max_time, random_time = self.__create_time_points(
                min_delta=min_delta,
                max_delta=max_delta,
                unit_delta=unit_delta
            )
            self.assertTrue(min_time <= random_time <= max_time)

    # when min_delta=max_delta: the random_time must be equal to current_time+min_delta
    def test_zero_delta(self):
        for _ in range(10):
            min_delta, _, unit_delta = self.__create_random_deltas()
            min_time, _, random_time = self.__create_time_points(
                min_delta=min_delta,
                max_delta=min_delta,
                unit_delta=unit_delta
            )
            self.assertEqual(random_time, min_time)

    def __create_time_points(self, min_delta, max_delta, unit_delta):
        current_time = datetime.now()
        min_time = current_time + timedelta(**{unit_delta: min_delta})
        max_time = current_time + timedelta(**{unit_delta: max_delta})

        randomizer = self.__create_randomizer(min_delta=min_delta,
                                              max_delta=max_delta,
                                              unit_delta=unit_delta)
        random_time = randomizer.next(current_time)

        return min_time, max_time, random_time

    def __create_randomizer(self, min_delta, max_delta, unit_delta):
        return DateTimeRandomizer(total=10,
                                  field_name='created_time',
                                  step=0,
                                  offset=0,
                                  offset_unit='days',
                                  delta_min=min_delta,
                                  delta_max=max_delta,
                                  delta_unit=unit_delta,
                                  format='%d/%m/%Y')

    def __create_random_deltas(self):
        min_delta = random.randint(0, 999)
        max_delta = random.randint(min_delta, 1000)
        unit_delta = random.choice(DELTA_UNITS)
        return min_delta, max_delta, unit_delta


if __name__ == '__main__':
    datetime_randomizer_suite = unittest.TestLoader().loadTestsFromTestCase(DatetimeRandomizerTest)
    datetime_injector_suite = unittest.TestLoader().loadTestsFromTestCase(DatetimeInjectorTest)

    suite = unittest.TestSuite([datetime_randomizer_suite, datetime_injector_suite])
    unittest.TextTestRunner(verbosity=2).run(suite)
