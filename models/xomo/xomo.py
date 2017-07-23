from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import random
from collections import OrderedDict
from utils.lib import O
from cocomo import Cocomo
from utils.lib import MAXIMIZE, MINIMIZE


def uniform(low, high):
  return random.uniform(low, high)


class Component(O):
  """
  All components
  should extend this class
  """
  id = 0

  def __init__(self, **kwargs):
    O.__init__(self, **kwargs)
    self.id = Component.id
    Component.id += 1

  def __hash__(self):
    if not self.id:
      return 0
    return hash(self.id)

  def __eq__(self, other):
    if not self.id or not other.id:
      return False
    return self.id == other.id


class Decision(O):
  """
  Decision of the model
  """
  def __init__(self, name, low, high):
    self.name = name
    self.low = low
    self.high = high
    O.__init__(self)

  def norm(self, val):
    return (val - self.low) / (self.high - self.low)

  def de_norm(self, val):
    return self.low + val * (self.high - self.low)


class Objective(O):
  """
  Objective of the model
  """
  def __init__(self, name, direction, low, high):
    self.name = name
    self.direction = direction
    self.low = low,
    self.high = high
    O.__init__(self)


class Model(O):
  def __init__(self):
    O.__init__(self)
    self.name = "XOMO"
    self._cocomo = Cocomo()
    self._max_size = sys.maxint
    self.names, lows, highs = [], [], []
    self.decisions = OrderedDict()
    for one in self._cocomo.about():
      self.names.append(one.txt)
      lows.append(one.min)
      highs.append(one.max)
    for name, low, up in zip(self.names, lows, highs):
      d = Decision(name, low, up)
      self.decisions[d.name] = d
    objs = [Objective("effort", MINIMIZE, 0, 43000),
            Objective("months", MINIMIZE, 0, 120),
            Objective("defects", MINIMIZE, 0, 1180000),
            Objective("risk", MINIMIZE, 0, 17)]
    self.objectives = OrderedDict()
    for obj in objs:
      self.objectives[obj.name] = obj

  def initialize(self):
    pass

  def generate(self):
    solutions = OrderedDict()
    for name, decision in self.decisions.items():
      solutions[name] = uniform(decision.low, decision.high)
    return solutions

  def populate(self, size):
    population = []
    while len(population) < size:
      one = self.generate()
      if one not in population:
        population.append(one)
    return population

  def get_max_size(self):
    return self._max_size

  def evaluate_constraints(self, solution):
    return True, 0

  def evaluate(self, solution):
    assert len(solution) == len(self.decisions)
    evaluated = OrderedDict()
    for name, val in zip(self.objectives.keys(), self._cocomo.xys(solution)):
      evaluated[name] = val
    return evaluated

  def bdom(self, obj1, obj2):
    """
    Binary Domination
    :param obj1: Objective 1
    :param obj2: Objective 2
    :return: Check objective 1 dominates objective 2
    """
    at_least = False
    for i in self.objectives.keys():
      a, b = obj1[i], obj2[i]
      if self.objectives[i].direction.better(a, b):
        at_least = True
      elif a == b:
        continue
      else:
        return False
    return at_least

  def better(self, obj1, obj2):
    if self.bdom(obj1, obj2):
      return 1
    elif self.bdom(obj2, obj1):
      return 2
    return 0

  def test(self):
    self.initialize()
    solutions = self.populate(10)
    for sol in solutions:
      evals = self.evaluate(sol)
      arr = [(self.objectives[key].name, val) for key, val in evals.items()]
      print(arr)


def _main():
  xomo = Model()
  xomo.test()


if __name__ == "__main__":
  _main()
