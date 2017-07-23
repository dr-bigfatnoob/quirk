from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import random
from collections import OrderedDict
import numpy as np
from utils.lib import O
from technix.tech_utils import Point, three_others, choice, StarPoint


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
    two, three, four = three_others(point, population)
    random_key = choice(self.model.decisions.keys())
    mutant_decisions = OrderedDict()
    for key in self.model.decisions.keys():
      r = random.random()
      if r < self.settings.cr or key == random_key:
        mutant_decisions[key] = random.choice([two.decisions[key], three.decisions[key], four.decisions[key]])
      else:
        mutant_decisions[key] = point.decisions[key]
    return Point(mutant_decisions)

  def generate(self, presets=None, size=10):
    pop = []
    presets = {} if presets is None else presets
    while len(pop) < size:
      solutions = OrderedDict()
      model = self.model
      if model.decision_map:
        ref = {key: np.random.choice(vals) for key, vals in model.decision_map.items()}
        for key, decision in model.decisions.items():
          if decision.key in presets:
            solutions[key] = decision.options[presets[decision.key]].id
          else:
            solutions[key] = decision.options[ref[decision.key]].id
      else:
        for key, decision in model.decisions.items():
          if key in presets:
            solutions[key] = decision.options[presets[key]].id
          else:
            solutions[key] = np.random.choice(decision.options.values()).id
      pop.append(Point(solutions))
    return pop

  def decision_ranker(self, best, rest):
    best_size = len(best)
    rest_size = len(rest)
    p_best = best_size / (best_size + rest_size)
    p_rest = rest_size / (best_size + rest_size)
    decisions = []
    best_sols = [self.model.get_solution(sol.decisions) for sol in best]
    rest_sols = [self.model.get_solution(sol.decisions) for sol in rest]
    for d_id, values in self.model.get_decisions().items():
      # Implement Ranks
      best_scores = {v: 0 for v in values}
      for point in best_sols:
        # best_scores[self.model.nodes[point.decisions[d_id]].label] += 1
        best_scores[point[d_id]] += 1
      rest_scores = {v: 0 for v in values}
      for point in rest_sols:
        rest_scores[point[d_id]] += 1
      for key in best_scores.keys():
        l_best = best_scores[key] * p_best / len(best_sols)
        l_rest = rest_scores[key] * p_rest / len(rest_sols)
        sup = 0 if l_best == l_rest == 0 else l_best ** 2 / (l_best + l_rest)
        decisions.append(StarPoint(support=sup,
                                   value=key,
                                   name=d_id))
    decisions.sort(key=lambda x: x.support, reverse=True)
    ranked, aux = [], set()
    for dec in decisions:
      if dec.name not in aux:
        ranked.append(dec)
        aux.add(dec.name)
    assert len(ranked) == len(self.model.get_decisions()), "Mismatch after sorting support"
    return ranked
