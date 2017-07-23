from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import random
from collections import OrderedDict
from utils.lib import O
from technix.tech_utils import Point, three_others, choice, StarPoint
import numpy as np


def default():
  """
  Default settings.
  :return:
  """
  return O(
      f=0.75,
      cr=0.3,
  )


class Mutator(O):
  def __init__(self, model, **settings):
    self.model = model
    self.settings = default().update(**settings)
    O.__init__(self)

  def mutate_random(self, point, population):
    """
    Just another random point
    :param point:
    :param population:
    :return:
    """
    other = Point(self.model.generate())
    other.evaluate(self.model)
    while other in population or other == point:
      other = Point(self.model.generate())
      other.evaluate(self.model)
    return other

  def mutate_binary(self, point, population):
    model = self.model
    two, three, four = three_others(point, population)
    random_key = choice(model.decisions.keys())
    mutant_decisions = OrderedDict()
    for key in model.decisions.keys():
      r = random.random()
      if r < self.settings.cr or key == random_key:
        mutant_decisions[key] = point.decisions[key]
      else:
        mutant_decisions[key] = min(
            max(point.decisions[key] + self.settings.f * (three.decisions[key] - two.decisions[key]),
                model.decisions[key].low),
            model.decisions[key].high)
    return Point(mutant_decisions)

  def generate(self, presets=None, size=10):
    pop = []
    presets = {} if presets is None else presets
    while len(pop) < size:
      solution = self.model.generate()
      for name, value in presets.items():
        solution[name] = value
      pop.append(Point(solution))
    return pop

  def decision_ranker(self, best, rest):
    best_size = len(best)
    rest_size = len(rest)
    p_best = best_size / (best_size + rest_size)
    p_rest = rest_size / (best_size + rest_size)
    decisions = []
    for d_name, decision in self.model.decisions.items():
      best_scores, rest_scores = [], []
      for point in best:
        best_scores.append(decision.norm(point.decisions[d_name]))
      for point in rest:
        rest_scores.append(decision.norm(point.decisions[d_name]))
      f_best = 1 / max(np.std(best_scores), 0.05)
      f_rest = 1 / np.std(rest_scores)
      l_best = f_best * p_best
      l_rest = f_rest * p_rest
      sup = 0 if l_best == l_rest == 0 else l_best ** 2 / (l_best + l_rest)
      decisions.append(StarPoint(support=sup,
                                 value=decision.de_norm(np.mean(best_scores)),
                                 name=d_name))
    decisions.sort(key=lambda x: x.support, reverse=True)
    assert len(decisions) == len(self.model.decisions)
    return decisions
