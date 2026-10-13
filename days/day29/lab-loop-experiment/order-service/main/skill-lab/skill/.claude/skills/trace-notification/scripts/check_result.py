"""Validate a teaching result contract. No network, model call or approval."""
import json
from pathlib import Path

def check(result, task, evidence):
    errors = []
    def add(code):
        if code not in errors: errors.append(code)
    if not isinstance(result, dict): return ["RESULT_OBJECT_REQUIRED"]
    for key in ("schema_version", "order_id", "notification_id", "version", "sender_status", "receiver_status", "evidence_refs", "missing_sources", "next_action"):
        if key not in result: add("MISSING_" + key.upper())
    if result.get("schema_version") != 1: add("SCHEMA_VERSION")
    for key in ("order_id", "notification_id", "version"):
        if result.get(key) != task[key]: add(key.upper() + "_MISMATCH")
    for side in ("sender", "receiver"):
        if result.get(side + "_status") not in ("confirmed", "unknown"): add(side.upper() + "_STATUS")
    missing = result.get("missing_sources")
    if not isinstance(missing, list) or any(not isinstance(x,str) or not x.strip() for x in missing): add("MISSING_SOURCES_TYPE")
    if not isinstance(result.get("next_action"), str) or not result["next_action"].strip(): add("NEXT_ACTION_REQUIRED")
    refs = result.get("evidence_refs")
    if not isinstance(refs, list) or any(not isinstance(x,str) for x in refs):
        add("EVIDENCE_REFS_TYPE"); refs = []
    known = {x["ref"]:x for x in evidence["records"]}
    if any(ref not in known for ref in refs): add("UNKNOWN_SOURCE_REF")
    for side,event in (("sender","notify_sent"),("receiver","notification_received")):
        if result.get(side + "_status") == "confirmed":
            matches = [known[x] for x in refs if x in known and known[x].get("side")==side and known[x].get("event")==event
                and all(known[x].get(k)==task[k] for k in ("order_id","notification_id","version"))]
            if not matches: add(side.upper() + "_EVIDENCE_REQUIRED")
    if result.get("receiver_status")=="unknown" and not missing: add("UNKNOWN_NEEDS_MISSING_SOURCE")
    if result.get("receiver_status")=="confirmed" and missing: add("CONFIRMED_WITH_MISSING_SOURCE")
    return errors

def evaluate(result,task,evidence):
    errors=check(result,task,evidence)
    state="RETURN_FOR_EVIDENCE" if errors else ("NEEDS_FOLLOWUP" if result["receiver_status"]=="unknown" else "READY_FOR_REVIEW")
    return {"state":state,"contract_passed":not errors,"errors":errors,"approved":False,"action_executed":False}

if __name__=="__main__":
    import sys
    try:
        result,task,evidence=[json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:4]]
        output=evaluate(result,task,evidence)
    except (ValueError,KeyError,TypeError,OSError) as exc:
        output={"state":"INPUT_ERROR","contract_passed":False,"errors":[type(exc).__name__],"approved":False,"action_executed":False}
    print(json.dumps(output,ensure_ascii=False,indent=2))
    sys.exit(0 if output["contract_passed"] else 1)
