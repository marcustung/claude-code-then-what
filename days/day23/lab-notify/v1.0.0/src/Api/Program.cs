// 訂單取消＋通知的薄 HTTP API。程序內記憶體儲存（不保證重啟持久性）；每 request 一行 logs.jsonl；/metrics 文字格式。
// 通知走 Channel → NotificationWorker → POST 到 fake sink（OC_SINK_URL）。故障注入由 OC_FAULTS 指定的 JSON 檔提供，只供演練。
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Channels;
using OrderCancel.Domain;

var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
var runDir = Environment.GetEnvironmentVariable("OC_RUN_DIR") ?? "runs/default";
Directory.CreateDirectory(runDir);
var versionFile = Path.Combine(AppContext.BaseDirectory, "VERSION");
var version = File.Exists(versionFile) ? File.ReadAllText(versionFile).Trim() : (Environment.GetEnvironmentVariable("OC_VERSION") ?? "unknown");
var faults = Faults.Load(Environment.GetEnvironmentVariable("OC_FAULTS"));
var store = new OrderStore();
var metrics = new Metrics();
var log = new JsonlLog(Path.Combine(runDir, "logs.jsonl"), version);
var channel = Channel.CreateUnbounded<Notification>();
builder.Services.AddSingleton(store); builder.Services.AddSingleton(metrics); builder.Services.AddSingleton(log); builder.Services.AddSingleton(faults);
builder.Services.AddSingleton(channel);
builder.Services.AddHostedService<NotificationWorker>();
var app = builder.Build();
log.Write(new { level = "INFO", @event = "startup", faults_loaded = faults.Any, sink = Environment.GetEnvironmentVariable("OC_SINK_URL") });

app.MapGet("/health", () => Results.Ok(new { ok = true, version }));
app.MapGet("/ready", () => Results.Ok(new { ready = true, version }));   // 記憶體儲存無外部依賴；readiness＝程序起來
app.MapPost("/orders", async (HttpRequest req) =>
{   // 建單（測試用）：body {id, shipped, paid}
    using var doc = await JsonDocument.ParseAsync(req.Body); var r = doc.RootElement;
    var id = r.GetProperty("id").GetString()!;
    var order = new Order(r.TryGetProperty("shipped", out var s) && s.GetBoolean(), r.TryGetProperty("paid", out var p) && p.GetBoolean(), false);
    store.Put(id, order);
    return Results.Ok(new { id, order });
});
app.MapGet("/orders/{id}", (string id) => store.TryGet(id, out var o) ? Results.Ok(new { id, order = o }) : Results.NotFound());
app.MapPost("/orders/{id}/cancel", async (string id, HttpRequest req) =>
{
    var t0 = DateTime.UtcNow;
    var rid = req.Headers["X-Request-Id"].FirstOrDefault() ?? Guid.NewGuid().ToString("N")[..12];
    var runId = req.Headers["X-Run-Id"].FirstOrDefault();
    var actor = req.Headers["X-Actor"].FirstOrDefault();
    if (string.IsNullOrEmpty(actor))
    {
        metrics.Inc("cancel_requests_total", "unauthorized");
        log.Write(new { level = "WARN", @event = "cancel", request_id = rid, run_id = runId, order_id = id, result = "unauthorized" });
        return Results.Json(new { ok = false, reason = "unauthorized", request_id = rid }, statusCode: 401);
    }
    if (!store.TryGet(id, out var before))
    {
        metrics.Inc("cancel_requests_total", "not_found");
        log.Write(new { level = "WARN", @event = "cancel", request_id = rid, run_id = runId, order_id = id, result = "not_found" });
        return Results.Json(new { ok = false, reason = "not_found", request_id = rid }, statusCode: 404);
    }
    var result = Cancellation.Cancel(before);
    bool transitioned = Cancellation.Transitioned(before, result);
    string outcome; int status;
    if (before.Shipped) { outcome = "rejected_shipped"; status = 409; }          // BR-02，不通知（NC-03）
    else if (transitioned) { outcome = "ok"; status = 200; store.Put(id, result.Order); }
    else { outcome = "idempotent"; status = 200; }                               // BR-04／NC-02，不通知
    metrics.Inc("cancel_requests_total", outcome);
    if (transitioned)
    {
        metrics.Inc("transitions_total");
        var n = new Notification(Guid.NewGuid().ToString("N"), id, rid, runId, "order_cancelled", result.RefundRequested);
        await channel.Writer.WriteAsync(n);
        metrics.Inc("notify_enqueued_total");
    }
    var lat = (DateTime.UtcNow - t0).TotalMilliseconds;
    log.Write(new { level = status == 200 ? "INFO" : "WARN", @event = "cancel", request_id = rid, run_id = runId, order_id = id, actor, result = outcome, transitioned, refund_requested = result.RefundRequested, latency_ms = Math.Round(lat, 1), queue_depth = channel.Reader.Count });
    return Results.Json(new { ok = status == 200, transitioned, refund_requested = result.RefundRequested, reason = status == 200 ? null : outcome, request_id = rid, order = status == 200 ? result.Order : before }, statusCode: status);
});
app.MapGet("/metrics", () => Results.Text(metrics.Render(channel.Reader.Count, version), "text/plain"));
app.Run();

record Notification(string NotificationId, string OrderId, string RequestId, string? RunId, string Kind, bool RefundRequested);

sealed class OrderStore
{
    readonly Dictionary<string, Order> _d = new(); readonly object _g = new();
    public void Put(string id, Order o) { lock (_g) _d[id] = o; }
    public bool TryGet(string id, out Order o) { lock (_g) return _d.TryGetValue(id, out o!); }
}

sealed class Metrics
{
    readonly Dictionary<string, long> _c = new(); readonly object _g = new();
    public void Inc(string name, string? label = null)
    {
        var k = label is null ? name : name + "{result=\"" + label + "\"}";
        lock (_g) _c[k] = _c.GetValueOrDefault(k) + 1;
    }
    public string Render(int depth, string version)
    {
        lock (_g)
        {
            var sb = new System.Text.StringBuilder();
            foreach (var kv in _c.OrderBy(k => k.Key)) sb.Append("oc_").Append(kv.Key).Append(' ').Append(kv.Value).Append('\n');
            sb.Append("oc_notify_queue_depth ").Append(depth).Append('\n');
            sb.Append("oc_info{version=\"").Append(version).Append("\"} 1\n");
            return sb.ToString();
        }
    }
}

sealed class JsonlLog
{
    readonly string _p; readonly string _v; readonly object _g = new();
    public JsonlLog(string p, string v) { _p = p; _v = v; }
    public void Write(object o)
    {
        var d = JsonSerializer.SerializeToNode(o)!.AsObject();
        d["ts"] = DateTimeOffset.Now.ToString("o"); d["version"] = _v;
        lock (_g) File.AppendAllText(_p, d.ToJsonString() + "\n");
    }
}

sealed class Faults
{
    public int? DropOverQueue; public int DelayMs;
    public bool Any => DropOverQueue is not null || DelayMs > 0;
    public static Faults Load(string? path)
    {
        var f = new Faults();
        if (string.IsNullOrEmpty(path) || !File.Exists(path)) return f;
        using var doc = JsonDocument.Parse(File.ReadAllText(path)); var r = doc.RootElement;
        if (r.TryGetProperty("notify_drop_over_queue", out var q)) f.DropOverQueue = q.GetInt32();
        if (r.TryGetProperty("notify_delay_ms", out var d)) f.DelayMs = d.GetInt32();
        return f;
    }
}

// 通知 worker：從 channel 取出 → POST sink → 失敗重試 3 次（200／400／800 ms）→ 超過進 dead_letter（NC-05）。
// 故障 notify_drop_over_queue（演練用）：佇列深度超過 N 時，記一行 notify_deferred 後**不再重送**，但 sent 計數照加——
// 服務自己的計數器說送了，接收端沒有收據。這是把 O 服務 fault-A 的設計移植過來，不是自然事故。
sealed class NotificationWorker : BackgroundService
{
    readonly Channel<Notification> _ch; readonly Metrics _m; readonly JsonlLog _log; readonly Faults _f; readonly HttpClient _http = new();
    readonly string _sink = Environment.GetEnvironmentVariable("OC_SINK_URL") ?? "http://127.0.0.1:5081/notify";
    static readonly int[] Backoff = { 200, 400, 800 };
    public NotificationWorker(Channel<Notification> ch, Metrics m, JsonlLog log, Faults f) { _ch = ch; _m = m; _log = log; _f = f; }
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        await foreach (var n in _ch.Reader.ReadAllAsync(ct))
        {
            if (_f.DelayMs > 0) await Task.Delay(_f.DelayMs, ct);
            if (_f.DropOverQueue is int q && _ch.Reader.Count > q)
            {   // 故障：假裝送了
                _m.Inc("notify_sent_total");
                _log.Write(new { level = "INFO", @event = "notify_deferred", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, queue_depth = _ch.Reader.Count });
                continue;
            }
            bool sent = false;
            for (int attempt = 0; attempt <= Backoff.Length && !sent; attempt++)
            {
                try
                {
                    var body = JsonSerializer.Serialize(new { notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, kind = n.Kind, refund_requested = n.RefundRequested, attempt });
                    var resp = await _http.PostAsync(_sink, new StringContent(body, System.Text.Encoding.UTF8, "application/json"), ct);
                    sent = resp.IsSuccessStatusCode;
                    if (!sent) _log.Write(new { level = "WARN", @event = "notify_attempt_failed", notification_id = n.NotificationId, attempt, status = (int)resp.StatusCode });
                }
                catch (Exception e) when (!ct.IsCancellationRequested)
                {
                    _log.Write(new { level = "WARN", @event = "notify_attempt_failed", notification_id = n.NotificationId, attempt, error = e.GetType().Name });
                }
                if (!sent && attempt < Backoff.Length) await Task.Delay(Backoff[attempt], ct);
            }
            if (sent)
            {
                _m.Inc("notify_sent_total");
                _log.Write(new { level = "INFO", @event = "notify_sent", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId });
            }
            else
            {
                _m.Inc("notify_failed_total"); _m.Inc("notify_dead_letter_total");
                _log.Write(new { level = "ERROR", @event = "notify_dead_letter", notification_id = n.NotificationId, order_id = n.OrderId, request_id = n.RequestId, run_id = n.RunId, attempts = Backoff.Length + 1 });
            }
        }
    }
}
