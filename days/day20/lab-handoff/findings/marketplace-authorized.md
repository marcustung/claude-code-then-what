# Marketplace 明確授權對照

原件：`../runs/marketplace-authorized-20261004-043435/`。

- 不改 Skill v2.1.2 或 complete fixture，只新增命令列授權對照；歷史 runner 與 runs 保留。
- 自測、安裝與 Skill 載入成功。
- 工具軌跡確認 collect.py 與 gate.py 實際由 Claude 執行。
- Claude gate 與操作者重跑均為 READY_FOR_REVIEW、contract_passed=true、approved=false、action_executed=false。
- 11 回合、36.1 秒、US$0.1367588。單次結果，不估成功率或減載。
- 三次 Bash 被擋：切換到未允許目錄、混合寫檔命令、包含退出碼變數的命令；最後 Write 寫檔與單一 Python 命令成功。
- 未證明舊版 allowed-tools 失敗根因、互動批准、另一台機器或真人接手；不連 Log server、不執行 .NET、不補送。
