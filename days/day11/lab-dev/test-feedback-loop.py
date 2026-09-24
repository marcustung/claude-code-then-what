"""Controller tests with scripted model responses and real .NET tests.
These are fault-injection checks, NOT additional Claude runs.
"""
import importlib.util, tempfile, shutil, json, sys, subprocess, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("loop", ROOT/"run-feedback-loop.py")
loop=importlib.util.module_from_spec(spec);spec.loader.exec_module(loop)
REAL_RUN=subprocess.run
class ControllerTests(unittest.TestCase):
    def exercise(self, name, proposals, rounds=3):
        with tempfile.TemporaryDirectory(prefix="day11-controller-") as tmp:
            root=Path(tmp)
            shutil.copytree(ROOT/"runs/tests/snapshot",root/"runs/tests/snapshot",ignore=shutil.ignore_patterns("bin","obj"))
            calls=[]
            def run(args, **kw):
                if Path(args[0]).name.lower().startswith("claude"):
                    calls.append(kw["input"])
                    response=proposals[min(len(calls)-1,len(proposals)-1)]
                    kw["stdout"].write(json.dumps({"type":"result","is_error":False,"result":json.dumps(response)}))
                    kw["stdout"].flush()
                    return subprocess.CompletedProcess(args,0)
                return REAL_RUN(args,**kw)
            with patch.object(loop,"ROOT",root),patch.object(sys,"argv",["test",name,"--max-rounds",str(rounds)]),patch.object(loop.subprocess,"run",side_effect=run):
                loop.main()
            report=json.loads((root/"runs"/name/"report.json").read_text(encoding="utf-8"))
            return report,calls
    def test_failure_is_returned_then_success(self):
        old=(ROOT/"runs/tests/snapshot/src/Domain/Cancellation.cs").read_text(encoding="utf-8")+"\n// fault injection: behavior deliberately unchanged\n"
        good=(ROOT/"runs/impl/snapshot/src/Domain/Cancellation.cs").read_text(encoding="utf-8")
        report,calls=self.exercise("retry",[{"status":"proposal","content":old},{"status":"proposal","content":good}])
        self.assertEqual(report["status"],"CHECKS_PASSED")
        self.assertEqual([x["test_exit"] for x in report["rounds"]],[1,0])
        self.assertIn("FAIL SC-03",calls[1])
    def test_round_limit(self):
        old=(ROOT/"runs/tests/snapshot/src/Domain/Cancellation.cs").read_text(encoding="utf-8")+"\n// deliberately unchanged behavior\n"
        report,calls=self.exercise("limit",[{"status":"proposal","content":old}])
        self.assertEqual(report["status"],"ROUND_LIMIT");self.assertEqual(len(calls),3)
    def test_escalation(self):
        report,calls=self.exercise("decision",[{"status":"needs_decision","reason":"synthetic specification conflict"}])
        self.assertEqual(report["status"],"NEEDS_DECISION");self.assertEqual(len(calls),1)
    def test_invalid_response_stops(self):
        report,calls=self.exercise("invalid",[{"status":"proposal","content":None}])
        self.assertEqual(report["status"],"INVALID_PROPOSAL")
if __name__=="__main__": unittest.main()
