using ReviewPoc;
var suite = args.ElementAtOrDefault(0) ?? "author-v1";
var implementation = args.ElementAtOrDefault(1) ?? "v1";
Func<Application, bool> canTransition = implementation == "v2" ? Transition.V2 : Transition.V1;
var cases = new List<(string Id, Application Input, bool Expected)> {
    ("R01-pending", new(Status.Pending), true),
    ("R02-rejected", new(Status.Rejected), false),
    ("already-interviewing", new(Status.Interviewing), false),
    ("not-reopened", new(Status.Rejected, false, true), false),
    ("not-authorized", new(Status.Rejected, true, false), false)
};
if (suite == "author-v1") cases.Add(("assumed-exception", new(Status.Rejected, true, true), true));
else if (suite == "acceptance-v2") cases.AddRange(new (string, Application, bool)[] {
    ("R03-valid", new(Status.Rejected, true, true, Role.HiringLead, "new evidence"), true),
    ("R03-no-role", new(Status.Rejected, true, true, Role.None, "new evidence"), false),
    ("R03-wrong-role", new(Status.Rejected, true, true, Role.Recruiter, "new evidence"), false),
    ("R03-no-reason", new(Status.Rejected, true, true, Role.HiringLead), false),
    ("R03-whitespace", new(Status.Rejected, true, true, Role.HiringLead, "  "), false)
});
else throw new ArgumentException("Unknown suite");
var results = cases.Select(c => new { c.Id, c.Expected, Actual = canTransition(c.Input) }).ToArray();
var failed = results.Count(r => r.Actual != r.Expected);
Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new {suite,implementation,total=results.Length,passed=results.Length-failed,failed,results},new System.Text.Json.JsonSerializerOptions {WriteIndented=true}));
return failed == 0 ? 0 : 1;
