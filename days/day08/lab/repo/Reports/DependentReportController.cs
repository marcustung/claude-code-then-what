using System;
using Demo.Data;

namespace Demo.Reports
{
    // 報表入口：下載某員工的扶養親屬報表（明細 + 人數）。
    public sealed class DependentReportController
    {
        private readonly DependentRepository _repo;
        private readonly DependentCountService _count;

        public DependentReportController(DependentRepository repo, DependentCountService count)
        {
            _repo = repo;
            _count = count;
        }

        public DependentReport Download(int companyId, int employeeId, int payrollGroupId, DateTime reportMonth)
        {
            var rows = _repo.ListForPayrollGroup(companyId, employeeId, payrollGroupId);
            var total = _count.Count(rows);
            return new DependentReport(reportMonth, rows, total);
        }
    }
}
