from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from utils.lib import O
import random
from collections import OrderedDict


def seed(val=None):
  random.seed(val)


def choice(lst):
  return random.choice(lst)


class Point(O):
  id = 0

  def __init__(self, decisions, objectives=None):
    """
    Point in the optimizer
    :param decisions: Ordered Dictionary of decisions
    :param objectives: Ordered Dictionary of objectives
    """
    O.__init__(self)
    Point.id += 1
    self.id = Point.id
    self.decisions = decisions
    self.objectives = objectives
    # Attributes for NSGA2
    self.dominating = 0
    self.dominated = []
    self.crowd_dist = 0

  def __hash__(self):
    """
    Hash Function
    :return:
    """
    decs = self.decisions.items() if type(self.decisions) == dict or type(self.decisions) == OrderedDict \
        else self.decisions
    objs = self.objectives.items() if type(self.objectives) == dict or type(self.objectives) == OrderedDict \
        else self.objectives
    hashed = hash(frozenset(decs))
    if objs is not None:
      hashed += hash(frozenset(objs))
    return hashed

  def __eq__(self, other):
    """
    Equality check
    :param other:
    :return:
    """
    return cmp(self.decisions, other.decisions) == 0 and self.objectives == other.objectives

  def evaluate(self, model):
    """
    Evaluate the objectives of the point
    :param model: Model against which evaluation is performed.
    :return:
    """
    if not self.objectives:
      self.objectives = model.evaluate(self.decisions)
    return self.objectives


def three_others(one, pop):
  """
  Return three other points from population
  :param one: Point not to consider
  :param pop: Population to look in
  :return: two, three, four
  """

  def one_other():
    while True:
      x = choice(pop)
      if x.id not in seen:
        seen.append(x.id)
        return x

  seen = [one.id]
  two = one_other()
  three = one_other()
  four = one_other()
  return two, three, four


class StarPoint(O):
  _id = 0

  def __init__(self, **params):
    self.id = self._id
    StarPoint._id += 1
    O.__init__(self, **params)

  def __hash__(self):
    return hash(self.id)
