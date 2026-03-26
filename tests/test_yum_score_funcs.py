import pytest
from yum_score_funcs import normalise_points

def test_normalise_points():
    min: float = 2.0
    max: float = 10.0
    score: float = 6.0
    assert normalise_points(min, max, score) == 0.5
