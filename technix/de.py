from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from utils.lib import O
import random
from collections import OrderedDict
from utils.stats import Statistics
import time


def default():
  """
  Default settings.
  :return:
  """
  return O(
      gens=10,
      candidates=20,
      f=0.75,
      cr=0.3,
      seed=1,
      binary=True,
      dominates="bdom",
      cdom_delta=0.01,
      early_termination=True,
  )


def seed(val=None):
  random.seed(val)


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
    self.settings = default().update(**settings)
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

  def mutate(self, point, population):
    """
    Mutate point against the population
    :param point: Point to be mutated
    :param population: Population to refer
    :return: Mutated point
    """
    # TODO: Implement DE binary mutation
    return self.mutate_random(point, population)

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


  def run(self):
    """
    DE runner
    :return:
    """
    # settings = self.settings
    stat = Statistics()
    start = time.time()
    self.model.initialize()
    population = self.populate(self.settings.candidates)
    stat.insert(population)
    [point.evaluate(self.model) for point in population]
    for i in range(self.settings.gens):
      print("Generation : %d " % (i + 1))
      clones = population[:]
      for point in population:
        original_obj = point.evaluate(self.model)
        mutant = self.mutate(point, clones)
        mutated_obj = mutant.evaluate(self.model)
        if self.dominates(mutated_obj, original_obj) and (mutant not in self.global_set):
          clones.remove(point)
          clones.append(mutant)
          self.global_set.add(mutant)
      population = clones
      stat.insert(population)
    stat.runtime = time.time() - start
    return stat


def _main():
  from language.parser import Parser
  mdl = Parser.from_file("models/AOWS.str")
  de = DE(mdl)
  de.run()

if __name__ == "__main__":
  _main()
