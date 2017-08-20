from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

import pydot as dot
import networkx as nx
from utils.lib import O, MINIMIZE
from genesis.gen_utils import GraphPoint, Objective, Vocabulary, Statement, choice


__author__ = "bigfatnoob"


MODEL_SETTINGS = O(
  objs={obj.name: obj for obj in [
    Objective("length", MINIMIZE, GraphPoint.evaluate_length),
    Objective("degree", MINIMIZE, GraphPoint.evaluate_degree),
  ]}
)


class Model(O):
  def __init__(self, vocab=None, positives=None, negatives=None):
    O.__init__(self)
    self.vocabulary = Vocabulary() if not vocab else vocab
    self.positives = set()
    self.negatives = set()
    if positives: self.add_examples(positives, is_positive=True)
    if negatives: self.add_examples(negatives, is_positive=False)
    self.objectives = MODEL_SETTINGS.objs

  def add_examples(self, examples, is_positive=True):
    for example in examples:
      self.vocabulary.update_node(example.source)
      self.vocabulary.update_edge(example.relation)
      self.vocabulary.update_node(example.target)
      if is_positive:
        self.positives.add(example)
      else:
        self.negatives.add(example)

  @staticmethod
  def cycle_exists(graph):
    try:
      return len(list(nx.simple_cycles(graph))) > 0
    except nx.exception.NetworkXNoCycle:
      return False

  @staticmethod
  def check_edge_consistency(graph):
    nodes = graph.nodes()
    for node in nodes:
      in_edges = graph.in_edges([node], data=True)
      if in_edges:
        relations = set([edge[2]['relation'] for edge in in_edges])
        if len(relations) != 1:
          return False
    return True

  def _check_edges_validity(self, graph):
    for pos in self.positives:
      edge = graph.get_edge_data(pos.source, pos.target)
      if not edge or edge['relation'] != pos.relation:
        return False
    for neg in self.negatives:
      edge = graph.get_edge_data(neg.source, neg.target)
      if edge and edge['relation'] == neg.relation:
        self.draw(graph)
        return False
    return True

  def _create_edge(self, graph, existing):
    stmt = None
    while stmt is None or stmt in existing:
      target = choice(self.vocabulary.nodes)
      in_edges = graph.in_edges([target], data=True)
      if in_edges:
        relations = set([edge[2]['relation'] for edge in in_edges])
        assert len(relations) == 1, "Multiple incoming relations to node %s" % target
        relation = choice(relations)
      else:
        relation = choice(self.vocabulary.edges)
      source = target
      while source == target:
        source = choice(self.vocabulary.nodes)
      # Checking if edge or its reverse does not exist in graph
      if graph.has_edge(source, target) or graph.has_edge(target, source):
        stmt = None
      else:
        stmt = Statement(source, relation, target)
    graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
    if not self.cycle_exists(graph):
      existing.add(stmt)
    else:
      graph.remove_edge(stmt.source, stmt.target)
    return graph, existing

  def evaluate_constraints(self, solution):
    """
    :param solution: Instance of graph
    :return:
    """
    return self.check_edge_consistency(solution) and self._check_edges_validity(solution) and not \
        self.cycle_exists(solution), 0

  def generate(self):
    """
    Generate an instance of GraphPoint
    :return:
    """
    graph = nx.DiGraph()
    graph.add_nodes_from(self.vocabulary.nodes)
    for stmt in self.positives:
      graph.add_edge(stmt.source, stmt.target, relation=stmt.relation)
    existing = set(list(self.positives) + list(self.negatives))
    while not nx.is_weakly_connected(graph):
      graph, existing = self._create_edge(graph, existing)
    return GraphPoint(graph, existing)

  def populate(self, size):
    """
    Populate a list of GraphPoints
    :param size: size of population
    :return:
    """
    population = set()
    while len(population) < size:
      point = self.generate()
      if not self.cycle_exists(point.decisions):
       population.add(self.generate())
    return list(population)

  def bdom(self, obj1, obj2):
    """
    Binary Domination
    :param obj1: Objective 1
    :param obj2: Objective 2
    :return: Check objective 1 dominates objective 2
    """
    at_least = False
    for i in self.objectives.keys():
      a, b = obj1[i], obj2[i]
      if self.objectives[i].direction.better(a, b):
        at_least = True
      elif a == b:
        continue
      else:
        return False
    return at_least

  def better(self, obj1, obj2):
    """
    Check if obj1 dominates obj2
    :param obj1: Objectives of point1
    :param obj2: Objectives of point2
    :return: if obj1 dominates obj2 return 1 elseif obj2 dominates obj1 return 2 else 0
    """
    if self.bdom(obj1, obj2):
      return 1
    elif self.bdom(obj2, obj1):
      return 2
    return 0

  def draw(self, graph, fig_name="genesis/temp.png"):
    dot_graph = dot.Dot(graph_type='digraph', rankdir="BT")
    for node in self.vocabulary.nodes:
      dot_graph.add_node(dot.Node(name=node))
    for edge in graph.edges(data=True):
      style = 'dashed' if edge[2]['relation'] == 'or' else 'solid'
      dot_graph.add_edge(dot.Edge(edge[0], edge[1], style=style))
    dot_graph.write(fig_name, format='png')


class QueryEngine(O):
  def __init__(self, model):
    O.__init__(self)
    self.model = model

  def query_space(self, population):
    """
    :param population: List of instance of GraphPoints
    :return: collection of statements which are the search spaces
    """
    spaces = set()
    for point in population:
      spaces.update(point.statements)
    spaces = spaces.difference(self.model.positives).difference(self.model.negatives)
    return spaces

  def top_queries(self, population, size=None):
    spaces = list(self.query_space(population))
    space_sets = []
    for space in spaces:
      pos, neg = 0, 0
      for point in population:
        if space in point.statements:
          pos += 1
        else:
          neg += 1
      space_sets.append((space, abs(pos - neg)))
    space_sets = sorted(space_sets, key=lambda x: x[1])
    if size is None:
      size = len(population)
    return [query for query, _ in space_sets][:size]



def test_basic():
  pos_examples = ["c1 -> or -> cost",
                  "b1 -> or -> benefit",
                  ]
  neg_examples = ["c1 -> and -> b1",
                  "c1 -> or -> b1"]
  other_nodes = {"c2", "nb"}
  other_edges = {"and"}
  vocab = Vocabulary(other_nodes, other_edges)
  pos_examples = map(Statement.from_string, pos_examples)
  neg_examples = map(Statement.from_string, neg_examples)
  model = Model(vocab, pos_examples, neg_examples)
  pop = model.populate(5)
  print([p.evaluate(model) for p in pop])
  model.draw(pop[0].decisions, "genesis/temp0.png")
  model.draw(pop[4].decisions, "genesis/temp4.png")


def test_nsga():
  from technix import nsga
  from genesis.mutator import Mutator
  pos_examples = ["c1 -> or -> cost",
                  "b1 -> or -> benefit",
                  ]
  neg_examples = ["c1 -> and -> b1",
                  "c1 -> or -> b1"]
  other_nodes = {"c2", "nb"}
  other_edges = {"and"}
  vocab = Vocabulary(other_nodes, other_edges)
  pos_examples = map(Statement.from_string, pos_examples)
  neg_examples = map(Statement.from_string, neg_examples)
  model = Model(vocab, pos_examples, neg_examples)
  pop = model.populate(10)
  # print([p.evaluate(model) for p in pop])
  mutator = Mutator(model)
  pop = nsga.nsga2(model, mutator, pop, iterations=10)
  model.draw(pop[0].decisions, "genesis/temp_best.png")
  model.draw(pop[-1].decisions, "genesis/temp_last.png")


def test_check_genesis():
  from genesis.mutator import Mutator
  from technix import nsga
  from genesis.oracle import StatementOracle
  oracle = StatementOracle([
      "c1 -> or -> cost",
      "c2 -> or -> cost",
      "b1 -> or -> benefit",
      "b2 -> or -> benefit",
      "cost -> and -> nb",
      "benefit -> and -> nb"
  ])
  pos_examples = ["c1 -> or -> cost",
                  "b1 -> or -> benefit",
                  ]
  neg_examples = ["c1 -> and -> b1",
                  "c1 -> or -> b1"]
  other_nodes = {"c2", "nb"}
  other_edges = {"and"}
  vocab = Vocabulary(other_nodes, other_edges)
  pos_examples = map(Statement.from_string, pos_examples)
  neg_examples = map(Statement.from_string, neg_examples)
  model = Model(vocab, pos_examples, neg_examples)
  repeats = 10
  pop = None
  mutator = Mutator(model)
  qe = QueryEngine(model)
  for _ in xrange(repeats):
    pop = model.populate(10)
    pop = nsga.nsga2(model, mutator, pop, iterations=10)
    top_query = qe.top_queries(pop)[0]
    status = oracle.validate(top_query)
    print(top_query, status)
    model.add_examples([top_query], status)
  model.draw(pop[0].decisions, "genesis/improved_best.png")


# TODO: Code up conversion from quirk to and or graphs


if __name__ == "__main__":
  # test_basic()
  # test_check_mutation()
  test_check_genesis()
