import json
import pytest
from pathlib import Path
from edge.m5_observability.smoke.smoke_runner import run_obs_smoke, run_and_record


@pytest.fixture
def fixture_repo():
    """Return path to fixture smoke project."""
    return str(Path(__file__).parent.parent.parent / "fixtures" / "m5_observability" / "smoke_project")


@pytest.fixture
def policy_cfg():
    """Return policy configuration."""
    return {
        "obs.required_signals": [
            "latency_ms",
            "status",
            "error_code",
            "request_id",
            "trace_id",
            "hw_ts_ms"
        ],
        "obs.min_telemetry_coverage_warn": 0.8
    }


def test_pass_case(fixture_repo, policy_cfg):
    """Test PASS outcome when coverage >= threshold."""
    result = run_obs_smoke(fixture_repo, policy_cfg)
    
    # Verify structure
    assert "checked_files" in result
    assert "required_signals" in result
    assert "missing_signals" in result
    assert "telemetry_coverage_pct" in result
    assert "outcome" in result
    assert "rationale" in result
    
    # Verify checked files
    assert result["checked_files"] == 2
    
    # Verify required signals preserved from policy
    assert result["required_signals"] == policy_cfg["obs.required_signals"]
    
    # Fixture contains: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
    # All 6 signals present
    assert result["telemetry_coverage_pct"] == 1.0
    
    # Should be PASS
    assert result["outcome"] == "pass"
    
    # Verify rationale format
    assert "OBS_SMOKE: coverage=" in result["rationale"]
    assert "missing=" in result["rationale"]
    
    # All signals present, so missing should be empty
    assert result["missing_signals"] == []
    assert "missing=none" in result["rationale"]


def test_warn_case(fixture_repo):
    """Test WARN outcome when coverage < threshold."""
    # Create policy with more signals that won't be found
    warn_policy = {
        "obs.required_signals": [
            "latency_ms",
            "status",
            "error_code",
            "request_id",
            "trace_id",
            "hw_ts_ms",
            "span_id",  # Not in fixture
            "parent_span_id",  # Not in fixture
            "service_name",  # Not in fixture
            "endpoint"  # Not in fixture
        ],
        "obs.min_telemetry_coverage_warn": 0.8
    }
    
    result = run_obs_smoke(fixture_repo, warn_policy)
    
    # Coverage should be 6/10 = 0.6
    assert result["telemetry_coverage_pct"] == 0.6
    
    # Should be WARN (0.6 < 0.8)
    assert result["outcome"] == "warn"
    
    # Missing signals should be sorted
    expected_missing = ["endpoint", "parent_span_id", "service_name", "span_id"]
    assert result["missing_signals"] == expected_missing
    
    # Verify rationale includes missing list
    assert "missing=endpoint,parent_span_id,service_name,span_id" in result["rationale"]


def test_receipt_writing(fixture_repo, policy_cfg, tmp_path):
    """Test that receipt is written correctly in JSONL format."""
    receipts_path = str(tmp_path / "receipts.jsonl")
    
    # Run and record
    result = run_and_record(fixture_repo, policy_cfg, receipts_path)
    
    # Verify result returned
    assert "outcome" in result
    
    # Verify receipt file exists
    assert Path(receipts_path).exists()
    
    # Read and parse JSONL
    with open(receipts_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Should have exactly 1 line
    assert len(lines) == 1
    
    # Parse JSON
    receipt = json.loads(lines[0])
    
    # Verify required fields
    assert receipt["module"] == "M5_observability_v1"
    assert receipt["gate_id"] == "observability_smoke_v1"
    
    # Verify decision structure
    assert "decision" in receipt
    assert "outcome" in receipt["decision"]
    assert "rationale" in receipt["decision"]
    assert receipt["decision"]["outcome"] == result["outcome"]
    assert receipt["decision"]["rationale"] == result["rationale"]
    
    # Verify inputs structure
    assert "inputs" in receipt
    assert "required_signals" in receipt["inputs"]
    assert "missing_signals" in receipt["inputs"]
    assert "telemetry_coverage_pct" in receipt["inputs"]
    assert "checked_files" in receipt["inputs"]
    
    # Verify timestamps structure
    assert "timestamps" in receipt
    assert "hw_monotonic_ms" in receipt["timestamps"]
    assert receipt["timestamps"]["hw_monotonic_ms"] == 0
    
    # Verify signature structure
    assert "signature" in receipt
    assert receipt["signature"]["algo"] == "stub-sha256"
    assert receipt["signature"]["value"] == "stub"


def test_no_egress_guard():
    """Test that smoke_runner module does not import network libraries."""
    # Read the smoke_runner source
    smoke_runner_path = Path(__file__).parent.parent.parent.parent / "edge" / "m5_observability" / "smoke" / "smoke_runner.py"
    source = smoke_runner_path.read_text(encoding="utf-8")
    
    # Check for forbidden imports
    forbidden_imports = [
        "import socket",
        "from socket",
        "import requests",
        "from requests",
        "import urllib",
        "from urllib",
        "import http",
        "from http",
        "import grpc",
        "from grpc",
        "import aiohttp",
        "from aiohttp"
    ]
    
    for forbidden in forbidden_imports:
        assert forbidden not in source, f"Found forbidden import: {forbidden}"


def test_deterministic_sorting(fixture_repo, policy_cfg):
    """Test that file lists and missing signals are sorted deterministically."""
    # Run twice
    result1 = run_obs_smoke(fixture_repo, policy_cfg)
    result2 = run_obs_smoke(fixture_repo, policy_cfg)
    
    # Results should be identical
    assert result1 == result2
    
    # Missing signals should be sorted
    assert result1["missing_signals"] == sorted(result1["missing_signals"])


def test_missing_policy_keys(fixture_repo):
    """Test that missing policy keys raise ValueError."""
    # Missing required_signals
    incomplete_cfg1 = {"obs.min_telemetry_coverage_warn": 0.8}
    
    with pytest.raises(ValueError) as exc_info:
        run_obs_smoke(fixture_repo, incomplete_cfg1)
    
    assert "obs.required_signals" in str(exc_info.value)
    
    # Missing min_telemetry_coverage_warn
    incomplete_cfg2 = {"obs.required_signals": ["signal1"]}
    
    with pytest.raises(ValueError) as exc_info:
        run_obs_smoke(fixture_repo, incomplete_cfg2)
    
    assert "obs.min_telemetry_coverage_warn" in str(exc_info.value)


def test_empty_required_signals(fixture_repo):
    """Test handling of empty required signals list."""
    empty_policy = {
        "obs.required_signals": [],
        "obs.min_telemetry_coverage_warn": 0.8
    }
    
    result = run_obs_smoke(fixture_repo, empty_policy)
    
    # Coverage should be 0.0 when no signals required
    assert result["telemetry_coverage_pct"] == 0.0
    assert result["missing_signals"] == []
    assert result["outcome"] == "warn"  # 0.0 < 0.8

