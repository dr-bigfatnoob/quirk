from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

from utils.lib import O
import re
import pydot as dot

__author__ = "bigfatnoob"


class Statement(O):
  Pattern = r'(\s*\w[\w\s\-]*)->(\s*\w[\w\s\-]*)->(\s*\w[\w\s\-]*)'

  def __init__(self, source, relation, target):
    O.__init__(self)
    self.source = source.strip()
    self.relation = relation.strip()
    self.target = target.strip()

  @staticmethod
  def from_string(stmt):
    groups = re.match(Statement.Pattern, stmt).groups()
    if len(groups) == 3:
      return Statement(*groups)
    raise Exception("Invalid format: %s. \nLegal format: %s" % (stmt, "Source->Relation->Target"))

  def __repr__(self):
    return "%s -> %s -> %s" % (self.source, self.relation, self.target)

  def __hash__(self):
    return hash(repr(self))


class Vocabulary(O):
  def __init__(self):
    O.__init__(self)
    self.nodes = set()
    self.edges = set()

  def add_stmt(self, stmt):
    self.nodes.add(stmt.source)
    self.edges.add(stmt.relation)
    self.nodes.add(stmt.target)


class Model(O):
  def __init__(self):
    O.__init__(self)
    self.positives = set()
    self.negatives = set()

  def add_examples(self, examples, is_positive=True):
    if is_positive:
      self.positives.update(examples)
    else:
      self.negatives.update(examples)


def draw(statements, file_name):
  graph = dot.Dot(graph_type='digraph', rankdir="BT")
  for stmt in statements:
    style = 'dashed' if stmt.relation == 'or' else 'solid'
    graph.add_edge(dot.Edge(stmt.source, stmt.target, style=style))
  graph.write(file_name, format='png')


def test():
  pos_examples = ["c1 -> or -> cost",
                  "c2 -> or -> cost",
                  "b1 -> or -> benefit",
                  "b2 -> or -> benefit",
                  "cost -> and -> nb",
                  "benefit -> and -> nb"]
  pos_examples = map(Statement.from_string, pos_examples)
  draw(pos_examples, "genesis/temp.png")

if __name__ == "__main__":
  test()
