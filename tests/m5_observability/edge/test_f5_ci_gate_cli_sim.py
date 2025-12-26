import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from edge.m5_observability.tools.m5_ci_gate_cli import main


@pytest.fixture
def sample_policy():
    return {
        "module": "m5_observability",
        "version": "1.0.0",
        "policy": {
            "obs.required_signals": ["request_id", "trace_id"],
            "obs.min_telemetry_coverage_warn": 0.8,
            "obs.min_telemetry_coverage_block": 0.7,
            "obs.require_correlation_id": True,
            "obs.require_hw_timestamp": False,
            "obs.max_label_cardinality_warn": 100,
            "obs.max_label_cardinality_block": 1000,
            "obs.disallow_dynamic_keys": False
        },
        "gate_mode": "Hard"
    }


def test_ci_gate_warn_mode(sample_policy):
    """Test Warn mode - should always exit 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"
        policy_path.write_text(json.dumps(sample_policy), encoding="utf-8")
        
        input_path = Path(tmpdir) / "input.json"
        input_path.write_text(
            Path("tests/fixtures/m5_observability/ci_input_warn.json").read_text(encoding="utf-8"),
            encoding="utf-8"
        )
        
        out_path = Path(tmpdir) / "receipt.jsonl"
        
        test_args = [
            "m5_ci_gate_cli.py",
            "--policy", str(policy_path),
            "--input", str(input_path),
            "--out", str(out_path),
            "--gate-mode", "Warn"
        ]
        
        with patch("sys.argv", test_args):
            exit_code = main()
        
        assert exit_code == 0
        assert out_path.exists()
        receipt = json.loads(out_path.read_text(encoding="utf-8").strip())
        assert receipt["decision"]["outcome"] == "warn"


def test_ci_gate_soft_mode(sample_policy):
    """Test Soft mode - should exit 1 for soft_block/hard_block."""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"
        policy_path.write_text(json.dumps(sample_policy), encoding="utf-8")
        
        input_path = Path(tmpdir) / "input.json"
        input_path.write_text(
            Path("tests/fixtures/m5_observability/ci_input_soft.json").read_text(encoding="utf-8"),
            encoding="utf-8"
        )
        
        out_path = Path(tmpdir) / "receipt.jsonl"
        
        test_args = [
            "m5_ci_gate_cli.py",
            "--policy", str(policy_path),
            "--input", str(input_path),
            "--out", str(out_path),
            "--gate-mode", "Soft"
        ]
        
        with patch("sys.argv", test_args):
            exit_code = main()
        
        assert exit_code == 1
        assert out_path.exists()
        receipt = json.loads(out_path.read_text(encoding="utf-8").strip())
        assert receipt["decision"]["outcome"] == "soft_block"


def test_ci_gate_hard_mode(sample_policy):
    """Test Hard mode - should exit 1 for hard_block only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_path = Path(tmpdir) / "policy.json"
        policy_path.write_text(json.dumps(sample_policy), encoding="utf-8")
        
        input_path = Path(tmpdir) / "input.json"
        input_path.write_text(
            Path("tests/fixtures/m5_observability/ci_input_hard.json").read_text(encoding="utf-8"),
            encoding="utf-8"
        )
        
        out_path = Path(tmpdir) / "receipt.jsonl"
        
        test_args = [
            "m5_ci_gate_cli.py",
            "--policy", str(policy_path),
            "--input", str(input_path),
            "--out", str(out_path),
            "--gate-mode", "Hard"
        ]
        
        with patch("sys.argv", test_args):
            exit_code = main()
        
        assert exit_code == 1
        assert out_path.exists()
        receipt = json.loads(out_path.read_text(encoding="utf-8").strip())
        assert receipt["decision"]["outcome"] == "hard_block"

