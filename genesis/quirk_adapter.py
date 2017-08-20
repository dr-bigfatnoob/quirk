from __future__ import print_function, division
import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from language import template as gt
from genesis import gen_utils
import networkx as nx
import pydot as dot

__author__ = "bigfatnoob"


def get_node_name(node):
  return "%s_%d" % (node.name, node.id)


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


def draw(graph, fig_name):
  dot_graph = dot.Dot(graph_type='digraph', rankdir="BT")
  for edge in graph.edges(data=True):
    style = 'dashed' if edge[2]['relation'] == 'or' else 'solid'
    dot_graph.add_edge(dot.Edge(edge[0], edge[1], style=style))
  dot_graph.write(fig_name, format='png')


def test_quirk_conversion(model_name):
  from oracle import StatementOracle
  print("# %s" % model_name)
  from language.parser import Parser
  mdl = Parser.from_file("models/quirk/%s.str" % model_name)
  points = convert(mdl)
  for i, point in enumerate(points):
    oracle = StatementOracle(point.statements)
    positive_examples = oracle.sample_positive_examples(2)
    negative_examples = oracle.sample_negative_examples(2)
    draw(point.decisions, "genesis/adapter_%d.png" % i)


if __name__ == "__main__":
  test_quirk_conversion("AOWS")
