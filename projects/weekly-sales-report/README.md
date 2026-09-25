# Weekly Sales Performance Report

Every Monday at 8 AM, this workflow reads a sales sheet. It checks how each salesperson and each product did this week. It compares that to last week. Then it emails a clean report and saves a copy in Google Docs.

- n8n workflow: `bUVByfzcHXW66122` (on `robertgrove.app.n8n.cloud`)
- Export: `workflows/weekly-sales-report.json`
- Notes script: `add_notes.py` (adds the canvas notes and the grid layout, then pushes to n8n)

## How it works

| # | Node | What it does |
|---|---|---|
| 1 | **Monday 8AM** | Starts the workflow every Monday at 8 AM. It uses the time zone of the n8n instance. |
| 1 | **Get Sales** | Reads all rows from the `Sales` tab. It tries again if Google fails. It always passes on at least one item. |
| 2 | **Has Sales Rows** | Checks that a row has a `date`. Yes: go to step 3. No: send the Slack alert. |
| 3 | **Crunch Numbers** | Adds up revenue, units, and deals per salesperson and per product. "This week" is the last 7 days. "Last week" is the 7 days before that. |
| 3 | **Flag Problems** | Checks the numbers against rules and makes a list of problems (flags). |
| 4 | **Write Report** + **OpenRouter Chat Model** | The AI writes the report text as JSON. It uses only the numbers it gets. |
| 5 | **Build Report** | Builds the HTML email, the plain text for the doc, and the email subject. |
| 6 | **Create Doc** | Makes an empty Google Doc named `Weekly Sales Report - <date>` in the Drive folder. |
| 6 | **Insert Doc Body** | Puts the plain text report into the doc. |
| 6 | **Email Report** | Sends the HTML report. It swaps `__DOC_LINK__` for the real doc link. |
| 7 | **Log Run** | Adds one row to the `Report Log` tab: date, rows read, flag count. |
| – | **Slack Zero Rows Alert** | Tells the team in Slack that no report was made, because the sheet had no rows. |

## Flag rules

These rules live in the **Flag Problems** code. You can change the numbers there.

| Flag | Rule |
|---|---|
| `revenue_drop` | A salesperson's revenue fell more than 20% since last week. |
| `low_close_rate` | A salesperson's close rate is under 15%. |
| `product_units_drop` | A product's units fell more than 30% since last week. |
| `product_zero_sales` | A product sold 0 units this week, but sold some last week. |

## Setup

1. The `Sales` tab needs these columns: `date`, `salesperson`, `product`, `units`, `revenue`, `deal_status`. Use `won` for a won deal.
2. The `Report Log` tab needs these columns: `run_date`, `rows_processed`, `flag_count`.
3. Connect credentials for Google Sheets, Google Docs, Gmail, Slack, and OpenRouter.
4. Set who gets the email in **Email Report** (`sendTo`).
5. Set the Google Drive folder in **Create Doc** (`folderId`).
6. Set the Slack channel in **Slack Zero Rows Alert**. Now it is `#acctg_report`.
7. Click **Execute workflow** to test. Then turn the workflow on.

## Words to know

- **Credential**: a saved login. It lets n8n use an app for you.
- **Close rate**: won deals divided by all deals. 3 won out of 10 is 30%.
- **Percent change**: how much a number went up or down since last week. $800 to $1,000 is +25%. If last week was 0, the report shows `n/a`, because you cannot divide by 0.
- **Flag**: a warning that something needs a look.
- **JSON**: a simple text format for data, made of names and values. Computers read it easily.
- **HTML**: the code that makes an email look nice, with colors and tables.
- **OpenRouter**: a service that runs many AI models through one account.

## Known limits

- **Has Sales Rows** checks each row on its own. A row with no `date` goes to the Slack alert, even when other rows are fine. So one blank row can send a false "no data" alert.
- **Flag Problems** does not check how many deals a person had. A person with 0 deals this week gets a `low_close_rate` flag. The email table only marks low close rates at 3 or more deals.
- `rowsProcessed` counts all rows in the sheet, not only the last 2 weeks. The email says "N deals reviewed" with this number.
