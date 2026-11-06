---
ticket: NV-114
status: approved
approved: 2026-11-05
---

## Plan — NV-114: UNPL-2-T5 [BE] Show the saved VAT on the Morans VAT breakdown
NV-75 › NV-109 (UNPL-2) › NV-114 (T5)
Labels: `S1`–`S4` = ticket scenarios. `B1`–`B8` = ticket description bullets, in order. `QA` = QA comment of 2026-11-04.

### Tests
| # | Covers | Test | Behaviour |
|---|--------|------|-----------|
| 1 | QA | `Freeze_ProductsAndServices_SavesEachOrderLinesTaxId` | Saved lines hold order line TaxIds 1 and 0 |
| 2 | QA | `GetPrintInvoiceInfo_OrderLineTaxIdChangedAfterIssue_PrintsSavedVatLabels` | 20%→No VAT prints "20.00%"; No VAT→tax 1 prints "No VAT" |
| 3 | QA, B3 | `GetPrintInvoiceInfo_SavedLineWithoutTaxId_PrintsOrderLineVatLabel` (guard) | Null saved TaxId labels from order line |
| 4 | AC, S1, B5 | `GetInvoiceVatBreakdown_IssuedInvoiceMixedRates_RowsSumSavedLineFigures` | One row per code, saved sums × rate, total = invoice VAT |
| 5 | S2, B6 | `GetInvoiceVatBreakdown_IssuedInvoiceRateChangedInDatabase_ShowsSavedRate` | Row rate is saved TaxRate, not tax's current percentage |
| 6 | S3, B2 | `GetInvoiceVatBreakdown_IssuedInvoiceNoVatAndZeroRate_ShowsTwoRows` | "No VAT" and "Zero" are separate rows |
| 7 | S4, B2 | `GetInvoiceVatBreakdown_OrderLineTaxChangedToNoVatAfterIssue_KeepsSavedRows` | Rows unchanged; "No VAT" row has zero VAT |
| 8 | B1 | `GetInvoiceVatBreakdown_SavedLinesInOtherOrder_MatchesByOrderLineId` | Reversed saved lines still read; no error logged |
| 9 | B3 | `GetInvoiceVatBreakdown_SavedLineWithoutTaxId_UsesOrderLineTaxIdAndLogsWarning` | Null TaxId grouped by order line TaxId, warning |
| 10 | B4 | `GetInvoiceVatBreakdown_SavedTaxNoLongerOnOrderLines_ReadsItsName` | Saved TaxId 1 still named "Standard" |
| 11 | B7 | `GetInvoiceVatBreakdown_IssuedInvoice_LeavesFrozenLinesUnchanged` (guard) | Same Lines list instance and order after call |
| 12 | B8 | `GetInvoiceVatBreakdown_InvoiceWithNoSavedFigures_RecalculatesAndLogsWarning` | Recalculated rows, one warning |
| 13 | B8 | `GetInvoiceVatBreakdown_SavedLinesDoNotMatchOrderLines_RecalculatesAndLogsError` | Missing or extra line recalculates, one error |
| 14 | B8 | `GetInvoiceVatBreakdown_OpenOrder_DoesNotReadSavedFigures` (guard) | `GetFrozenFigures` never called |

### Test setup
- Test 1: product TaxId 1, service TaxId 0. If the TaxId is null or not copied, the test fails.
- Tests 2–3: use the existing `IssueInvoice` (real `Freeze`), then change the order line TaxId. If `InCurrency` drops TaxId, test 2 fails.
- Test 3: set the saved line's TaxId to null after `IssueInvoice`.
- Tests 4–13: a hand-built `SalesInvoice` from a mocked `ISalesInvoiceService`, with `SalesStatus = Invoice`.
- The saved LineNet and LineVat differ from a recalculation, so the recalculating path fails tests 4–10.
- Test 4: `CurrencyRateUsed = 2`, so a missing conversion fails.
- Change the tax mock to return only the requested Ids. Set tax 1's `Percentage = 17.5`, saved TaxRate 20 (test 5).
- Replace `Mock.Of<ILogger<...>>` with a verifiable `Mock`. Check the log level and DocNumber.
- The existing breakdown tests keep `Open` status and stay green unchanged.

### Files
- edit `_source/LogicCloud.DAL/Data/Models/SalesInvoiceLine.cs` — add nullable `TaxId`
- new `_source/LogicCloud.DAL/Migrations/[ts]_AddTaxIdToSalesInvoiceLines.cs` — add column
- new `_source/LogicCloud.DAL/Migrations/[ts]_AddTaxIdToSalesInvoiceLines.Designer.cs` — EF generated
- edit `_source/LogicCloud.DAL/Migrations/ApplicationDbContextModelSnapshot.cs` — EF generated
- edit `_source/LogicCloud.DAL/Business/Services/SalesInvoiceService.cs` — copy order line TaxId
- edit `_source/LogicCloud/Business/Services/InvoiceService.cs` — label from saved TaxId
- edit `_source/Plugins/LogicCloud.Module.Morans/Business/PluginImplementations/ExtraSalesOrderImplementation.cs` — breakdown from saved lines
- edit `_source/Tests/LogicCloud.DAL.Tests/Business/Services/SalesInvoiceServiceTests.cs` — test 1
- edit `_source/Tests/LogicCloud.Tests/Business/Services/InvoiceServiceTests.cs` — tests 2–3
- edit `_source/Tests/LogicCloud.Module.Morans.Tests/Business/Services/ExtraSalesOrderImplementationTests.cs` — tests 4–14
- edit `docs/planning-artifacts/epic-plans/NV-75-UNPL-2-freeze-invoice-figures.md` — sync T5 with Jira

### Steps
0. Scaffold: `SalesInvoiceLine.TaxId` (`int?`), and an `ISalesInvoiceService` constructor parameter on `ExtraSalesOrderImplementation`. No behaviour.
1. Add migration `AddTaxIdToSalesInvoiceLines` (nullable int, no FK). Verify: `dotnet ef migrations has-pending-model-changes` reports none. Verify `Down` drops the column. No Jobs snapshot change.
2. Copy `TaxId` in `ProductLine` and `ServiceLine` → test 1
3. In `InvoiceService`, copy `TaxId` in `InCurrency`. Make the print label use `line.TaxId ?? x.TaxId` → test 2
4. Read saved lines in `GetInvoiceVatBreakdownViewComponentInfo` → tests 4–10, 12, 13
5. Replace the T5 block and table AC in the epic plan with the Jira text. Add the T4 label change. Verify: diff against the Jira description.

### Decisions
- D1: Print falls back to the order line TaxId without its own warning. The ticket asks for a warning only on the breakdown, and the Morans breakdown already logs on the same render.
- D2: Keep the print fallback inside `GetVatLabel`'s caller. Recalculated lines have null TaxId, so they use the order line, as today.

### Accepted risks
- One TaxId with mixed saved rates shows the first line's rate. This happens only if a tax's percentage changed while the order was open.
- Invoices issued before this release have no saved TaxId and keep the old grouping (QA comment). No backfill.

### Out of scope
- Email VAT display. It shows `TaxRate` only, with no VAT label.
- Xero/QuickBooks, reports and credit notes (E13, per NV-109).
- Backfilling `TaxId` on existing `SalesInvoiceLines`.
