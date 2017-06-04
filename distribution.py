from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils import O
import numpy as np

__author__ = "bigfatnoob"

class Distribution(O):
  def __init__(self):
    O.__init__(self)

  def sample(self, size):
    raise NotImplemented("Method has to be implemented in sub class")


class Constant(Distribution):
  """
  Constant distribution.
  Parameters: value
  """
  def __init__(self, value):
    self.value = float(value)
    Distribution.__init__(self)

  def sample(self, size):
    return np.full(size, self.value)


class Normal(Distribution):
  """
  Normal distribution
  Parameters: mean, std_dev
  """
  def __init__(self, mean, std_dev):
    self.mean = float(mean)
    self.sd = float(std_dev)
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.normal(self.mean, self.sd, size)


class NormalCI(Distribution):
  """
  Normal distribution between a 99.9% confidence interval
  Parameters: low, high
  """
  def __init__(self, low, high):
    self.low = float(low)
    self.high = float(high)
    Distribution.__init__(self)

  def sample(self, size):
    mean = (self.low + self.high) / 2
    sd = abs(self.high - self.low) / 3.29
    return np.random.normal(mean, sd, size)


class Uniform(Distribution):
  """
  Uniform distribution between two limits
  Parameters: low, high
  """
  def __init__(self, low, high):
    self.low = float(low)
    self.high = float(high)
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.uniform(self.low, self.high, size)


class Random(Distribution):
  """
  Random distribution between 0 and 1
  """
  def __init__(self):
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.random_sample(size)


class Exponential(Distribution):
  """
  Exponential distribution
  Parameter: scale
  """
  def __init__(self, scale):
    self.scale = scale
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.exponential(self.scale, size)


class Binomial(Distribution):
  """
  Binomial Distribution
  Parameter: trials, prob
  """
  def __init__(self, trials, prob):
    self.trials = trials
    self.prob = prob
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.binomial(self.trials, self.prob, size)


class Geometric(Distribution):
  """
  Geometric Distribution
  Parameter: prob
  """
  def __init__(self, prob):
    self.prob = prob
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.geometric(self.prob, size)


class Triangular(Distribution):
  """
  Triangular Distribution
  Parameter: low, mode, high
  """
  def __init__(self, low, mode, high):
    self.low = low
    self.mode = mode
    self.high = high
    Distribution.__init__(self)

  def sample(self, size):
    return np.random.triangular(self.low, self.mode, self.high, size)
