
using System.Diagnostics;
using System.Diagnostics.Metrics;
using OpenTelemetry;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Metrics;
using OpenTelemetry.Logs;
public static class Obs {
 public static readonly ActivitySource Source=new("Day24.Notifications");
 public static readonly Meter Meter=new("Day24.Notifications");
 public static readonly Histogram<double> QueueWait=Meter.CreateHistogram<double>("notification.queue.wait","ms");
 static ILogger? logger;
 public static void Configure(WebApplicationBuilder b) {
  var name=Environment.GetEnvironmentVariable("OTEL_SERVICE_NAME") ?? "day24-api";
  b.Services.AddOpenTelemetry().ConfigureResource(r=>r.AddService(name).AddAttributes(new Dictionary<string,object>{{"lab.variant","after"}}))
    .WithTracing(t=>t.AddSource("Day24.Notifications").AddAspNetCoreInstrumentation().AddHttpClientInstrumentation().AddOtlpExporter())
    .WithMetrics(m=>m.AddMeter("Day24.Notifications").AddOtlpExporter());
  b.Logging.AddOpenTelemetry(o=> {o.IncludeFormattedMessage=true;o.IncludeScopes=true;o.SetResourceBuilder(ResourceBuilder.CreateDefault().AddService(name));o.AddOtlpExporter();});
 }
 public static void Init(WebApplication app) { logger=app.Services.GetRequiredService<ILoggerFactory>().CreateLogger("Day24.Evidence"); }
 public static void Log(string json) {logger?.LogInformation("{Evidence}",json);}
}
