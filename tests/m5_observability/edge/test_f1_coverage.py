import pytest
from edge.m5_observability.checks.coverage import compute_coverage, aggregate_coverage


def test_compute_coverage_basic():
    """Test basic coverage computation."""
    required = ["a", "b", "c", "d"]
    present = ["a", "c"]
    
    result = compute_coverage(present, required)
    
    assert result == 0.50


def test_compute_coverage_empty_required():
    """Test coverage when required is empty."""
    required = []
    present = ["x"]
    
    result = compute_coverage(present, required)
    
    assert result == 0.00


def test_compute_coverage_duplicates():
    """Test coverage with duplicates in required."""
    required = ["a", "a", "b"]
    present = ["a"]
    
    result = compute_coverage(present, required)
    
    assert result == 0.50


def test_aggregate_coverage_min():
    """Test aggregation using minimum."""
    per_surface = [0.72, 1.0, 0.8]
    
    result = aggregate_coverage(per_surface)
    
    assert result == 0.72


def test_aggregate_coverage_empty():
    """Test aggregation with empty list."""
    per_surface = []
    
    result = aggregate_coverage(per_surface)
    
    assert result == 0.00

