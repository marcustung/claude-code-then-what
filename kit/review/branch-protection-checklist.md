# Branch protection 清單（GitHub）

放了 CODEOWNERS 不會擋合併；下面每一項都要勾到，Owner 審查才是合併條件。

- [ ] Require a pull request before merging
- [ ] Required approvals ≥ 1
- [ ] Require review from Code Owners
- [ ] Dismiss stale approvals when new commits are pushed
- [ ] Require status checks to pass：列出 CI 工作名稱（編譯、測試、靜態／安全掃描）
- [ ] Require branches to be up to date before merging
- [ ] Do not allow bypassing the above settings（核對誰有 admin／bypass 權限，列出來）
- [ ] AI reviewer 的帳號只有 comment 權限，不在 approvers 名單
- [ ] 每季核對一次：實際被繞過的合併有幾次、誰、為什麼
