import pytest
from edge.m5_observability.discovery.surfaces import discover_surfaces


def test_endpoints_discovery():
    """Test that endpoints are correctly discovered from diff."""
    diff = """--- a/src/api/routes.py
+++ b/src/api/routes.py
@@ -1,3 +1,5 @@
+router.get("/orders/:id")
+@app.post("/login")
 # existing code
"""
    result = discover_surfaces([], diff)
    
    assert "endpoints_touched" in result
    assert "GET /orders/:id" in result["endpoints_touched"]
    assert "POST /login" in result["endpoints_touched"]
    assert result["endpoints_touched"] == sorted(result["endpoints_touched"])


def test_handlers_discovery():
    """Test that handlers are correctly discovered from diff."""
    diff = """--- a/src/handlers.py
+++ b/src/handlers.py
@@ -1,3 +1,5 @@
+def handle_order(request):
+export function submit(data) {
 # existing code
"""
    result = discover_surfaces([], diff)
    
    assert "handlers_touched" in result
    assert "handle_order" in result["handlers_touched"]
    assert "submit" in result["handlers_touched"]
    assert result["handlers_touched"] == sorted(result["handlers_touched"])


def test_jobs_discovery():
    """Test that jobs are correctly discovered from diff."""
    diff = """--- a/src/jobs/cleanup.ts
+++ b/src/jobs/cleanup.ts
@@ -1,3 +1,4 @@
+cron.schedule("0 0 * * *", () => {
 # existing code
"""
    result = discover_surfaces([], diff)
    
    assert "jobs_touched" in result
    assert "cron@src/jobs/cleanup.ts" in result["jobs_touched"]


def test_determinism():
    """Test that calling twice with same inputs produces identical results."""
    changed_files = ["src/api/routes.py"]
    diff = """--- a/src/api/routes.py
+++ b/src/api/routes.py
@@ -1,3 +1,4 @@
+router.get("/users")
+def handle_request(req):
 # existing code
"""
    result1 = discover_surfaces(changed_files, diff)
    result2 = discover_surfaces(changed_files, diff)
    
    assert result1 == result2
    assert result1["endpoints_touched"] == result2["endpoints_touched"]
    assert result1["handlers_touched"] == result2["handlers_touched"]
    assert result1["jobs_touched"] == result2["jobs_touched"]


def test_negative():
    """Test that diff with no patterns returns empty lists."""
    diff = """--- a/src/config.py
+++ b/src/config.py
@@ -1,3 +1,4 @@
+DEBUG = True
+TIMEOUT = 30
 # existing code
"""
    result = discover_surfaces([], diff)
    
    assert result["endpoints_touched"] == []
    assert result["handlers_touched"] == []
    assert result["jobs_touched"] == []

