namespace ReviewPoc;
public enum Status { Pending, Rejected, Interviewing }
public enum Role { None, Recruiter, HiringLead }
public record Application(Status Status, bool Reopened = false, bool Authorized = false, Role Role = Role.None, string? Reason = null);
public static class Transition
{
    public static bool V1(Application a) => a.Status == Status.Pending
        || (a.Status == Status.Rejected && a.Reopened && a.Authorized);
    public static bool V2(Application a) => a.Status == Status.Pending
        || (a.Status == Status.Rejected && a.Reopened && a.Authorized
            && a.Role == Role.HiringLead && !string.IsNullOrWhiteSpace(a.Reason));
}
