"""新增對照：本機 marketplace，命令列明確允許三支教學腳本。
沿用既有輸入與 Skill；不覆寫歷史結果，不跳過權限檢查。
"""
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("handoff", Path(__file__).with_name("run-handoff.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.SCEN["marketplace-authorized"] = dict(
    case="complete", tools=m.READ + ["Write", "Bash"],
    allow=m.READ + m.WRITE + m.TEAM_ALLOW, full=False, market=True)
if __name__ == "__main__":
    m.run("marketplace-authorized")
