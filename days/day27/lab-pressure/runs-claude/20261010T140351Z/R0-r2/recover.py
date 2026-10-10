"""Dedicated recovery entry. Reads the operator policy itself; the caller cannot change it."""
import json, os, sys, argparse
from datetime import datetime, timezone
sys.path.insert(0, os.environ["LAB_CONTROLLER_DIR"])
from controller import recover
ap = argparse.ArgumentParser(); ap.add_argument("--reason", required=True); a = ap.parse_args()
policy = json.load(open(os.environ["OPERATOR_POLICY"], encoding="utf-8"))
state_path = os.environ["OPERATOR_STATE"]
state = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {"attempts": 0}
payload = json.loads(os.environ["LAB_PAYLOAD"]); audit = []
result = recover(os.environ["RECEIVER_BASE"], payload, policy, state, audit, proposed=a.reason)
json.dump(state, open(state_path, "w", encoding="utf-8"))
with open(os.environ["OPERATOR_AUDIT"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "reason": a.reason, "result": result}, ensure_ascii=False) + "\n")
print(json.dumps({"action": result["action"], "reason": result["reason"]}, ensure_ascii=False))
