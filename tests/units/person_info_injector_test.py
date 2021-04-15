import os
import re
import sys
import random
import unittest

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/../../src')

from modelmock.injectors import PersonInfoInjector
from modelmock.injectors import personal_lookup

FIELD_NAMES = ['gender', 'fullname', 'email', 'phone']


class PersonInfoInjectorTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(PersonInfoInjectorTest, self).__init__(*args, **kwargs)
        self.__injector = PersonInfoInjector(locale='vi_VN')

    def setUp(self):
        pass

    # check whether the name is valid
    def test_is_valid_name(self):
        for _ in range(10):
            data = self.__injector.inject({})
            name_components = data['fullname'].split(' ')
            self.assertTrue(len(name_components) >= 2)
            last, middle, first = name_components[0], ' '.join(name_components[1:-1]), name_components[-1]

            gender = data['gender']
            is_contain = lambda list_values, element: element == '' or element in list_values
            if gender == 'F':
                self.assertTrue(is_contain(personal_lookup.first_names_female, first))
                self.assertTrue(is_contain(personal_lookup.middle_name_female, middle))
            else:
                self.assertTrue(is_contain(personal_lookup.first_names_male, first))
                self.assertTrue(is_contain(personal_lookup.middle_name_male, middle))
            self.assertTrue(is_contain(personal_lookup.last_names, last))

    # check whether the email is valid
    def test_is_valid_email(self):
        for _ in range(10):
            data = self.__injector.inject({})
            email = data['email']

            pattern = '^[\\w\\.-]+@' + '(' + '|'.join(domain for domain in personal_lookup.free_email_domains) + ')$'
            self.assertEqual(re.search(pattern=pattern, string=email).string, email)

    # check whether the phone number is valid
    def test_is_valid_phone_number(self):
        for _ in range(10):
            data = self.__injector.inject({})
            phone_number = data['phone']

            pattern = '^(' + '|'.join(
                ('\\' if i.startswith('+') else '') + i for i in personal_lookup.phone) + ')\\d{8}$'
            # pattern = '^('+'|'.join(i if not i.startswith('+') else '\\' + i for i in personal_lookup.phone)+')\\d{8}$'
            self.assertEqual(re.search(pattern=pattern, string=phone_number).string, phone_number)

    # check whether non-iterable data has full of person informations
    def test_noniterable_data_has_full_fields(self):
        for _ in range(10):
            data = self.__injector.inject({})
            for field_name in FIELD_NAMES:
                self.assertTrue(field_name in data)

    # check whether iterable data has full of person informations
    def test_iterable_data_has_full_fields(self):
        for _ in range(10):
            data = self.__injector.inject([{} for _ in range(random.randint(1, 10))])
            for elem in data:
                for field_name in FIELD_NAMES:
                    self.assertTrue(field_name in elem)


if __name__ == '__main__':
    unittest.main()
