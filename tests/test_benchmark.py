"""Tests for the stealth benchmark harness (backend/benchmark.py).

All browser interaction is faked — these run without Chromium or a network.
"""
from pathlib import Path

from backend.benchmark import (
    BenchmarkResult,
    BenchmarkTarget,
    TARGETS,
    build_summary_table,
    interpret_evaluation,
    parse_args,
    run_target,
    select_targets,
)


# ── Target catalogue ─────────────────────────────────────────────────────────
def test_targets_integrity():
    names = [t.name for t in TARGETS]
    assert len(names) == len(set(names)), "detector names must be unique"
    for t in TARGETS:
        assert t.url.startswith("https://")
        assert t.evaluator_js is None or isinstance(t.evaluator_js, str)


# ── interpret_evaluation ─────────────────────────────────────────────────────
def test_interpret_all_green_is_pass():
    r = interpret_evaluation({"passed": 29, "failed": 0})
    assert r["status"] == "pass"
    assert (r["passed"], r["failed"], r["total"]) == (29, 0, 29)


def test_interpret_any_failure_is_fail():
    r = interpret_evaluation({"passed": 25, "failed": 4})
    assert r["status"] == "fail"
    assert r["total"] == 29


def test_interpret_zero_checks_degrades_to_loaded():
    assert interpret_evaluation({"passed": 0, "failed": 0})["status"] == "loaded"


def test_interpret_verdict_good_and_bad():
    assert interpret_evaluation({"verdict": "Trustworthy"})["status"] == "pass"
    assert interpret_evaluation({"verdict": "Human"})["status"] == "pass"
    assert interpret_evaluation({"verdict": "Bot detected"})["status"] == "fail"
    assert interpret_evaluation({"verdict": "Suspicious"})["status"] == "fail"


def test_interpret_score_only_is_loaded():
    r = interpret_evaluation({"score": "72%"})
    assert r["status"] == "loaded" and r["score"] == "72%"


def test_interpret_none_or_garbage_never_raises():
    for bad in (None, "nope", 42, {}):
        assert interpret_evaluation(bad)["status"] == "loaded"


# ── summary table ────────────────────────────────────────────────────────────
def test_build_summary_table():
    results = [
        BenchmarkResult(name="sannysoft", url="u", status="pass", detail="29/29 checks green"),
        BenchmarkResult(name="iphey", url="u", status="fail", detail="Suspicious"),
        BenchmarkResult(name="rebrowser", url="u", status="loaded", detail="artifact saved"),
    ]
    table = build_summary_table(results)
    assert "sannysoft" in table and "PASS" in table
    assert "iphey" in table and "FAIL" in table
    assert "1/2 auto-scored detectors passed" in table
    assert "3 visited" in table


def test_build_summary_table_shows_error_detail():
    results = [BenchmarkResult(name="x", url="u", status="error", error="nav failed")]
    assert "nav failed" in build_summary_table(results)


# ── target selection & args ──────────────────────────────────────────────────
def test_select_targets():
    assert len(select_targets(None)) == len(TARGETS)
    assert len(select_targets([])) == len(TARGETS)
    picked = select_targets(["sannysoft", "IPHEY"])  # case-insensitive
    assert {t.name for t in picked} == {"sannysoft", "iphey"}
    assert select_targets(["does-not-exist"]) == []


def test_parse_args():
    a = parse_args([])
    assert a.dry_run is False and a.headless is False and a.only is None
    a2 = parse_args(["--dry-run", "--headless", "--only", "sannysoft", "creepjs", "--timeout", "1000"])
    assert a2.dry_run is True and a2.headless is True
    assert a2.only == ["sannysoft", "creepjs"] and a2.timeout == 1000


# ── run_target with a faked browser ──────────────────────────────────────────
class _FakePage:
    def __init__(self, eval_results):
        self._eval_results = list(eval_results)
        self.screenshots: list[str] = []

    async def screenshot(self, path, full_page=False):
        self.screenshots.append(path)
        Path(path).write_bytes(b"PNG")

    async def evaluate(self, js):
        val = self._eval_results.pop(0)
        if isinstance(val, Exception):
            raise val
        return val


class _FakeBC:
    def __init__(self, page):
        self.page = page
        self.goto_calls: list[str] = []

    async def goto(self, url, wait_until="networkidle", timeout=45000):
        self.goto_calls.append(url)
        return True


async def test_run_target_scores_and_writes_artifacts(tmp_path):
    # evaluate() runs twice: innerText, then the evaluator JS.
    page = _FakePage(["some page text", {"passed": 29, "failed": 0}])
    bc = _FakeBC(page)
    target = BenchmarkTarget("sannysoft", "https://bot.sannysoft.com/", settle_s=0, evaluator_js="() => ({})")
    res = await run_target(bc, target, tmp_path)
    assert res.status == "pass" and res.passed == 29
    assert (tmp_path / "sannysoft.png").exists()
    assert (tmp_path / "sannysoft.txt").read_text() == "some page text"
    assert bc.goto_calls == ["https://bot.sannysoft.com/"]


async def test_run_target_handles_goto_error(tmp_path):
    class _BoomBC:
        page = _FakePage([])

        async def goto(self, *a, **k):
            raise RuntimeError("nav failed")

    res = await run_target(_BoomBC(), BenchmarkTarget("x", "https://x", settle_s=0), tmp_path)
    assert res.status == "error" and "nav failed" in res.error


async def test_run_target_evaluator_error_still_saves_artifacts(tmp_path):
    page = _FakePage(["text", ValueError("bad js")])
    bc = _FakeBC(page)
    target = BenchmarkTarget("iphey", "https://iphey.com/", settle_s=0, evaluator_js="() => x")
    res = await run_target(bc, target, tmp_path)
    assert res.status == "loaded"  # evaluator failed -> artifact-only, not a crash
    assert (tmp_path / "iphey.png").exists()
