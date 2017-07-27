from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True
from utils.lib import MAXIMIZE
import numpy as np
from copy import deepcopy

__author__ = "bigfatnoob"


def evtpi(samples, direction):
  """
  Expected Value of Total Perfect Information
  :param samples: A 2d array (#points, #samples)
  :param direction: MAXIMIZE or MINIMIZE
  :return:
  """
  func = np.max if direction == MAXIMIZE else np.min
  return abs(np.mean(map(func, samples)) - func(row_means(samples)))


def evppi(samples, param_distribution, direction):
  if min(param_distribution) == max(param_distribution):
    # print("Deterministic Distribution")
    return None
  assert(len(param_distribution) == len(samples[0]))
  samps = np.asarray([s[:] for s in samples])
  dist = param_distribution[:]
  d = len(samps)
  n = len(dist)
  quick_sort_pivot(dist, samps)
  n_segs = np.ones((d, d), dtype=np.int)
  seg_points = []
  for i in xrange(d - 1):
    for j in xrange(i + 1, d):
      cm = np.cumsum(samps[i] - samps[j]) / n
      if n_segs[i][j] == 1:
        l = np.argmin(cm)
        u = np.argmax(cm)
        if cm[u] - np.max((cm[0], cm[n - 1])) > np.min((cm[0], cm[n-1])) - cm[l]:
          seg_point = u
        else:
          seg_point = l
        if seg_point > 0 and seg_point < n - 1:
          seg_points.append(seg_point)

  score = 0
  print(len(seg_points))
  if len(seg_points) > 0:
    quick_sort_vector_pivot(seg_points)
    seg_points2 = np.unique([-1] + seg_points + [n - 1])
    func = np.max if direction == MAXIMIZE else np.min
    for j in xrange(len(seg_points2) - 1):
      extreme = -np.inf if direction == MAXIMIZE else np.inf
      for nb in samps:
        tot = sum([nb[l] for l in range(seg_points2[j]+1, seg_points2[j+1]+1)])
        extreme = func((extreme, tot))
      score += extreme / n
    score -= func(row_means(samps))
  else:
    score = 0
  return abs(score)


def row_means(samples):
  """
  Means of rows of 2d array
  :param samples:
  :return:
  """
  return map(np.mean, samples)


def col_means(samples):
  """
  Means of cols of 2d array
  :param samples:
  :return:
  """
  return map(np.mean, zip(*samples))


def quick_sort_vector_pivot(vector):
  left = 0
  right = len(vector) - 1
  quick_sort_vector(vector, left, right)


def quick_sort_vector(vector, left, right):
  i = left
  j = right
  mid_val = vector[(i + j) // 2]
  while i < j:
    while vector[i] < mid_val and i < right:
      i += 1
    while vector[j] > mid_val and j > left:
      j -= 1
    if i < j:
      swap_vector(vector, i, j)
    if i <= j:
      i += 1
      j -= 1
    if j > left:
      quick_sort_vector(vector, left, j)
    if i < right:
      quick_sort_vector(vector, i, right)


def quick_sort_pivot(vector, matrix):
  left = 0
  right = len(vector) - 1
  quick_sort(vector, matrix, left, right)


def quick_sort(vector, matrix, left, right):
  i = left
  j = right
  mid_val = vector[(i + j) // 2]
  while i < j:
    while vector[i] < mid_val and i < right:
      i += 1
    while vector[j] > mid_val and j > left:
      j -= 1
    if i < j:
      swap_vector(vector, i, j)
      swap_matrix(matrix, i, j)
    if i <= j:
      i += 1
      j -= 1
    if j > left:
      quick_sort(vector, matrix, left, j)
    if i < right:
      quick_sort(vector, matrix, i, right)


def swap_vector(vector, i, j):
  vector[i], vector[j] = vector[j], vector[i]


def swap_matrix(matrix, i, j):
  for row in matrix:
    row[i], row[j] = row[j], row[i]
