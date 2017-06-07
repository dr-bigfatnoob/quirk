from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from distribution import *
import operator as o
from utils.lib import gt, lt, gte, lte, neq, eq

__author__ = "bigfatnoob"


def sample(values, size=100):
  return np.random.choice(values, size=size)


def expected_value(values, size=1000):
  means = []
  for _ in range(1000):
    samples = sample(values, int(size))
    means.append(np.mean(samples))
  return np.mean(means)


def standard_deviation(values):
  return np.std(values)


def percentile(values, percent):
  return np.percentile(values, percent)


def probability(values):
  return sum([1 if v >= 1 else 0 for v in values]) / len(values)


def lambda_ev(*args):
  return lambda x: expected_value(x, *args)


def lambda_std():
  return lambda x: standard_deviation(x)


def lambda_percentile(*args):
  return lambda x: percentile(x, *args)


def lambda_probability():
  return lambda x: probability(x)


def to_int(func):
  return lambda a, b: 1 if func(a, b) else 0

evaluations = {
    "EV": lambda_ev,
    "STD": lambda_std,
    "PERCENTILE": lambda_percentile,
    "PROBABILITY": lambda_probability
}

distributions = {
    "constant": Constant,
    "normal": Normal,
    "normalCI": NormalCI,
    "uniform": Uniform,
    "random": Random,
    "exp": Exponential,
    "binomial": Binomial,
    "geometric": Geometric,
    "triangular": Triangular
}

operations = {
    "+": o.add,
    "-": o.sub,
    "*": o.mul,
    "/": o.div,
    "|": max,
    "&": o.mul,
    ">": to_int(gt),
    "<": to_int(lt),
    ">=": to_int(gte),
    "<=": to_int(lte),
    "==": to_int(eq),
    "!=": to_int(neq)
}
