from __future__ import print_function, division
import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from language import template as gt
from genesis import gen_utils
import networkx as nx

__author__ = "bigfatnoob"


def get_node_name(node):
  return node.name + "_" + node.id


def convert(q_model):
  points = []
  for node in q_model.objectives.values():
    statements = []
    graph = nx.DiGraph()
    stack = [node]
    while len(stack):
      target = stack.pop()
      children, relation = None, None
      if isinstance(target, gt.Decision):
        children = target.options.values()
        relation = "or"
      elif target.children:
        children = target.children
        relation = "and"
      if children:
        t_name = get_node_name(target)
        for source in children:
          stack.append(source)
          s_name = get_node_name(source)
          graph.add_edge(s_name, t_name, relation=relation)
          statements.append(gen_utils.Statement(s_name, relation, t_name))
    points.append(gen_utils.GraphPoint(graph, statements))
  return points


def test_quirk_conversion(model_name):
  print("# %s" % model_name)
  from language.parser import Parser
  from language.mutator import Mutator
  mdl = Parser.from_file("models/quirk/%s.str" % model_name)
  points = convert(mdl)
