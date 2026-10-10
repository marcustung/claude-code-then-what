using System.Text.Json;
using OrderCancel.Domain;

// Loopback teaching receiver. Fault truth is written outside the future model input directory.
var mode = Environment.GetEnvironmentVariable("LAB_CASE") ?? throw new Exception("LAB_CASE required");
var truthPath = Environment.GetEnvironmentVariable("LAB_TRUTH") ?? throw new Exception("LAB_TRUTH required");
var port = int.Parse(Environment.GetEnvironmentVariable("LAB_PORT")!);
var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
var app = builder.Build();
var sync = new object();
var attempts = 0;
var effects = 0;
var inFlight = 0;
Notification? accepted = null;
// Same Domain rule as the series; the experiment narrows the boundary to notification delivery.
var before = new Order(false, true, false);
var cancelled = Cancellation.Cancel(before);
if (!Cancellation.Transitioned(before, cancelled)) throw new Exception("Fixture must be a real transition");
var expected = new Notification("notice-01", "order-01", "request-01", "order_cancelled", cancelled.RefundRequested);
void SaveTruth() => File.WriteAllText(truthPath, JsonSerializer.Serialize(new { mode, attempts, effects, inFlight, accepted }));
SaveTruth();
app.MapGet("/health", () => Results.Ok(new { ok = true }));
app.MapGet("/receipt", () => {
    if (mode == "receipt_unavailable") return Results.Json(new { error = "query_unavailable" }, statusCode: 503);
    lock (sync) return Results.Ok(new {
        source = "receiver", notification_id = expected.NotificationId, order_id = expected.OrderId,
        request_id = expected.RequestId, generation = attempts, attempt_closed = inFlight == 0 && attempts > 0,
        status = effects > 0 ? "completed" : inFlight > 0 ? "in_progress" : attempts > 0 ? "not_completed" : "unknown",
        receipt = accepted
    });
});
app.MapPost("/notify", async (Notification n, HttpContext context) => {
    bool first;
    lock (sync) {
        attempts++;
        if (n != expected) { SaveTruth(); return Results.Json(new { error = "identity_or_payload_conflict" }, statusCode: 409); }
        if (accepted != null) { SaveTruth(); return Results.Ok(new { duplicate = true, notification_id = n.NotificationId }); }
        first = attempts == 1;
        inFlight++;
        // In the second scenario, the first attempt is explicitly abandoned BEFORE applying the effect.
        if (!(first && mode == "not_completed")) { accepted = n; effects++; }
        SaveTruth();
    }
    if (first) await Task.Delay(650); // caller timeout is 120ms in all three cases
    lock (sync) { inFlight--; SaveTruth(); }
    if (first) { context.Abort(); return Results.Empty; } // identical caller symptom
    return Results.Ok(new { accepted = true, notification_id = n.NotificationId });
});
app.Run($"http://127.0.0.1:{port}");
record Notification(string NotificationId, string OrderId, string RequestId, string Kind, bool RefundRequested);
