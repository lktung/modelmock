#!/usr/bin/env python3

from datetime import datetime, timedelta
from modelmock.bases.abcs import AbstractInjector
from modelmock.utils import dictify, isiterable
import random

TIMEDELTA_UNITS = ['weeks', 'days', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds']

class DateTimeInjector(AbstractInjector):

  def __init__(self, total, descriptors, begin=None, **kwargs):
    assert isinstance(total, int) and total > 0, 'total must be a positive integer'
    self.__total = total

    assert isinstance(descriptors, list), 'descriptors must be a list'
    self.__randomizers = []
    for i, descriptor in enumerate(descriptors):
      self.__randomizers.append(DateTimeRandomizer(total, **descriptor))
    self.__randomizers = sorted(self.__randomizers, key= lambda r: r.step)

    self.__begin = datetime.now() if begin is None else begin
    assert isinstance(self.__begin, datetime), 'begin must be a datetime'

  def inject(self, data):
    if isinstance(data, dict):
      return self.__gen_times(data)
    elif isiterable(data):
      return self.__inject(data)
    else:
      return data

  def __inject(self, nodes):
      for node in nodes:
        yield self.__gen_times(node)

  def __gen_times(self, data):
    data = dictify(data)
    prev_step = 0
    current = self.__begin
    for randomizer in self.__randomizers:
      if randomizer.step > prev_step:
        current = randomizer.next(current)
        prev_step = randomizer.step
      else:
        current = randomizer.next(current)
      if randomizer.format is None:
        data[randomizer.name] = current
      else:
        data[randomizer.name] = current.strftime(randomizer.format)
    return data


class DateTimeRandomizer(object):

  def __init__(self, total, field_name, step=0, offset=0, offset_unit='days', delta_min=0, delta_max=0, delta_unit='days', format=None, **kwargs):
    self.__field_name = field_name

    assert isinstance(offset, int), '[offset] must be an integer'
    self.__offset = offset

    assert offset_unit in TIMEDELTA_UNITS, '[offset_unit] is empty or mismatched value'
    self.__offset_unit = offset_unit

    if self.__offset != 0:
      self.__compiled_offset = timedelta(**{self.__offset_unit: self.__offset})
    else:
      self.__compiled_offset = None

    assert isinstance(delta_min, int) and delta_min >= 0, '[delta_min] must be a non-negative integer'
    self.__delta_min = delta_min

    assert isinstance(delta_max, int) and delta_max >= 0, '[delta_max] must be a non-negative integer'
    self.__delta_max = delta_max

    assert delta_unit in TIMEDELTA_UNITS, '[delta_unit] is empty or mismatched value'
    self.__delta_unit = delta_unit

    assert isinstance(format, str), 'datetime [format] must be a string'
    self.__format = format

    assert isinstance(step, int) and step >= 0, '[step] must be a non-negative integer'
    self.__step = step

  @property
  def name(self):
    return self.__field_name

  @property
  def format(self):
    return self.__format

  @property
  def step(self):
    return self.__step

  def next(self, current = None):
    current = datetime.now() if current is None else current
    assert isinstance(current, datetime)

    if self.__compiled_offset is not None:
      current = current + self.__compiled_offset

    if 0 < self.__delta_max:
      _delta = 0

      if self.__delta_min == self.__delta_max:
        _delta = self.__delta_min
      elif self.__delta_min < self.__delta_max:
        _delta = random.randint(self.__delta_min, self.__delta_max)

      if _delta > 0:
        current = current + timedelta(**{ self.__delta_unit: _delta })

    return current
