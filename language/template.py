from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils.lib import O
import numpy as np
from collections import deque, OrderedDict
from copy import deepcopy
from operator import mul

__author__ = "bigfatnoob"


class Component(O):
  """
  All components of graph
  should extend this class
  """
  id = 0

  def __init__(self, **kwargs):
    O.__init__(self, **kwargs)
    self.id = Component.id
    Component.id += 1

  def __hash__(self):
    if not self.id:
      return 0
    return hash(self.id)

  def __eq__(self, other):
    if not self.id or not other.id:
      return False
    return self.id == other.id


class Node(Component):
  """
  Node for a model
  """
  @staticmethod
  def agg(a, b, op):
    assert len(a) == len(b)
    return np.asarray([op(a_i, b_i) for a_i, b_i in zip(a, b)])

  def __init__(self, **kwargs):
    self._samples = []
    self.children = []
    self.operation = None
    Component.__init__(self, **kwargs)

  def add_child(self, child, operation):
    if self.operation is not None and operation != self.operation:
      raise AttributeError("Parent has an existing operation %s but new operation is %s" % (self.operation, operation))
    self.children.append(child)
    self.operation = operation

  def bfs(self):
    queue = deque()
    queue.append(self)
    while len(queue) > 0:
      item = queue.popleft()
      print((item.id, item.name))
      for child in item.children:
        queue.append(child)

  def dfs(self):
    stack = list()
    stack.insert(0, self)
    while len(stack) > 0:
      item = stack.pop(0)
      print((item.id, item.name))
      for child in item.children[::-1]:
        stack.insert(0, child)

  def evaluate(self):
    raise NotImplemented("Method has to be implemented in sub class")

  def clone(self):
    return deepcopy(self)

  def get_samples(self):
    return self._samples


class Decision(Node):
  """
  A Decision node.
  Can have multiple options in a hash called options
  """
  def __init__(self, **options):
    self.value = None
    self.options = options
    self.key = None
    Node.__init__(self)

  def clear(self):
    self.value = None
    self._samples = None

  def evaluate(self):
    self._samples = self.value.evaluate()
    return self._samples


class Objective(Node):
  """
  An objective node.
  """
  def __init__(self, direction, evaluation):
    self.direction = direction
    self.eval = evaluation
    self.value = None
    Node.__init__(self)

  def clear(self):
    self.value = None
    self._samples = None

  def evaluate(self):
    self._samples = self.children[0].evaluate()
    self.value = self.eval(self._samples)
    return self.value


class Input(Node):
  """
  A Node which is neither a decision or an objective
  but has distribution parameter
  """
  def __init__(self, distribution):
    self.distribution = distribution
    Node.__init__(self)

  def generate(self, size):
    if not self._samples or len(self._samples) != size:
      self._samples = self.distribution.sample(size)
    return self._samples

  def evaluate(self):
    return self._samples


class Variable(Node):
  def __init__(self):
    Node.__init__(self)

  def evaluate(self):
    children = self.children
    self._samples = children[0].evaluate()
    if len(children) > 1:
      for child in children[1:]:
        self._samples = Node.agg(self._samples, child.evaluate(), self.operation)
    else:
      self._samples = [self.operation(s) for s in self._samples]
    return self._samples


class Edge(Component):
  def __init__(self, source, target, operation):
    self.source = source
    self.target = target
    self.operation = operation
    Component.__init__(self)


def same(node):
  return node.children[0].get_samples()


class Model(O):
  def __init__(self, name, sample_size=100):
    self.name = name
    self.sample_size = sample_size
    self.nodes = OrderedDict()
    self.edges = OrderedDict()
    self.decisions = OrderedDict()
    self.inputs = OrderedDict()
    self.objectives = OrderedDict()
    self.variables = OrderedDict()
    self.decision_map = OrderedDict()
    O.__init__(self)

  def add_edge(self, source, target, operation=same):
    target.add_child(source, operation)
    edge = Edge(source, target, operation)
    self.edges[edge.id] = edge

  def input(self, distribution, name=None):
    i = Input(distribution)
    i.name = name if name else i.id
    self.inputs[i.id] = i
    self.nodes[i.id] = i
    return i

  def variable(self, name=None):
    v = Variable()
    v.name = name if name else v.id
    self.variables[v.id] = v
    self.nodes[v.id] = v
    return v

  def decision(self, options, name=None, key=None):
    d = Decision(**options)
    for value in options.values():
      self.add_edge(value, d, None)
    d.name = name if name else d.id
    if key is not None:
      d.key = key
    self.decisions[d.id] = d
    self.nodes[d.id] = d
    return d

  def objective(self, direction, evaluation=np.mean, name=None):
    o = Objective(direction, evaluation)
    o.name = name if name else o.id
    self.objectives[o.id] = o
    self.nodes[o.id] = o
    return o

  def node_edges(self, node):
    for child in node.children:
      edge = Edge(child, node, node.operation)
      self.edges[edge.id] = edge

  def generate(self):
    solutions = OrderedDict()
    if self.decision_map:
      ref = {key: np.random.choice(vals) for key, vals in self.decision_map.items()}
      for key, decision in self.decisions.items():
        solutions[key] = decision.options[ref[decision.key]].id
    else:
      for key, decision in self.decisions.items():
        solutions[key] = np.random.choice(decision.options.values()).id
    return solutions

  def get_parameters(self):
    parameters = []
    for node in self.nodes.values():
      if isinstance(node, Input):
        parameters.append(node)
    return parameters

  def get_max_size(self):
    if self.decision_map:
      lst = [len(vals) for vals in self.decision_map.values()]
    else:
      lst = [len(value.options) for value in self.decisions.values()]
    return reduce(mul, lst, 1)

  def get_decisions(self):
    if self.decision_map:
      return self.decision_map
    else:
      return {d.name: [o.name for o in d.options.values()] for d in self.decisions.values()}

  def get_decision_name(self, key):
    name = self.decisions[key].key
    if name is None:
      name = self.decisions[key].name
    return name

  def get_decision_value(self, value):
    value = self.nodes[value].has()["label"]
    if value is None:
      value = self.nodes[value].name
    return value

  def print_solution(self, solution):
    print("Solution:")
    dic = OrderedDict()
    for key, value in solution.items():
      name = self.get_decision_name(key)
      value = self.get_decision_value(value)
      dic[name] = value
    for name, value in dic.items():
      print("\t name: %s, value: %s" % (name, value))

  def get_solution(self, solution):
    dic = OrderedDict()
    for key, value in solution.items():
      name = self.get_decision_name(key)
      value = self.get_decision_value(value)
      dic[name] = value
    return dic

  def populate(self, size):
    max_size = self.get_max_size()
    if size > max_size:
      size = max_size
    population = []
    while len(population) < size:
      one = self.generate()
      if one not in population:
        population.append(one)
    return population

  def evaluate(self, solution):
    assert len(solution) == len(self.decisions)
    for key, value in solution.items():
      self.decisions[key].value = self.nodes[value]
    for key in self.objectives.keys():
      self.objectives[key].value = None
    objs = OrderedDict()
    for key, objective in self.objectives.items():
      objective.evaluate()
      objs[key] = O(id=objective.id, value=objective.value, _samples=objective.get_samples()[:])
    return objs

  def evaluate_constraints(self, solution):
    return True, 0

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
    if self.bdom(obj1, obj2):
      return 1
    elif self.bdom(obj2, obj1):
      return 2
    return 0

  def initialize(self):
    for inp in self.inputs.values():
      inp.generate(self.sample_size)

  def test(self):
    self.initialize()
    print("Max Size = %d" % self.get_max_size())
    solutions = self.populate(10)
    # print(self.evaluate(solutions[0]))
    for sol in solutions:
      evals = self.evaluate(sol)
      arr = []
      for key, val in evals.items():
        arr.append((self.objectives[key].name, val))
      print(arr)
      # self.print_solution(sol)
