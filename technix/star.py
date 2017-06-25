from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils.lib import O
from technix.de import DE
from technix import nsga

__author__ = "bigfatnoob"


def default():
  return O(
      k1=10,
      k2=100,
      best_percent=33,
      gen_step=2
  )


class Star(O):
  def __init__(self, model, **settings):
    O.__init__(self)
    self.model = model
    self.settings = default().update(**settings)
    self.de = DE(model, gens=self.settings.k1)

  def sample(self):
    stat = self.de.run()
    population = set()
    for point in stat.generations[0] + stat.generations[-1]:
      population.add(point)
    best = set(nsga.select(self.model, list(population), int(len(population) / 4)))
    rest = population - best
    return best, rest

  # TODO Implement Ranks
  def rank(self, best, rest):
    best_size = len(best)
    rest_size = len(rest)
    p_best = best_size / (best_size + rest_size)
    p_rest = rest_size / (best_size + rest_size)
    # decisions = []
    # for d_id in self.model.decisions.keys():
    #   f_best, pos_count, neg_count = 0, 0, 0
    #   # Implement Ranks


def _main(model_name):
  from language.parser import Parser
  mdl = Parser.from_file("models/%s.str" % model_name)
  star = Star(mdl)
  best, rest = star.sample()
  print(len(best), len(rest))


if __name__ == "__main__":
  _main("ECS")



