# Day12 integration demonstration
Read plan.md and specs/rules-v2.md. RefundRequested is a request flag, not a payment.
This NEW fixture allows verification commands; the earlier Domain-only demonstration restrictions do not apply.
Verification: dotnet run --project tests/DomainTests (seven PASS); python verify-integration.py <unused-name> (11 checks, pass true).
Verifier must not edit source/tests/spec/runner. Repair may edit ONLY src/Api/Program.cs.
No new dependencies, real payments, network services beyond the loopback fixture, or altered acceptance criteria.
Stop on environmental failure or need for new business decisions. Tool output is evidence, self-report is not.
