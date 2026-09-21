using System;
using Demo.Data;

namespace Demo.Payroll
{
    public sealed class PayslipPrinter
    {
        private readonly DependentRepository _repo;
        public PayslipPrinter(DependentRepository repo) { _repo = repo; }

        public string DependentLine(int companyId, int employeeId, DateTime monthStart, DateTime monthEnd)
        {
            var rows = _repo.ListEffectiveInPeriod(companyId, employeeId, monthStart, monthEnd);
            return $"扶養親屬 {rows.Count} 人";
        }
    }
}
