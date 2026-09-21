using System;
using Demo.Data;

namespace Demo.Payroll
{
    public sealed class BonusCalculator
    {
        private readonly DependentRepository _repo;
        public BonusCalculator(DependentRepository repo) { _repo = repo; }

        public int DependentAllowanceUnits(int companyId, int employeeId, DateTime bonusPeriodStart, DateTime bonusPeriodEnd)
        {
            var rows = _repo.ListEffectiveInPeriod(companyId, employeeId, bonusPeriodStart, bonusPeriodEnd);
            return rows.Count;
        }
    }
}
