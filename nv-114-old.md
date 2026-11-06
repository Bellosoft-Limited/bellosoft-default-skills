# Implementation Plan — NV-114 (UNPL-2-T5): Show the saved VAT on the Morans VAT breakdown

**Status:** ✅ Approved 2026-11-04 (Fernando Wolff). Ready for `/bellosoft-dev-execute`.
**Spec:** `docs/planning-artifacts/epic-plans/NV-75-UNPL-2-freeze-invoice-figures.md` → UNPL-2-T5
**Jira:** NV-114 (sub-task of NV-109, story under NV-75); QA follow-up in NV-115
**Branch:** to be created off `develop` (has T1–T4)

## Context

Epic: NV-75 Novo — General Fixes and Improvements
Story: NV-109 UNPL-2 — Freeze invoice figures when the invoice is issued. Each invoice saves its inputs and figures once at issue (`SalesInvoices` / `SalesInvoiceLines`), and every reader shows the saved figures instead of recalculating.
This task: the last reader still recalculating. `ExtraSalesOrderImplementation.GetInvoiceVatBreakdownViewComponentInfo` (Morans) calls `VatCalculationHelper.GetOrderLineVatValues` (`ExtraSalesOrderImplementation.cs:154`). A Morans invoice can therefore show saved line figures above a recalculated VAT breakdown. T1–T4 are done and merged on `develop`. T6 (NV-115, QA) waits for this task.

Task AC: for an issued invoice, each rate's net and VAT on the breakdown are the sums of the saved lines at that rate, and they add up to the invoice's VAT.

**Decision (Fernando, 2026-11-04):** group the saved lines **by the order line's `TaxId`, as today**, not by saved `TaxRate` as the ticket text says. Grouping by rate would merge "No VAT" (TaxId 0) with a 0% tax, which are different (see the No VAT rule).

## Summary

For an `Invoice`-status order that has a saved invoice, build the breakdown rows from `SalesInvoiceService.GetFrozenFigures`. Each saved line gets its `TaxId` from its order line, matched by `SalesOrderProductId` / `SalesOrderServiceId`. Lines are grouped by `TaxId`. Each row sums the saved `LineNet` and `LineVat` and shows the saved `TaxRate`. The `TaxId` also supplies the code name (`Tax.Name`, or "No VAT" for 0). In every other case, the breakdown is built as today: for orders not yet invoiced (no warning), for invoices with no saved figures (warning, decision 8), and for saved lines that don't match the order lines (error, the same rule as NV-113).

## Files to Modify

- `Plugins/LogicCloud.Module.Morans/Business/PluginImplementations/ExtraSalesOrderImplementation.cs`
  - Inject `ISalesInvoiceService` (`LogicCloud.DAL.Business.Interfaces`; already registered at `LogicCloud/Startup.cs:435`).
  - In `GetInvoiceVatBreakdownViewComponentInfo`, keep the load, the NoVAT/empty-line early returns, `rateUsed` and the currency symbol unchanged. Then:
    - Call a new private `GetSavedLineTaxes(salesOrder)`. It returns `List<(int TaxId, SalesInvoiceLine Line)>`, or null so the caller recalculates. Its rules follow NV-113's `InvoiceService.GetSavedInvoice` (`InvoiceService.cs:572-601`):
      - Status is not `Invoice` → null, no log.
      - `GetFrozenFigures` returns null → `LogWarning` with the DocNumber ("has no saved figures, so they are recalculated from the sales order").
      - A saved line has no matching order line, or the counts differ → `LogError` with the DocNumber, then null. Saved and recalculated figures are never mixed.
      - It builds `Id → TaxId` dictionaries from `SalesOrderProducts` / `SalesOrderServices` and **does not modify** the returned invoice or its `Lines`. This is audit finding F7: copy the figures, don't reorder them.
    - **Saved path:** group by `TaxId`. `NetGoodsValue = Σ LineNet × rateUsed`, `VatAmount = Σ LineVat × rateUsed`, `VatRate = first saved line's TaxRate` (first in SortOrder). `VatCode` follows today's rule.
    - **Recalculated path:** today's code, unchanged. Move it into a private `RecalculateRows(...)` so the method body stays readable.
    - Shared row building: a small private helper that takes `(taxId, net, vat, rate)` and the tax dictionary, and returns `VatBreakdownRowViewModel`. Both paths use it, so the label rule exists only once.
  - Put the new helpers in a `#region Private Methods` at the bottom, following the convention in `InvoiceService`.
- `Tests/LogicCloud.Module.Morans.Tests/Business/Services/ExtraSalesOrderImplementationTests.cs`
  - Add `Mock<ISalesInvoiceService>` and `Mock<ILogger<ExtraSalesOrderImplementation>>` fields, and pass them to the constructor. The existing 5 tests stay unchanged. Their orders are `Open` (the default), so they keep testing the recalculated path.
  - Add a helper `SetupInvoicedOrder(...)` that builds an `Invoice` order with line Ids, plus a `SalesInvoice` whose saved figures are deliberately **different** from what a recalculation would give. A test then fails if the code recalculates.
  - Update the fixture `<summary>` to mention NV-114.

No new files.

## Test Cases (write these FIRST)

NUnit + Moq, in `ExtraSalesOrderImplementationTests`.

| # | Test Name | Covers | Expected Behaviour |
|---|-----------|--------|--------------------|
| 1 | `GetInvoiceVatBreakdown_IssuedInvoiceWithMixedRates_RowsAreSumsOfSavedLines` | AC, scenario "Mixed rates" | Invoice with two Standard (20%) lines and one Zero (0%) service line, all saved. There is one row per TaxId. Each row's Net and VAT are the sums of its saved `LineNet` and `LineVat`, and the row VATs add up to `SalesInvoice.Vat` |
| 2 | `GetInvoiceVatBreakdown_IssuedInvoice_OrderLineChangedAfterIssue_ShowsSavedFigures` | Scenario "Issued invoice does not change" | The order line's `TaxRate` and `UnitPrice` are changed after issue. The rows still show the saved figures, and the saved rate (`20.00%`) as `VatRate` |
| 3 | `GetInvoiceVatBreakdown_IssuedInvoice_ShowsSavedRateNotCurrentTaxPercentage` | Frozen rate | `Tax.Percentage` is now 22, but the saved line `TaxRate` is 20. The row shows 20% |
| 4 | `GetInvoiceVatBreakdown_IssuedInvoice_NoVatLineKeptApartFromZeroRate` | No VAT rule | A TaxId 0 line and a 0% TaxId line give two rows, "No VAT" and "Zero" |
| 5 | `GetInvoiceVatBreakdown_IssuedInvoice_ForeignCurrency_MultipliesSavedFiguresByRate` | Currency | With `CurrencyRateUsed = 1.5`, the rows are the saved sums × 1.5 |
| 6 | `GetInvoiceVatBreakdown_InvoiceWithNoSavedFigures_RecalculatesAndLogsWarning` | Decision 8 | `GetFrozenFigures` returns null. The rows equal today's recalculation, and a warning is logged once |
| 7 | `GetInvoiceVatBreakdown_SavedLinesDoNotMatchOrderLines_RecalculatesAndLogsError` | Mismatch rule (NV-113) | A saved line points to an unknown order line Id. The breakdown is recalculated, and an error is logged |
| 8 | `GetInvoiceVatBreakdown_OpenOrder_DoesNotReadSavedFigures` | Open orders recalculate | For an `Open` order, `GetFrozenFigures` is never called |

The existing 5 tests stay green, so the recalculated path does not regress.

## Implementation Steps

Start only after tests 1–8 are written and confirmed failing (red):

1. `ExtraSalesOrderImplementationTests.cs`: add the mocks and constructor argument, the `SetupInvoicedOrder` helper and tests 1–8. Build, then confirm that tests 1–5, 7 and 8 fail and the existing 5 pass. Test 6 can already pass, since today's code recalculates. Its warning assertion is what fails.
2. `ExtraSalesOrderImplementation.cs`: inject `ISalesInvoiceService`.
3. `ExtraSalesOrderImplementation.cs`: extract today's row building into `RecalculateRows` and the shared row helper. Re-run the tests: the existing 5 still pass.
4. `ExtraSalesOrderImplementation.cs`: add `GetSavedLineTaxes` and the saved-figures path. Re-run the tests: all green.
5. Run the whole `LogicCloud.Module.Morans.Tests` (99 → 107) and `LogicCloud.Tests`. Also run a build of the solution, to catch any other place that constructs `ExtraSalesOrderImplementation`.
6. Manual check on local Postgres: issue a Morans invoice with mixed rates. In the DB, change one order line's `TaxRate`/`UnitPrice`. Open the invoice details/print: the breakdown is unchanged and its VAT rows add up to the invoice VAT shown above.

## Out of Scope (not touching)

- `TaxType == NoVAT` early return (kept as is; orders are never NoVAT in practice).
- Snapshotting `TaxId`/tax name onto `SalesInvoiceLine` (E8).
- Xero/QuickBooks, payments, the reports' VAT control (E13).
- `InvoiceService` / NV-113 code.
- Fixing the `GetFrozenFigures` mutation itself (F7). This task only avoids adding to it.

## Risks / Questions

- **Two saved rates under one TaxId** (a tax percentage changed between lines being added before issue). The lines are grouped by TaxId as decided, and the row shows the first line's saved rate. The row's figures are still the correct sums. This is rare, and it is accepted.
- **The label still comes from live data**: `Tax.Name` (via TaxId) is read at display time, as NV-97/T4 do. Renaming a tax code changes the label on old invoices. This is accepted until E8.
- **Row rounding**: rows are rounded with `ToPrice()` after the multiplication by `rateUsed`. On a foreign-currency invoice, the rounded rows can differ from the rounded invoice VAT by a penny. This is unchanged from today, and in base currency the sums match exactly.
