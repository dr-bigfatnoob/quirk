from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
import random
from utils.lib import O
from genesis.gen_utils import Statement, Vocabulary, choice

__author__ = "bigfatnoob"


def sample(collection, size):
  size = min(size, len(collection))
  return random.sample(collection, size)


class Oracle(O):
  def __init__(self):
    O.__init__(self)

  def validate(self, query):
    raise NotImplemented("Has to be implemented in sub class.")

  def sample_positive_examples(self, size):
    raise NotImplemented("Has to be implemented in sub class.")

  def sample_negative_examples(self, size):
    raise NotImplemented("Has to be implemented in sub class.")


class StatementOracle(Oracle):
  def __init__(self, statements):
    Oracle.__init__(self)
    self.statements = set()
    self.vocabulary = None
    nodes = set()
    edges = set()
    for statement in statements:
      stmt = statement
      if isinstance(stmt, str):
        stmt = Statement.from_string(stmt)
      nodes.add(stmt.source)
      edges.add(stmt.relation)
      nodes.add(stmt.target)
      self.statements.add(stmt)
    self.vocabulary = Vocabulary(nodes, edges)

  def validate(self, query):
    return query in self.statements

  def sample_positive_examples(self, size):
    return list(sample(self.statements, size))

  def sample_negative_examples(self, size):
    samples = set()
    while len(samples) < size:
      target = choice(self.vocabulary.nodes)
      relation = choice(self.vocabulary.edges)
      source = target
      while source == target:
        source = choice(self.vocabulary.nodes)
      stmt = Statement(source, relation, target)
      if stmt in self.statements or stmt in samples:
        continue
      samples.add(stmt)
    return list(samples)
