# SYNTHETIC spec v1
REQ-01: Let users cancel orders that have not shipped yet.
Interface: Order(bool Shipped, bool Paid, bool Cancelled); CancellationResult(Order Order, bool RefundRequested).
LIMIT-01: No dependencies, network, files, payments, or other side effects. RefundRequested is only an in-memory flag.
This is a public synthetic teaching task, not company policy.
