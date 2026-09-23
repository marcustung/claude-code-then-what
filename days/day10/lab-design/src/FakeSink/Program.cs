// 本機假的通知接收端：只做一件事——把每則實際收到的通知寫成一行收據 receipts.jsonl。
// 這是「送達」的獨立來源（通知契約 NC-04）；服務自己的 sent counter 不算。
using System.Text.Json;
var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
var app = builder.Build();
var runDir = Environment.GetEnvironmentVariable("OC_RUN_DIR") ?? "runs/default";
Directory.CreateDirectory(runDir);
var receiptsPath = Path.Combine(runDir, "receipts.jsonl");
var seen = new HashSet<string>(); var gate = new object(); int received = 0, duplicates = 0;
var delayMs = int.TryParse(Environment.GetEnvironmentVariable("OC_SINK_DELAY_MS"), out var dm) ? dm : 0;   // 演練：接收端慢

app.MapGet("/health", () => Results.Ok(new { ok = true }));
app.MapPost("/notify", async (HttpRequest req) =>
{
    if (delayMs > 0) await Task.Delay(delayMs);
    using var doc = await JsonDocument.ParseAsync(req.Body);
    var root = doc.RootElement;
    string nid = root.TryGetProperty("notification_id", out var n) ? n.GetString() ?? "" : "";
    var receipt = new
    {
        notification_id = nid,
        order_id = root.TryGetProperty("order_id", out var o) ? o.GetString() : null,
        request_id = root.TryGetProperty("request_id", out var r) ? r.GetString() : null,
        run_id = root.TryGetProperty("run_id", out var ru) ? ru.GetString() : null,
        kind = root.TryGetProperty("kind", out var k) ? k.GetString() : null,
        received_at = DateTimeOffset.Now.ToString("o"),
    };
    lock (gate)
    {
        if (!seen.Add(nid)) duplicates++; else received++;
        File.AppendAllText(receiptsPath, JsonSerializer.Serialize(receipt) + Environment.NewLine);
    }
    return Results.Ok(new { ok = true, notification_id = nid });
});
app.MapGet("/receipts", () => { lock (gate) return Results.Ok(new { received, duplicates }); });
app.Run();
