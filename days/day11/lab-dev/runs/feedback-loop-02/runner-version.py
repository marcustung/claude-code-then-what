"""Bounded Claude Code proposal/test loop; historical runs remain immutable.
Claude has read-only tools. The host writes only the Domain file in a fresh copy.
This is a local teaching runner, not an OS sandbox or deployment approval.
"""
from pathlib import Path
import argparse, subprocess, shutil, json, re, hashlib, difflib, time
ROOT = Path(__file__).resolve().parent
TARGET = "src/Domain/Cancellation.cs"

def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and not {"bin", "obj"}.intersection(p.relative_to(root).parts)}

def tests(work, out):
    try:
        p = subprocess.run(["dotnet", "run", "--project", "tests/DomainTests"], cwd=work,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        log = p.stdout + p.stderr
        out.write_text(log, encoding="utf-8")
        return p.returncode, log
    except subprocess.TimeoutExpired:
        out.write_text("TEST_TIMEOUT", encoding="utf-8")
        return 124, "TEST_TIMEOUT"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--max-rounds", type=int, choices=range(1,4), default=3)
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", a.name): ap.error("simple unique name required")
    out = ROOT / "runs" / a.name
    out.mkdir(exist_ok=False)
    work = out / "workspace"
    shutil.copytree(ROOT / "runs/tests/snapshot", work)
    (out / "mcp.json").write_text('{"mcpServers":{}}', encoding="utf-8")
    baseline = snapshot(work)
    code, feedback = tests(work, out / "baseline-tests.txt")
    report = {"case": "teaching rule change", "max_rounds": a.max_rounds, "baseline_exit": code,
              "human_minutes": None, "rounds": [], "status": "NOT_STARTED"}
    def save(): (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not (code == 1 and "FAIL SC-03" in feedback and feedback.count("FAIL SC-") == 1):
        report["status"] = "UNEXPECTED_BASELINE"; save(); return 1
    cli = shutil.which("claude.exe") or shutil.which("claude")
    if not cli: report["status"] = "CLAUDE_NOT_FOUND"; save(); return 1
    for i in range(1, a.max_rounds + 1):
        rd = out / f"round-{i:02d}"; rd.mkdir()
        prompt = """Read CLAUDE.md, plan.md, specs/rules-v2.md, tests/DomainTests/Program.cs and src/Domain/Cancellation.cs.
Implement ONLY the Domain rule change confirmed in rules-v2. Keep type signatures and shipped-order behavior. No real payments, API changes or test changes.
This is a new implementation-phase demonstration; the tests have already been established. Historical plan's test-writing step is complete.
You have read-only tools. Return a JSON object only, with status (proposal or needs_decision), reason, and content (the complete Cancellation.cs file for proposal).
The host applies content ONLY to src/Domain/Cancellation.cs and executes the fixed tests. Failed execution results will be sent to your next round.
If acceptance criteria conflict or you require other files changed, return needs_decision instead. Do not claim you executed tests.
Latest actual runner output:\n""" + feedback
        (rd / "prompt.txt").write_text(prompt, encoding="utf-8")
        args = [cli, "-p", "--model", "sonnet", "--effort", "medium", "--setting-sources", "project",
                "--strict-mcp-config", "--mcp-config", str(out / "mcp.json"),
                "--tools", "Read,Grep,Glob", "--allowedTools", "Read,Grep,Glob",
                "--no-session-persistence", "--output-format", "stream-json", "--verbose"]
        before = snapshot(work); start = time.monotonic(); result = None
        with (rd / "trace.jsonl").open("w", encoding="utf-8") as o, (rd / "stderr.txt").open("w", encoding="utf-8") as e:
            try:
                proc = subprocess.run(args, input=prompt, cwd=work, text=True, encoding="utf-8", stdout=o, stderr=e, timeout=300)
            except subprocess.TimeoutExpired:
                report["status"] = "MODEL_TIMEOUT"; save(); return 1
        for line in (rd / "trace.jsonl").read_text(encoding="utf-8").splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            if event.get("type") == "result": result = event
        item = {"round": i, "elapsed_seconds": time.monotonic()-start, "model_exit": proc.returncode,
                "model_result": result}
        report["rounds"].append(item)
        if snapshot(work) != before:
            report["status"] = "UNEXPECTED_MODEL_WRITE"; save(); return 1
        if proc.returncode or not result or result.get("is_error"):
            report["status"] = "MODEL_ERROR"; save(); return 1
        raw = result.get("result", "").strip()
        (rd / "result.txt").write_text(raw, encoding="utf-8")
        blocks = re.findall(r"```json\s*([\s\S]*?)```", raw)
        if len(blocks) == 1:
            raw = blocks[0].strip()
        try:
            proposal = json.loads(raw)
            if proposal.get("status") == "needs_decision":
                report["status"] = "NEEDS_DECISION"; save(); return 2
            assert proposal.get("status") == "proposal" and isinstance(proposal.get("content"), str)
            assert proposal["content"].strip()
        except (ValueError, AssertionError, AttributeError):
            report["status"] = "INVALID_PROPOSAL"; save(); return 1
        (work / TARGET).write_text(proposal["content"], encoding="utf-8")
        after = snapshot(work)
        changed = sorted(k for k in baseline.keys() | after.keys() if baseline.get(k) != after.get(k))
        item["changed_from_baseline"] = changed
        item["protected_files_unchanged"] = all(after.get(k) == v for k,v in baseline.items() if k != TARGET)
        if changed != [TARGET] or not item["protected_files_unchanged"]:
            report["status"] = "SCOPE_REJECTED"; save(); return 1
        (rd / "diff.patch").write_text("".join(difflib.unified_diff(before[TARGET].decode("utf-8").splitlines(True),
                after[TARGET].decode("utf-8").splitlines(True), fromfile="before", tofile="after")), encoding="utf-8")
        code, feedback = tests(work, rd / "tests.txt")
        item["test_exit"] = code
        item["tests_sha256"] = hashlib.sha256(after["tests/DomainTests/Program.cs"]).hexdigest()
        save()
        print(f"round={i} exit={code} protected={item['protected_files_unchanged']}", flush=True)
        if code == 0 and feedback.count("PASS SC-") == 7 and "FAIL SC-" not in feedback:
            report["status"] = "CHECKS_PASSED"; save(); return 0
        if code != 1 or "FAIL SC-" not in feedback:
            report["status"] = "ENVIRONMENT_OR_BUILD_ERROR"; save(); return 1
    report["status"] = "ROUND_LIMIT"; save(); return 2

if __name__ == "__main__": raise SystemExit(main())
