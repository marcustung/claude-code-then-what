using System;
using System.Linq;
using Demo.Data;

namespace Demo.Payroll
{
    // 計薪端：當月個人所得稅要納入的扶養人數。
    public sealed class MonthlyTaxCalculator
    {
        private readonly DependentRepository _repo;
        public MonthlyTaxCalculator(DependentRepository repo) { _repo = repo; }

        public int DependentsForMonth(int companyId, int employeeId, DateTime periodStart, int payrollDays)
        {
            var periodEnd = periodStart.AddDays(payrollDays);
            var rows = _repo.ListEffectiveInPeriod(companyId, employeeId, periodStart, periodEnd);
            return rows.Count(r => r.EffectiveFrom <= periodEnd);
        }
    }
}
