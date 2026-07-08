"""Reproducible stealth benchmark for BrowserPilot Ghost Mode.

Instead of trusting committed screenshots, run a real Ghost Mode browser against
public bot-detection sites yourself. For every detector this saves a full-page
screenshot + the page's text to ``outputs/benchmark/`` (so any result is
verifiable by eye), and prints an automated pass/fail summary for the detectors
that expose a machine-readable result.

Usage:
    python -m backend.benchmark                      # run every detector
    python -m backend.benchmark --only sannysoft     # run a subset
    python -m backend.benchmark --dry-run            # list targets, launch nothing
    python -m backend.benchmark --headless           # for servers without a display

The pure helpers (interpret_evaluation, build_summary_table, select_targets,
parse_args) are import-safe and browser-free so they can be unit-tested without
launching Chromium; BrowserController is imported lazily only when a run starts.
"""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

DEFAULT_OUT_DIR = Path("outputs/benchmark")
DEFAULT_TIMEOUT_MS = 45000
MAX_TEXT_CHARS = 20000


# ── Detector definitions ─────────────────────────────────────────────────────
# Each evaluator is a JS function evaluated in the page. It must return a
# JSON-serializable dict shaped like one of:
#   {"passed": int, "failed": int}   -> counted checks (e.g. sannysoft)
#   {"verdict": str}                 -> a human/bot label (e.g. iphey)
#   {"score": str}                   -> a freeform score (e.g. creepjs trust %)
# Detectors with no evaluator are captured as artifacts only (status "loaded").

_SANNYSOFT_JS = """
() => {
  // sannysoft reports each check as text in a results cell: "passed", "ok", or
  // "... (passed)" for good; anything containing "failed" for bad. Neutral value
  // cells (user agent, plugin count, etc.) are ignored.
  const cells = Array.from(document.querySelectorAll('td'));
  let passed = 0, failed = 0;
  for (const c of cells) {
    const t = c.textContent.trim().toLowerCase();
    if (!t) continue;
    if (t.includes('failed')) failed++;
    else if (t === 'passed' || t === 'ok' || t.includes('(passed)')) passed++;
  }
  return { passed, failed };
}
"""

_DEVICEINFO_JS = """
() => {
  const t = (document.body ? document.body.innerText : '').toLowerCase();
  let verdict = null;
  if (t.includes('not a bot') || t.includes('are a human') || t.includes('you are human')) verdict = 'Human';
  else if (t.includes('you are a bot') || t.includes('bot detected')) verdict = 'Bot';
  return { verdict };
}
"""

@dataclass(frozen=True)
class BenchmarkTarget:
    name: str
    url: str
    wait_until: str = "networkidle"
    settle_s: float = 3.0
    evaluator_js: Optional[str] = None


TARGETS: list[BenchmarkTarget] = [
    BenchmarkTarget("sannysoft", "https://bot.sannysoft.com/", evaluator_js=_SANNYSOFT_JS),
    BenchmarkTarget("deviceandbrowserinfo", "https://deviceandbrowserinfo.com/are_you_a_bot", evaluator_js=_DEVICEINFO_JS),
    # iphey/creepjs render their verdict in ways that aren't reliably readable from
    # body text (article boilerplate contains "suspicious"; creepjs scores slowly),
    # so they are captured as artifacts for visual inspection rather than auto-scored.
    BenchmarkTarget("iphey", "https://iphey.com/", settle_s=4.0),
    BenchmarkTarget("creepjs", "https://abrahamjuliot.github.io/creepjs/", settle_s=8.0),
    BenchmarkTarget("rebrowser", "https://bot-detector.rebrowser.net/"),
    BenchmarkTarget("browserscan", "https://www.browserscan.net/"),
    BenchmarkTarget("pixelscan", "https://pixelscan.net/", settle_s=6.0),
    BenchmarkTarget("browserleaks-webrtc", "https://browserleaks.com/webrtc"),
]


@dataclass
class BenchmarkResult:
    name: str
    url: str
    status: str = "pending"  # pass | fail | loaded | error | pending
    passed: Optional[int] = None
    failed: Optional[int] = None
    total: Optional[int] = None
    score: Optional[str] = None
    detail: str = ""
    screenshot: Optional[str] = None
    text_file: Optional[str] = None
    error: Optional[str] = None


# ── Pure logic (browser-free, unit-tested) ───────────────────────────────────
_GOOD_WORDS = ("human", "trustworthy", "not a bot", "clean", "normal")
_BAD_WORDS = ("bot", "suspicious", "detected", "fail", "automation")


def interpret_evaluation(raw: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Normalize a detector's raw evaluator output into result fields.

    Returns a dict with keys: status, passed, failed, total, score, detail.
    Never raises — unknown shapes degrade to a "loaded" (artifact-only) result.
    """
    out: dict[str, Any] = {
        "status": "loaded", "passed": None, "failed": None,
        "total": None, "score": None, "detail": "artifact saved — inspect screenshot",
    }
    if not isinstance(raw, dict):
        return out

    if raw.get("passed") is not None and raw.get("failed") is not None:
        p, f = int(raw["passed"]), int(raw["failed"])
        total = int(raw.get("total", p + f))
        out.update(passed=p, failed=f, total=total)
        if total == 0:
            out.update(status="loaded", detail="no scored checks found — inspect screenshot")
        elif f == 0:
            out.update(status="pass", detail=f"{p}/{total} checks green")
        else:
            out.update(status="fail", detail=f"{f}/{total} checks failed")
        return out

    verdict = raw.get("verdict")
    if verdict:
        v = str(verdict)
        low = v.lower()
        good = any(w in low for w in _GOOD_WORDS)
        bad = any(w in low for w in _BAD_WORDS)
        out.update(score=v, detail=v)
        out["status"] = "pass" if (good and not bad) else ("fail" if bad else "loaded")
        return out

    score = raw.get("score")
    if score:
        out.update(status="loaded", score=str(score), detail=f"trust={score}")
        return out

    return out


_STATUS_LABEL = {
    "pass": "PASS", "fail": "FAIL", "loaded": "LOADED",
    "error": "ERROR", "pending": "PENDING",
}


def build_summary_table(results: list[BenchmarkResult]) -> str:
    """Render a fixed-width summary table. Pure — safe to snapshot in tests."""
    name_w = max([len("DETECTOR")] + [len(r.name) for r in results]) if results else len("DETECTOR")
    header = f"{'DETECTOR'.ljust(name_w)}  {'RESULT'.ljust(8)}  DETAIL"
    line = "-" * len(header)
    rows = []
    for r in results:
        label = _STATUS_LABEL.get(r.status, r.status.upper())
        detail = r.error or r.detail or ""
        rows.append(f"{r.name.ljust(name_w)}  {label.ljust(8)}  {detail}")
    passed = sum(1 for r in results if r.status == "pass")
    scored = sum(1 for r in results if r.status in ("pass", "fail"))
    footer = f"{passed}/{scored} auto-scored detectors passed · {len(results)} visited"
    return "\n".join(
        ["BrowserPilot Ghost Mode — Stealth Benchmark", line, header, line, *rows, line, footer]
    )


def select_targets(only: Optional[list[str]], targets: list[BenchmarkTarget] = TARGETS) -> list[BenchmarkTarget]:
    """Filter targets by name (case-insensitive). Empty/None -> all targets."""
    if not only:
        return list(targets)
    wanted = {name.lower() for name in only}
    return [t for t in targets if t.name.lower() in wanted]


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m backend.benchmark",
        description="Run BrowserPilot Ghost Mode against public bot-detection sites.",
    )
    p.add_argument("--only", nargs="*", metavar="NAME",
                   help=f"Run only these detectors (choices: {', '.join(t.name for t in TARGETS)})")
    p.add_argument("--headless", action="store_true", help="Run headless (servers without a display)")
    p.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="Artifact output directory")
    p.add_argument("--dry-run", action="store_true", help="List selected targets and exit (no browser)")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_MS, help="Per-page navigation timeout (ms)")
    return p.parse_args(argv)


# ── Browser-touching runner ──────────────────────────────────────────────────
async def run_target(bc: Any, target: BenchmarkTarget, out_dir: Path, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> BenchmarkResult:
    """Navigate to one detector, save artifacts, and score it.

    ``bc`` is any object exposing async ``goto(url, wait_until, timeout)`` and a
    ``page`` with async ``screenshot`` / ``evaluate`` (a real BrowserController
    in production, a fake in tests).
    """
    res = BenchmarkResult(name=target.name, url=target.url)
    try:
        await bc.goto(target.url, wait_until=target.wait_until, timeout=timeout_ms)
        await asyncio.sleep(target.settle_s)

        shot = out_dir / f"{target.name}.png"
        try:
            await bc.page.screenshot(path=str(shot), full_page=True)
            res.screenshot = str(shot)
        except Exception as e:  # a screenshot failure must not sink the whole run
            res.detail = f"screenshot failed: {e}"

        try:
            text = await bc.page.evaluate("() => document.body ? document.body.innerText : ''")
            tf = out_dir / f"{target.name}.txt"
            tf.write_text(str(text)[:MAX_TEXT_CHARS], encoding="utf-8")
            res.text_file = str(tf)
        except Exception:
            pass

        raw = None
        if target.evaluator_js:
            try:
                raw = await bc.page.evaluate(target.evaluator_js)
            except Exception as e:
                res.detail = f"evaluator error: {e}"

        norm = interpret_evaluation(raw)
        res.status = norm["status"]
        res.passed, res.failed, res.total = norm["passed"], norm["failed"], norm["total"]
        res.score = norm["score"]
        if not res.detail:
            res.detail = norm["detail"]
    except Exception as e:
        res.status = "error"
        res.error = str(e)
    return res


async def run_benchmark(targets: list[BenchmarkTarget], out_dir: Path,
                        headless: bool = False, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> list[BenchmarkResult]:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Lazy import: keeps the pure helpers (and their tests) browser-free.
    from backend.browser_controller import BrowserController

    results: list[BenchmarkResult] = []
    async with BrowserController(headless=headless, proxy=None) as bc:
        for target in targets:
            print(f"→ {target.name}: {target.url}")
            results.append(await run_target(bc, target, out_dir, timeout_ms))
    return results


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    targets = select_targets(args.only)
    if not targets:
        print("No matching detectors. Available:", ", ".join(t.name for t in TARGETS))
        return 2

    if args.dry_run:
        pending = [BenchmarkResult(name=t.name, url=t.url, detail=t.url) for t in targets]
        print(build_summary_table(pending))
        return 0

    out_dir = Path(args.out)
    results = asyncio.run(run_benchmark(targets, out_dir, headless=args.headless, timeout_ms=args.timeout))
    print("\n" + build_summary_table(results))
    print(f"\nArtifacts (screenshot + text per detector): {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
