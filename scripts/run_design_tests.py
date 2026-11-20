#!/usr/bin/env python3
# Copyright(c) 2026 Lattice Semiconductor Corporation. All rights reserved. DO NOT DISTRIBUTE.
# Subject to the terms of the AI Solutions Software License Agreement
"""
Compile Diamond projects from the design-migration repository through the MCP server's own tools, and write a summary.

    python scripts/run_design_tests.py --list
    python scripts/run_design_tests.py --family xo3 --limit 3
    python scripts/run_design_tests.py --select uart --select rd1005
    python scripts/run_design_tests.py --family all --out results/

Every design is copied to a scratch folder first, so the originals are never modified. Each design gets a fresh
Diamond session and one call to the server's compile_project tool (open, Synthesis, Translate, Map, PAR, Bitgen).
The summary (summary.md, results.json) is meant to be pasted into docs/Test_Summary.md.

Families are taken from the device in the .ldf: xo2 (LCMXO2), xo3 (LCMXO3L, LCMXO3LF, LAMXO3LF), xo3d (LCMXO3D),
other (anything else, left out unless asked for). Projects under tests/fixtures are test inputs of the migration
tool, not designs, and are always left out.

Needs the project's dependencies importable (run it from the project's environment), a Diamond installation and a
licence. Designs run one at a time, so a single licence seat is enough. Exit status 1 if any design failed.
A design passes when the flow completes; whether its own timing constraints were met is reported separately.
"""

import argparse
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from diamond_mcp import discovery, project as prj, server  # noqa: E402

DEFAULT_ROOT = REPO.parent / "design-migration"
FAMILIES = ("xo2", "xo3", "xo3d", "other")
SKIPPED_DIRS = ("tests/fixtures/",)
MAX_LEVELS_UP = 4
ERROR_LINES = 6
TIMING = {True: "yes", False: "no", None: "n/a"}


def family_of(device):
    d = (device or "").upper()
    if d.startswith("LCMXO3D"):
        return "xo3d"
    if d.startswith(("LCMXO3L", "LAMXO3L")):
        return "xo3"
    if d.startswith("LCMXO2-"):
        return "xo2"
    return "other"


def find_designs(root):
    designs = []
    for ldf in sorted(root.rglob("*.ldf")):
        rel = ldf.relative_to(root).as_posix()
        if any(s in rel for s in SKIPPED_DIRS):
            continue
        try:
            device = prj.parse_ldf(str(ldf)).get("device")
        except Exception as exc:  # an unreadable project is still reported, under "other"
            device = None
            rel_note = str(exc)[:80]
        else:
            rel_note = ""
        designs.append({"ldf": ldf, "rel": rel, "device": device, "family": family_of(device), "note": rel_note})
    return designs


def design_root(ldf):
    """The folder to copy: the closest one holding the .ldf and every relative source the project names."""
    folder = ldf.parent
    for src in prj._load(str(ldf)).iter("Source"):
        name = src.get("name", "")
        if not name or Path(name).is_absolute():
            continue
        target = Path(os.path.normpath(ldf.parent / name))
        while folder != folder.parent and folder not in target.parents:
            folder = folder.parent
    return folder


def pick_exe(version):
    found = discovery.discover_diamond_installations()
    if version:
        found = [i for i in found if i.version.startswith(version) or i.version.replace("_", ".").startswith(version)]
    if not found:
        raise SystemExit(f"No Diamond installation matching '{version}' was found. Set DIAMOND_EXE or use --diamond-version.")
    return found[0]


def short_error(result):
    text = str(result.get("output") or result.get("message") or result.get("error") or "")
    lines = [l.strip() for l in text.splitlines() if re.search(r"error|fail|unsupported|license|licence", l, re.I)]
    return " | ".join((lines or text.splitlines() or ["no message"])[:ERROR_LINES])[:600]


def run_one(design, work, args):
    started = time.monotonic()
    row = {"design": design["rel"], "device": design["device"], "family": design["family"]}
    root = design_root(design["ldf"])
    target = work / re.sub(r"[^A-Za-z0-9_.-]", "_", design["rel"])
    try:
        shutil.copytree(root, target / root.name)
        ldf = target / root.name / design["ldf"].relative_to(root)
        server._set_session(None)
        result = server.compile_project(str(ldf), bitstream=not args.no_bitstream, timeout=args.timeout)
        row["success"] = bool(result.get("success"))
        row["stages"] = {s["stage"]: ("ok" if s["success"] else "FAILED") for s in result.get("stages", [])}
        if row["success"]:
            par = (result.get("timing") or {}).get("par") or {}
            row["par_status"] = par.get("run_status")
            row["bitstream"] = any(f.endswith(".bit") for f in result.get("bitstream_files", []))
            row["timing"] = result.get("timing")
            twr = (result.get("timing") or {}).get("twr") or {}
            row["timing_met"] = (twr.get("setup_preferences_met") and twr.get("hold_preferences_met")) if twr else None
            row["resources"] = result.get("resources")
        else:
            row["failed_stage"] = result.get("failed_stage") or "before the flow"
            row["error"] = short_error(result)
    except Exception as exc:  # a crash of one design must not stop the run
        row["success"] = False
        row["failed_stage"] = "harness"
        row["error"] = f"{type(exc).__name__}: {exc}"[:600]
    finally:
        session = server._SESSION
        if session is not None:
            try:
                session.stop()
            except Exception:
                pass
        server._set_session(None)
        if not args.keep_work:
            shutil.rmtree(target, ignore_errors=True)
    row["seconds"] = round(time.monotonic() - started, 1)
    return row


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True,
                              timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def markdown(rows, meta):
    out = ["# Design test results", ""]
    out += [f"- Date: {meta['date']}", f"- Host: {meta['host']}",
            f"- Diamond: {meta['diamond']}", f"- Server commit: {meta['commit']}",
            f"- Source: `{meta['root']}`", f"- Bitstream generated: {'no' if meta['no_bitstream'] else 'yes'}",
            f"- Per-stage timeout: {meta['timeout']} s", ""]
    passed = sum(1 for r in rows if r["success"])
    out += ["## Totals", "", f"- Designs run: {len(rows)}", f"- Passed: {passed}", f"- Failed: {len(rows) - passed}",
            f"- Flow completed but timing not met: {sum(1 for r in rows if r['success'] and r.get('timing_met') is False)}",
            f"- Total time: {round(sum(r['seconds'] for r in rows) / 60, 1)} min", "",
            "## By family", "", "| Family | Run | Passed | Failed |", "|---|---|---|---|"]
    for fam in FAMILIES:
        sub = [r for r in rows if r["family"] == fam]
        if sub:
            ok = sum(1 for r in sub if r["success"])
            out.append(f"| {fam.upper()} | {len(sub)} | {ok} | {len(sub) - ok} |")
    out += ["", "## By design", "", "| Design | Device | Result | Timing met | Failed stage | Seconds |", "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['design']} | {r['device']} | {'PASS' if r['success'] else 'FAIL'} | "
                   f"{TIMING.get(r.get('timing_met'), 'n/a')} | {r.get('failed_stage', '')} | {r['seconds']} |")
    failed = [r for r in rows if not r["success"]]
    if failed:
        out += ["", "## Failures", ""]
        for r in failed:
            out.append(f"- {r['design']} ({r['device']}), stage {r.get('failed_stage')}: {r.get('error', '')}")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="the design-migration checkout (default: ../design-migration)")
    ap.add_argument("--family", action="append", choices=FAMILIES + ("all",), help="xo2, xo3, xo3d, other or all; may repeat (default: xo2, xo3, xo3d)")
    ap.add_argument("--select", action="append", metavar="TEXT", help="only designs whose path contains TEXT (case-insensitive); may repeat")
    ap.add_argument("--limit", type=int, help="run at most this many designs")
    ap.add_argument("--list", action="store_true", help="list the designs that would run and stop")
    ap.add_argument("--diamond-version", default="3.14", help="Diamond version prefix to use (default: 3.14)")
    ap.add_argument("--timeout", type=float, default=1200, help="seconds allowed per flow stage (default: 1200)")
    ap.add_argument("--no-bitstream", action="store_true", help="stop after PAR")
    ap.add_argument("--out", type=Path, default=Path("design_test_results"), help="folder for summary.md and results.json")
    ap.add_argument("--keep-work", action="store_true", help="keep the scratch copies of the designs")
    args = ap.parse_args()

    root = args.root.resolve()
    args.root = root
    wanted = set(args.family or ["xo2", "xo3", "xo3d"])
    if "all" in wanted:
        wanted = set(FAMILIES)
    designs = [d for d in find_designs(root) if d["family"] in wanted]
    if args.select:
        designs = [d for d in designs if any(s.lower() in d["rel"].lower() for s in args.select)]
    if args.limit:
        designs = designs[: args.limit]

    if args.list:
        for d in designs:
            print(f"{d['family']:5} {d['device'] or '?':26} {d['rel']}")
        print(f"{len(designs)} design(s)")
        return 0
    if not designs:
        print("No designs match.")
        return 1

    install = pick_exe(args.diamond_version)
    os.environ["DIAMOND_EXE"] = install.exe
    print(f"Diamond {install.version} ({install.exe})")
    args.out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="design_tests_"))
    meta = {"date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "host": f"{platform.node()} ({platform.platform()})",
            "diamond": install.version, "commit": git_commit(), "root": str(root),
            "no_bitstream": args.no_bitstream, "timeout": args.timeout}
    rows = []
    try:
        for i, design in enumerate(designs, 1):
            print(f"[{i}/{len(designs)}] {design['rel']} ...", flush=True)
            row = run_one(design, work, args)
            rows.append(row)
            print(f"    {'PASS' if row['success'] else 'FAIL'} in {row['seconds']} s"
                  + ("" if row["success"] else f" ({row.get('failed_stage')}: {row.get('error', '')[:120]})"), flush=True)
            (args.out / "results.json").write_text(json.dumps({"meta": meta, "results": rows}, indent=1))
            (args.out / "summary.md").write_text(markdown(rows, meta))
    finally:
        if args.keep_work:
            print(f"Scratch copies kept in {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    print(f"Wrote {args.out / 'summary.md'}")
    return 0 if all(r["success"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
