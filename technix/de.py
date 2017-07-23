from __future__ import print_function, division

import os
import sys

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from utils.lib import O
from utils.stats import Statistics
import time
from technix.tech_utils import Point, seed
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


class DE(O):
  def __init__(self, model, mutator, **settings):
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
    self.mutator = mutator(self.model, cr=self.settings.cr, f=self.settings.f)
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
    if self.settings.mutate == "random":
      return self.mutator.mutate_random(point, population)
    elif self.settings.mutate == "binary":
      return self.mutator.mutate_binary(point, population)
    else:
      raise Exception("Invalid mutation setting %s" % self.settings.mutate)

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
    [point.evaluate(self.model) for point in population]
    stat.insert(population)
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


def _pareto_quirk_test(model_name, **settings):
  from language.parser import Parser
  from language.mutator import Mutator
  mdl = Parser.from_file("models/quirk/%s.str" % model_name)
  obj_ids = mdl.objectives.keys()
  de = DE(mdl, Mutator, **settings)
  stat = de.run()
  gens_obj_start = stat.get_objectives(0, obj_ids)
  gens_obj_end = stat.get_objectives(-1, obj_ids)
  plotter.plot_pareto([gens_obj_start, gens_obj_end], ['red', 'green'], ['x', 'o'],
                      ['first', 'last'], obj_ids[0], obj_ids[1], 'Pareto Front',
                      'results/pareto/%s_pareto.png' % model_name)


def _pareto_xomo_test():
  from models.xomo.xomo import Model
  from models.xomo.mutator import Mutator
  mdl = Model()
  obj_ids = mdl.objectives.keys()
  de = DE(mdl, Mutator)
  stat = de.run()
  gens_obj_start = stat.get_objectives(0, obj_ids)
  gens_obj_end = stat.get_objectives(-1, obj_ids)
  plotter.plot_pareto([gens_obj_start, gens_obj_end], ['red', 'green'], ['x', 'o'],
                      ['first', 'last'], obj_ids[0], obj_ids[1], 'Pareto Front',
                      'results/pareto/%s_pareto.png' % mdl.name)


if __name__ == "__main__":
  _pareto_xomo_test()
  exit()
  _pareto_quirk_test("SAS", candidates=10)
  _pareto_quirk_test("AOWS")
  _pareto_quirk_test("ECS")
