#!/usr/bin/env python3

import random
from modelmock.abc import AbstractSeqFaker
from modelmock.utils import (
  array_random_split,
  chunkify,
  number_to_id,
  generate_ids,
  generate_uuids,
  generatorify,
  shuffle_nodes,
  list_to_dict,
  flatten_sub_dict,
  flatten_sub_list,
  random_fixed_sum_array,
  wrap_nodes,
)
from modelmock.user_info import Generator as UserGenerator


class IdentifiableSeqFaker(AbstractSeqFaker):

  def __init__(self, total, id_method=None, id_prefix='A', id_padding=4, id_shuffle=True, **kwargs):
    assert isinstance(total, int) and total > 0, '[total] must be a positive integer'
    self.__total = total

    assert id_method is None or isinstance(id_method, str), '[id_method] must be a string (incr, uuid)'
    self.__id_method = 'incr' if id_method is None else id_method

    assert isinstance(id_prefix, str) and len(id_prefix) > 0, '[id_prefix] must be a non-empty string'
    self.__id_prefix = id_prefix

    assert isinstance(id_padding, int) and id_padding > 0, '[id_padding] must be a positive integer'
    self.__id_padding = id_padding

    if isinstance(id_shuffle, str):
      self.__id_shuffle = id_shuffle.lower() in ['yes', 'true', '1']
    else:
      self.__id_shuffle = bool(id_shuffle)

    self.__ids = None

  @property
  def total(self):
    return self.__total

  @property
  def ids(self):
    if self.__ids is None:
      if self.__id_method == 'uuid':
        self.__ids = generate_uuids(self.total)
      else:
        self.__ids = generate_ids(self.total, prefix=self.__id_prefix, padding=self.__id_padding, shuffle=self.__id_shuffle)
    return self.__ids


# [BEGIN AgentsFaker]

class AgentsFaker(IdentifiableSeqFaker):

  def __init__(self, total_agents, level_mappings, id_method=None, id_prefix='A', id_padding=4, id_shuffle=True, subpath='record', locale='en_US', **kwargs):
    assert level_mappings is None or isinstance(level_mappings, list), '[level_mappings] must be a list or None'
    self.__level_mappings = level_mappings if level_mappings is not None else []

    assert subpath is None or isinstance(subpath, str) and len(subpath) > 0, '[subpath] must be a non-empty string or None'
    self.__subpath = subpath

    self.__user_info_faker = UserGenerator(locale=locale)

    IdentifiableSeqFaker.__init__(self, total_agents, id_method, id_prefix, id_padding, id_shuffle)

  @property
  def records(self):
    return self._generate_agents(self.ids, self.__level_mappings, self.__user_info_faker, subpath=self.__subpath)

  @classmethod
  def _generate_agents(cls, agent_ids, level_mappings, user_info_faker, subpath='record'):
    _records = user_info_faker.inject_user_info(
      flatten_sub_dict(
        generatorify(
          cls._expand_tree_path(
            cls._assign_levels(None,
              indices=list(agent_ids),
              levels=level_mappings)
          )
        )
      )
    )
    if isinstance(subpath, str):
      return map(lambda item: { subpath: item }, _records)
    else:
      return _records

  @classmethod
  def _expand_tree_path(cls, nodes, index_name='index', level_name='level', super_name='super', prior_list='refs'):
    _lkup = list_to_dict(nodes)
    for node in nodes:
      node[prior_list] = dict()
      node[prior_list][node[level_name]] = node[index_name]

      _super_id = node[super_name]
      if _super_id is None:
        continue

      _super = _lkup[_super_id]
      _super_refs = _super[prior_list]

      for ref_label in _super_refs.keys():
        node[prior_list][ref_label] = _super_refs[ref_label]

    return nodes

  @classmethod
  def _assign_levels(cls, super_id, indices, levels):
    if not isinstance(indices, list):
      raise TypeError('indices is invalid')

    ret = []

    if not isinstance(indices, list) or len(indices) == 0:
      return ret
    if isinstance(levels, list) and len(levels) > 0:
      current = levels[0]
      levels = levels[1:]
      if len(levels) == 0:
        for i in indices:
          item = dict(
            level=current['level'],
            index=i,
            super=super_id
          )
          ret.append(item)
      else:
        # determines the number of branches
        if 'count' in current:
          _count = current['count']
        else:
          _min = current['min'] if 'min' in current else 0
          _max = current['max'] if 'max' in current else len(indices)
          _count = random.randint(_min, _max)
        # no any branch of this level
        if _count == 0:
          return cls._assign_levels(super_id, indices, levels)
        # split the children
        group_len = _count if _count < len(indices) else len(indices)
        child_group = array_random_split(indices, group_len)
        for child in child_group:
          first_index = child[0]
          subchild = child[1:]
          ret.append(dict(
            level=current['level'],
            index=first_index,
            super=super_id
          ))
          ret = ret + cls._assign_levels(first_index, subchild, levels = levels)
    return ret

# [END AgentsFaker]


# [BEGIN CandidatesFaker]

class CandidatesFaker(IdentifiableSeqFaker):

  def __init__(self, total_candidates, id_method=None, id_prefix='CAN', id_padding=10, id_shuffle=False, locale='en', **kwargs):
    IdentifiableSeqFaker.__init__(self, total_candidates, id_method, id_prefix, id_padding, id_shuffle)
    self.__user_info_faker = UserGenerator(locale=locale)

  @property
  def records(self):
    return self.__user_info_faker.inject_user_info(wrap_nodes(self.ids, field_name='id'))

# [END CandidatesFaker]


# [BEGIN PromotionCodeFaker]

class PromotionCodeFaker(AbstractSeqFaker):

  def __init__(self, total_codes, spread_limit=5, **kwargs):
    self.__total_codes = total_codes
    assert isinstance(self.__total_codes, int) and self.__total_codes > 0,\
        'total_codes must be a positive integer'

    self.__spread_limit = spread_limit
    assert isinstance(self.__spread_limit, int) and self.__spread_limit > 0 and self.__spread_limit <= self.__total_codes,\
        'spread_limit must be a positive integer'

    self.__referral_targets = dict()

  @property
  def total(self):
    return self.__total_codes

  @property
  def records(self):
    _procodes = generate_ids(self.__total_codes, prefix='PC', padding=10)
    for _procode in _procodes:
      _referral_code = self.__pick_a_referral_code()
      if _referral_code is not None:
        self.__referral_targets[_referral_code].append(_procode)
      self.__referral_targets[_procode] = []
      yield dict(promotion_code=_procode, referral_code=_referral_code)

  def __pick_a_referral_code(self):
    _referral_code = None
    _avail_codes = list(filter(lambda _key: (len(self.__referral_targets[_key]) < self.__spread_limit), self.__referral_targets.keys()))
    if len(_avail_codes) > 2:
      _referral_code = _avail_codes[random.randint(0, len(_avail_codes) - 1)]
    return _referral_code

# [END PromotionCodeFaker]


# [BEGIN ContractsFaker]

class ContractsFaker(AbstractSeqFaker):

  def __init__(self, total_contracts, contract_price, multiplier=1, id_prefix='CONTR', id_padding=6, id_shuffle=False, flatten=True, **kwargs):
    self.__total_contracts = total_contracts
    assert isinstance(self.__total_contracts, int) and self.__total_contracts > 0,\
        'total_contracts must be a positive integer'

    self.__contract_price = contract_price
    assert isinstance(self.__contract_price, int) and self.__contract_price > 0,\
        'contract_price must be a positive integer'

    self.__multiplier = multiplier
    self.__id_prefix = id_prefix
    self.__id_padding = id_padding
    self.__id_shuffle = id_shuffle
    self.__flatten = flatten

  @property
  def total(self):
    return self.__total_contracts

  @property
  def records(self):
    return self.__generate_contracts(self.__total_contracts, self.__contract_price,
        multiplier=self.__multiplier,
        id_prefix=self.__id_prefix,
        id_padding=self.__id_padding,
        flatten=self.__flatten)

  def __generate_contracts(self, total_contracts, contract_price, multiplier, id_prefix='CONTR', id_padding=6, flatten=True):
    # estimate the revenue ~ price * total
    _revenue = contract_price * total_contracts

    # randomize the prices (length: total_contracts)
    _prices = random_fixed_sum_array(_revenue, total_contracts)

    # common kwargs
    _args_tail = dict(multiplier=multiplier, id_prefix=id_prefix, id_padding=id_padding, flatten=flatten)

    # generate each contracts
    return map(lambda idx, price: self.__generate_contract(idx, price, **_args_tail), range(total_contracts), _prices)


  def __generate_contract(self, idx, price, multiplier, id_prefix='C', id_padding=6, max_extras=5, flatten=True, extra_generator=None):
      num_extras = random.randint(1, max_extras)
      if extra_generator is None:
        extras = []
        for idx_extras in range(num_extras):
          extras.append(dict(
            fare = random.randint(1,5) * multiplier,
            type = random.randint(1,3),
            duration = random.randint(1, 12),
          ))
      else:
        extras = map(extra_generator, range(num_extras))
      _contract = dict(id=number_to_id(idx, id_prefix, id_padding), fyp=price * multiplier, extras=extras)
      if flatten:
        return flatten_sub_list(_contract)
      return _contract

# [END ContractsFaker]


# [BEGIN PurchasesFaker]

class PurchasesFaker(AbstractSeqFaker):

  def __init__(self, agents_faker, contracts_faker, **kwargs):
    self.__agents_faker = agents_faker
    assert isinstance(self.__agents_faker, AgentsFaker), '[agents_faker] must be an instance of AgentsFaker type'

    self.__contracts_faker = contracts_faker
    assert isinstance(self.__contracts_faker, ContractsFaker), '[contracts_faker] must be an instance of ContractsFaker type'

  @property
  def total(self):
    return self.__contracts_faker.total

  @property
  def records(self):
    total_agents = self.__agents_faker.total
    total_contracts = self.__contracts_faker.total

    def assign_contract_to_agent(contract, agent_id):
      contract['agent_id'] = agent_id
      return contract

    def select_agent_for_contract(total_contracts, total_agents):
      # assign the contracts to agents
      num_contracts_per_agents = random_fixed_sum_array(total_contracts, total_agents)

      for i, agent_id in enumerate(self.__agents_faker.ids):
        for j in range(num_contracts_per_agents[i]):
          yield agent_id

    return map(assign_contract_to_agent, self.__contracts_faker.records, select_agent_for_contract(total_contracts, total_agents))

# [END PurchasesFaker]


def generate_agents(total, level_mappings, subpath='record', id_prefix='A', id_padding=4, locale='en'):
  faker = AgentsFaker(total, level_mappings,
      subpath=subpath,
      id_prefix=id_prefix,
      id_padding=id_padding,
      locale=locale)
  return faker.records


def generate_contracts(total_contracts, contract_price, multiplier, **kwargs):
  myargs = dict(total_contracts=total_contracts, contract_price=contract_price, multiplier=multiplier)
  myargs.update(kwargs)
  return ContractsFaker(**myargs).records


def generate_purchases(total_agents, total_contracts, contract_price, multiplier,
    agent_id_method=None, agent_id_prefix='CONTR', agent_id_padding=6, agent_id_shuffle=True,
    contract_id_method=None, contract_id_prefix='CONTR', contract_id_padding=6, contract_id_shuffle=True,
    flatten=True, chunky=None):

  agents_faker = AgentsFaker(total_agents, [],
      id_method=agent_id_method,
      id_prefix=agent_id_prefix,
      id_padding=agent_id_padding,
      id_shuffle=agent_id_shuffle)

  contracts_faker = ContractsFaker(total_contracts, contract_price, multiplier,
      id_method=contract_id_method,
      id_prefix=contract_id_prefix,
      id_padding=contract_id_padding,
      id_shuffle=contract_id_shuffle,
      flatten=flatten)

  return PurchasesFaker(agents_faker, contracts_faker).records
