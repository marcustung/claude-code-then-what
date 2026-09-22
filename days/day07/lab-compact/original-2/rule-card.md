# RULE-01
marker: RULE-CONTEXT-7-KITE-0911
version: demo-v2
scope: Single synthetic rejected-to-interview guard.
rule: Direct return from rejected is forbidden. Explicit authorized reopening is allowed only when both reopenRequested and authorized are true. Non-rejected states are outside this guard.
reason: Direct return bypasses the rejection decision; explicit authorized reopening records a deliberate exception.
unknowns: Actual authorization source, audit storage, API and other state rules are not provided. Do not invent them.
