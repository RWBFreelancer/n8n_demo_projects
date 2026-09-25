"""Add canvas notes (sticky notes) and node notes to the Weekly Sales
Performance Report workflow, lay the nodes out on an even grid, and push it
back to n8n. Also saves a copy to workflows/weekly-sales-report.json.

Run: python projects/weekly-sales-report/add_notes.py
Needs N8N_BASE_URL and N8N_API_KEY in .env.
"""
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
WORKFLOW_ID = "bUVByfzcHXW66122"


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
BASE = ENV["N8N_BASE_URL"].rstrip("/") + "/api/v1"


def api(method, path, body=None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-N8N-API-KEY": ENV["N8N_API_KEY"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# ---------- Text ----------

OVERVIEW = """## Weekly Sales Performance Report

### What it does
Every Monday at 8 AM, this workflow reads your sales sheet. It checks how each salesperson and each product did this week. It compares that to last week. Then it emails a clean report and saves a copy in Google Docs.

### How it works
1. Get all rows from the `Sales` tab in Google Sheets.
2. No rows? Send a Slack alert and stop.
3. Do the math in code. The AI never makes up the numbers.
4. Find problems, such as a big drop in sales.
5. The AI writes short notes about the numbers.
6. Build the email and the doc text.
7. Make the Google Doc, send the email, and log the run.

### Setup
- The `Sales` tab needs these columns: `date`, `salesperson`, `product`, `units`, `revenue`, `deal_status` (use `won` for a won deal).
- The `Report Log` tab needs these columns: `run_date`, `rows_processed`, `flag_count`.
- Connect your credentials for Google Sheets, Google Docs, Gmail, Slack, and OpenRouter.
- Set who gets the email in **Email Report**.
- Set the Google Drive folder in **Create Doc**.
- Set the Slack channel in **Slack Zero Rows Alert**.
- Test it with the **Execute workflow** button. Then turn the workflow on.

### Words to know
- **Credential**: a saved login. It lets n8n use an app for you.
- **Close rate**: won deals divided by all deals. 3 won out of 10 is 30%.
- **Percent change**: how much a number went up or down since last week. $800 to $1,000 is +25%.
- **Flag**: a warning that something needs a look.
- **JSON**: a simple text format for data, made of names and values. Computers read it easily."""

SECTIONS = [
    # (title, text, node names on the main row, extra nodes one row down, width)
    ("Step 1", """## 1. Start and get data
Runs every Monday at 8 AM.

Reads every row from the `Sales` tab.

If the tab is empty, it still passes on one empty item. That lets the next step send the alert.""",
     ["Monday 8AM", "Get Sales"], [], 480),

    ("Step 2", """## 2. Is there data?
Checks that each row has a `date`.

**Yes:** go on to the math.
**No:** send a Slack alert (see below).""",
     ["Has Sales Rows"], [], 400),

    ("Step 3", """## 3. Do the math
**Crunch Numbers** adds up revenue, units, and deals. "This week" is the last 7 days. "Last week" is the 7 days before that.

**Flag Problems** checks simple rules:
- revenue down more than 20%
- close rate under 15%
- product units down more than 30%
- product sold 0 this week, but sold last week

Change these numbers in the **Flag Problems** code.""",
     ["Crunch Numbers", "Flag Problems"], [], 560),

    ("Step 4", """## 4. The AI writes the words
The AI gets the numbers and the flags. It writes a summary, who did well, who fell behind, and 3 actions.

It must use only the numbers it gets.

**OpenRouter** is the service that runs the AI model.""",
     ["Write Report"], ["OpenRouter Chat Model"], 440),

    ("Step 5", """## 5. Build the report
Makes two versions:
- a styled email in HTML (the code that makes an email look nice)
- plain text for the Google Doc

If the AI reply is broken, the report still goes out with the correct numbers.""",
     ["Build Report"], [], 420),

    ("Step 6", """## 6. Save and send
Makes a new Google Doc in your Drive folder. Then it fills the doc with the report.

Emails the report with a button that opens the doc.""",
     ["Create Doc", "Insert Doc Body", "Email Report"], [], 700),

    ("Step 7", """## 7. Keep a record
Adds one row to the `Report Log` tab.

The row has the date, the number of rows read, and the number of flags.""",
     ["Log Run"], [], 400),
]

ALERT = ("No data alert", """## No data alert
If the `Sales` tab has no rows, this sends a message to the Slack channel `#acctg_report`.

No report is made that week.""", "Slack Zero Rows Alert")

NODE_NOTES = {
    "Monday 8AM": "Starts the workflow every Monday at 8 AM (n8n instance time zone).",
    "Get Sales": "Reads all rows from the Sales tab. Tries again if Google fails. Always passes on at least one item.",
    "Has Sales Rows": "True: the row has a date. False: no data, so send the Slack alert.",
    "Crunch Numbers": "Adds up this week (last 7 days) and last week (the 7 days before) per salesperson and per product.",
    "Flag Problems": "Makes a list of problems. Limits: revenue -20%, close rate 15%, units -30%, 0 units sold.",
    "Write Report": "The AI writes the report text as JSON. It uses only the numbers it gets.",
    "OpenRouter Chat Model": "The AI model used by Write Report. Change the model here.",
    "Build Report": "Builds the HTML email, the plain text for the doc, and the email subject.",
    "Create Doc": "Makes an empty Google Doc named 'Weekly Sales Report - <date>' in the Drive folder.",
    "Insert Doc Body": "Puts the plain text report into the new doc.",
    "Email Report": "Sends the HTML report. Swaps __DOC_LINK__ for the real doc link.",
    "Log Run": "Adds one row to the Report Log tab: date, rows read, flag count.",
    "Slack Zero Rows Alert": "Tells the team in Slack that no report was made, because the sheet had no rows.",
}

# ---------- Layout ----------

GRID = 20
TOP = 0            # top edge of the step notes
SECTION_H = 780    # step note height
NODE_Y = 400       # main row of nodes
LOWER_Y = 620      # second row (AI model)
GAP = 40           # space between notes
NODE_STEP = 220    # space between nodes in one note
NODE_W = 100


def snap(v):
    return int(round(v / GRID) * GRID)


def sticky(name, x, y, w, h, text, color=7):
    return {
        "parameters": {"content": text, "height": h, "width": w, "color": color},
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
    }


def main():
    wf = api("GET", f"/workflows/{WORKFLOW_ID}")
    nodes = [n for n in wf["nodes"] if n["type"] != "n8n-nodes-base.stickyNote"]
    by_name = {n["name"]: n for n in nodes}

    stickies = [sticky("Overview", -700, TOP, 660, 1300, OVERVIEW, 4)]

    x = 0
    step2_left = None
    for title, text, main_nodes, lower_nodes, width in SECTIONS:
        stickies.append(sticky(title, x, TOP, width, SECTION_H, text))
        span = (len(main_nodes) - 1) * NODE_STEP + NODE_W
        start = x + (width - span) / 2
        for i, name in enumerate(main_nodes):
            by_name[name]["position"] = [snap(start + i * NODE_STEP), NODE_Y]
        for i, name in enumerate(lower_nodes):
            by_name[name]["position"] = [snap(start + i * NODE_STEP), LOWER_Y]
        if title == "Step 2":
            step2_left = x
        x += width + GAP

    # Alert lane under steps 2 and 3
    a_title, a_text, a_node = ALERT
    a_y = TOP + SECTION_H + GAP
    stickies.append(sticky(a_title, step2_left, a_y, 520, 480, a_text, 3))
    by_name[a_node]["position"] = [snap(step2_left + 60), a_y + 280]

    for name, note in NODE_NOTES.items():
        by_name[name]["notes"] = note

    body = {
        "name": wf["name"],
        "nodes": stickies + nodes,
        "connections": wf["connections"],
        "settings": wf["settings"],
    }
    saved = api("PUT", f"/workflows/{WORKFLOW_ID}", body)

    out = HERE / "workflows" / "weekly-sales-report.json"
    out.parent.mkdir(exist_ok=True)
    keep = {k: saved[k] for k in ("name", "nodes", "connections", "settings")}
    out.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved", len(saved["nodes"]), "nodes to n8n and", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
