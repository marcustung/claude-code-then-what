"""Read-only receiver query for this incident. GET /receipt only."""
import json, os, sys
sys.path.insert(0, os.environ["LAB_CONTROLLER_DIR"])
from controller import http
try:
    print(json.dumps(http(os.environ["RECEIVER_BASE"], "/receipt"), ensure_ascii=False, indent=2))
except Exception as e:
    print(json.dumps({"query_error": type(e).__name__, "detail": str(e)}, ensure_ascii=False)); sys.exit(1)
