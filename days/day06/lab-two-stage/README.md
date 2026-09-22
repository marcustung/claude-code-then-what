# Day 6 兩階段需求澄清驗證

事前固定 protocol.md，再以 run.py 執行兩次獨立 Claude CLI 呼叫。第二次明確讀 previous-draft.md 與 decision.md。

[事前判準](protocol.md)｜[逐項核對](review.md)｜[第一階段原回答](stage1-answer.md)｜[第二階段原回答](stage2-answer.md)

完整 prompt、trace、result 與 meta 保留於本目錄。僅 Read，無 plugin/MCP，不修改實作。與旁邊 Claude Code 的 draft/impl 實驗不同，不能混為同一次。
run.py 是歷史執行腳本，重跑請複製至新目錄，避免覆蓋這次輸出。教學輸入已縮寫，非 Day 3 原始 prompt 的逐字重跑。
