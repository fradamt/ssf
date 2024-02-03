from typing import TypeVar, Optional

from pyrsistent import PSet, PMap, PVector, pset
from formal_verification_annotations import *

T1 = TypeVar('T1')
T2 = TypeVar('T2')

def merge_maps(a: PMap[T1, T2], b:PMap[T1, T2]) -> PMap[T1, T2]:
    return a.update(b)

def concat_lists(a: PVector[T1], b: PVector[T1]) -> PVector[T1]:
    return a.extend(b)

def merge_sets(a: PSet[T1], b: PSet[T1]) -> PSet[T1]:
    return a.union(b)

def create_set(l: list[T1]) -> PSet[T1]:
    return pset(l)

def pick_from_set(s: PSet[T1]) -> T1:
    Requires(len(s) > 0)
    return list(s)[0]

def get_key_set(d: PMap[T1,T2]) -> PSet[T1]:
    return pset(d.keys())