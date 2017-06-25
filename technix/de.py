from __future__ import print_function, division

import os
import sys

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from utils.lib import O
import random
from collections import OrderedDict
from utils.stats import Statistics
import time
from utils import plotter


def default():
  """
  Default settings.
  :return:
  """
  return O(
      gens=50,
      candidates=20,
      f=0.75,
      cr=0.3,
      seed=1,
      binary=True,
      dominates="bdom",  # bdom or cdom
      cdom_delta=0.01,
      mutate="binary",  # binary or random
      early_termination=True,
      verbose=True
  )


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


class DE(O):
  def __init__(self, model, **settings):
    """
    Initialize a DE optimizer
    :param model: Model to be optimized
    :param settings: Settings for the optimizer
    """
    O.__init__(self)
    self.model = model
    if self.model.get_max_size() < 50:
      raise Exception("Cannot run DE since # possible decisions less than 50")
    self.settings = default().update(**settings)
    self.settings.candidates = int(min(self.settings.candidates, 0.5 * self.model.get_max_size() / self.settings.gens))
    seed(self.settings.seed)
    if self.settings.dominates == "bdom":
      self.dominates = self.bdom
    else:
      # TODO: Insert cdom
      self.dominates = self.bdom
    self.global_set = set()
    self.max_size = None

  def bdom(self, obj1, obj2):
    """
    Binary Domination
    :param obj1: Objective 1
    :param obj2: Objective 2
    :return: Check objective 1 dominates objective 2
    """
    at_least = False
    for i in self.model.objectives.keys():
      a, b = obj1[i], obj2[i]
      if self.model.objectives[i].direction.better(a, b):
        at_least = True
      elif a == b:
        continue
      else:
        return False
    return at_least

  def populate(self, size):
    self.max_size = self.model.get_max_size() if self.max_size is None else self.max_size
    if size > self.max_size:
      size = self.max_size
    population = set()
    while len(population) < size:
      point = Point(self.model.generate())
      if point not in population:
        population.add(point)
        self.global_set.add(point)
    return list(population)

  @staticmethod
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

  def mutate(self, point, population):
    """
    Mutate point against the population
    :param point: Point to be mutated
    :param population: Population to refer
    :return: Mutated point
    """
    # TODO: Implement DE binary mutation
    if self.settings.mutate == "random":
      return self.mutate_random(point, population)
    elif self.settings.mutate == "binary":
      return self.mutate_binary(point, population)
    else:
      raise Exception("Invalid mutation setting %s" % self.settings.mutate)

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
    two, three, four = DE.three_others(point, population)
    random_key = choice(self.model.decisions.keys())
    mutant_decisions = OrderedDict()
    for key in self.model.decisions.keys():
      r = random.random()
      if r < self.settings.cr or key == random_key:
        mutant_decisions[key] = random.choice([two.decisions[key], three.decisions[key], four.decisions[key]])
      else:
        mutant_decisions[key] = point.decisions[key]
    return Point(mutant_decisions)

  def run(self):
    """
    DE runner
    :return:
    """
    # settings = self.settings
    self.print("Optimizing using DE ... ")
    stat = Statistics()
    start = time.time()
    self.model.initialize()
    population = self.populate(self.settings.candidates)
    stat.insert(population)
    [point.evaluate(self.model) for point in population]
    for i in range(self.settings.gens):
      self.print("Generation : %d ... " % (i + 1))
      clones = set(population[:])
      for point in population:
        original_obj = point.evaluate(self.model)
        mutant = self.mutate(point, population)
        mutated_obj = mutant.evaluate(self.model)
        if self.dominates(mutated_obj, original_obj) and (mutant not in self.global_set):
          clones.remove(point)
          clones.add(mutant)
          self.global_set.add(mutant)
      population = list(clones)
      stat.insert(population)
    stat.runtime = time.time() - start
    return stat

  def print(self, message):
    if self.settings.verbose:
      print(message)


def _pareto_test(model_name, **settings):
  from language.parser import Parser
  mdl = Parser.from_file("models/%s.str" % model_name)
  obj_ids = mdl.objectives.keys()
  de = DE(mdl, **settings)
  stat = de.run()
  gens_obj_start = stat.get_objectives(0, obj_ids)
  gens_obj_end = stat.get_objectives(-1, obj_ids)
  plotter.plot_pareto([gens_obj_start, gens_obj_end], ['red', 'green'], ['x', 'o'],
                      ['first', 'last'], obj_ids[0], obj_ids[1], 'Pareto Front',
                      'figs/%s_pareto.png' % model_name)


if __name__ == "__main__":
  _pareto_test("SAS", candidates=10)
  _pareto_test("AOWS")
  _pareto_test("ECS")
