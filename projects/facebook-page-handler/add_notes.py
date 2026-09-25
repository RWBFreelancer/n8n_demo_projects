"""Add canvas notes (sticky notes) and node notes to the Facebook Page
Message Handler (v7 - human handoff) workflow, lay the nodes out on an even
grid, and push it back to n8n. Also saves a copy to
workflows/facebook-page-handler.json.

The workflow is live. A PUT on a published workflow re-publishes it
(n8n 2.39+). This script changes only notes and positions.

Run: python projects/facebook-page-handler/add_notes.py
Test first (no change in n8n): add --dry-run
Needs N8N_BASE_URL and N8N_API_KEY in .env.
"""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
WORKFLOW_ID = "iK2hDxMAtEt7DTVW"


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

OVERVIEW = """## Facebook Page Message Handler

### What it does
When someone messages your Facebook Page, this workflow answers for you. An AI reads the message and writes a short reply. If the person needs a real human, the bot sends a "please wait" message and alerts the team in Slack. When a team member replies by hand, the bot stays quiet for 6 hours.

### How it works
1. Facebook sends each new message to this workflow.
2. A reply typed by a team member pauses the bot for that customer.
3. Customer messages are handled one at a time.
4. Messages already handled are skipped.
5. If a human is on the chat, the bot stays quiet.
6. The AI reads the message and the last 5 messages, then writes a reply.
7. Code checks the AI answer with safety rules.
8. Send the reply, or alert the team and send a "please wait" message.
9. Save the chat in Airtable.

### Setup
- In Airtable, make a `Conversations` table and a `Handoffs` table. The field names are in the README.
- Connect your credentials for Airtable, OpenRouter, Slack, and Facebook Graph API (use a Page access token).
- In your Meta app, set the webhook URL to the production URL of **FB Messages (POST)**. Subscribe to `messages` and `message_echoes`.
- Put your verify token in **Token OK?**. Use the same token in the Meta app.
- Put your Meta App ID in **Parse Message** (`APP_ID`).
- Set the Slack channel in **Alert Team**.

### Words to know
- **Webhook**: a web address. Facebook sends new messages to it.
- **Credential**: a saved login. It lets n8n use an app for you.
- **Echo**: a copy of a message your Page sent out. Facebook sends it back, so we can see who sent it.
- **Handoff**: when a real person takes over the chat from the bot.
- **Intent**: what the person wants, such as `pricing` or `greeting`.
- **Confidence**: how sure the AI is, from 0 (not sure) to 1 (very sure).
- **JSON**: a simple text format for data, made of names and values. Computers read it easily."""

# Each column is (top node, bottom node or None).
SECTIONS = [
    ("Step 1", """## 1. Messages come in
Facebook sends new messages to this webhook (a web address).

**Parse Message** pulls out who sent it and what it says. It skips empty messages and the bot's own replies.""",
     [("FB Messages (POST)", None), ("Parse Message", None)], 480),

    ("Step 2", """## 2. Did a team member reply?
**Yes:** save a 6 hour pause in the `Handoffs` table. The bot stays quiet for this customer.

**No:** it is a customer message. Go on.""",
     [("Human Reply?", "Mark Handoff")], 420),

    ("Step 3", """## 3. One at a time
Handles each message on its own.

When all are done, it stops at **Done**.""",
     [("Loop Over Messages", "Done")], 400),

    ("Step 4", """## 4. Seen it before?
Looks for the `Message ID` in Airtable.

Facebook sometimes sends the same message twice. If we saw it before, skip it.""",
     [("Check Duplicate", None), ("New Message?", "Skip Duplicate")], 480),

    ("Step 5", """## 5. Is a human on this chat?
Checks the `Handoffs` table. If the pause time has not passed, the bot stays quiet.

Settings are at the top of **Handoff Check**: pause hours, office hours, and time zone.""",
     [("Check Handoff", None), ("Handoff Check", None), ("Bot Allowed?", "Human Handling (Stay Quiet)")], 700),

    ("Step 6", """## 6. The AI reads and drafts
Gets the last 5 messages with this customer, so the AI knows the chat so far.

The AI picks the intent (what the person wants), a confidence score, and writes a short reply.

**OpenRouter** is the service that runs the AI model.""",
     [("Get History", None), ("Build Context", None), ("Classify and Draft", "OpenRouter Chat Model")], 760),

    ("Step 7", """## 7. Safety checks
Code checks the AI answer. Hard rules win over the AI:
- a greeting always gets a reply
- "talk to a human" always goes to a human
- price, demo, timeline, and complaints always go to a human
- confidence under 0.7 goes to a human
- a broken AI answer goes to a human""",
     [("Parse JSON", None), ("Human Needed?", None)], 520),

    ("Step 8", """## 8. Reply or hand off
**Human needed:** alert the team in Slack. Then send the customer a "please wait" message (a holding reply).

**No human needed:** send the AI reply on Facebook.""",
     [("Alert Team", None), ("Send Holding Reply", "Send Reply")], 480),

    ("Step 9", """## 9. Save the chat
Adds one row to the `Conversations` table: the message, intent, confidence, reply, and status.

Then goes back for the next message.""",
     [("Log Row", None)], 400),
]

VERIFY = ("Facebook setup check", """## Facebook setup check (one time)
When you add the webhook in your Meta app, Facebook calls this address once to test it.

**Token OK?** checks that the verify token (a password you pick) matches. If it matches, it sends back Facebook's test code. If not, it answers `Forbidden`.""",
          [("FB Verify (GET)", None), ("Token OK?", None), ("Echo Challenge", "Reject")], 700)

NODE_NOTES = {
    "FB Verify (GET)": "Facebook calls this once to check the webhook when you set it up.",
    "Token OK?": "Checks the verify token from Facebook. It must match the token in your Meta app.",
    "Echo Challenge": "Sends Facebook's test code back. This proves we own the webhook.",
    "Reject": "Wrong token. Answers 403 Forbidden.",
    "FB Messages (POST)": "Facebook sends every new Page message here.",
    "Parse Message": "Pulls out sender, text, and message ID. Marks team replies as human_reply. Skips the bot's own replies. Set APP_ID here.",
    "Human Reply?": "True: a team member replied by hand. False: a customer message.",
    "Mark Handoff": "Saves 'Paused Until' = now + 6 hours in the Handoffs table.",
    "Loop Over Messages": "Handles one customer message at a time.",
    "Done": "All messages are handled.",
    "Check Duplicate": "Looks for this Message ID in the Conversations table.",
    "New Message?": "True: not seen before. False: a repeat from Facebook.",
    "Skip Duplicate": "Skips a repeat message.",
    "Check Handoff": "Looks up this customer in the Handoffs table.",
    "Handoff Check": "Decides if the bot may answer. Settings: PAUSE_HOURS, OFFICE_HOURS_ONLY, TZ_OFFSET, OFFICE_START, OFFICE_END.",
    "Bot Allowed?": "True: the bot answers. False: a human is on the chat.",
    "Human Handling (Stay Quiet)": "A human is on this chat, so the bot says nothing.",
    "Get History": "Gets the last 5 rows for this customer from Conversations.",
    "Build Context": "Puts the new message and the history together for the AI.",
    "Classify and Draft": "The AI picks the intent, confidence, and needs_human, and writes a reply. If it fails, the flow goes on and Parse JSON sends it to a human.",
    "OpenRouter Chat Model": "The AI model for Classify and Draft. Change the model here.",
    "Parse JSON": "Reads the AI answer and applies the safety rules. Picks the holding reply.",
    "Human Needed?": "True: hand off to a human. False: send the AI reply.",
    "Alert Team": "Posts the lead in the Slack channel #new_fb_lead.",
    "Send Holding Reply": "Tells the customer that Rey will reply soon.",
    "Send Reply": "Sends the AI reply on Facebook (Graph API v21.0).",
    "Log Row": "Saves the chat in Conversations. Status is escalated or auto_replied.",
}

# ---------- Layout ----------

GRID = 20
TOP = 0
SECTION_H = 780
NODE_Y = 400
LOWER_Y = 620
GAP = 40
NODE_STEP = 220
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


def place(by_name, left, width, columns, top_y, bottom_y):
    span = (len(columns) - 1) * NODE_STEP + NODE_W
    start = left + (width - span) / 2
    for i, (top, bottom) in enumerate(columns):
        x = snap(start + i * NODE_STEP)
        by_name[top]["position"] = [x, top_y]
        if bottom:
            by_name[bottom]["position"] = [x, bottom_y]


def main(dry_run=False, source=None):
    if source:
        wf = json.loads(pathlib.Path(source).read_text(encoding="utf-8"))
    else:
        wf = api("GET", f"/workflows/{WORKFLOW_ID}")
    nodes = [n for n in wf["nodes"] if n["type"] != "n8n-nodes-base.stickyNote"]
    by_name = {n["name"]: n for n in nodes}

    stickies = [sticky("Overview", -780, TOP, 740, 1540, OVERVIEW, 4)]

    x = 0
    for title, text, columns, width in SECTIONS:
        stickies.append(sticky(title, x, TOP, width, SECTION_H, text))
        place(by_name, x, width, columns, NODE_Y, LOWER_Y)
        x += width + GAP

    # Setup check lane under steps 1 and 2
    v_title, v_text, v_cols, v_width = VERIFY
    v_y = TOP + SECTION_H + GAP
    stickies.append(sticky(v_title, 0, v_y, v_width, 720, v_text, 5))
    place(by_name, 0, v_width, v_cols, v_y + 340, v_y + 540)

    for name, note in NODE_NOTES.items():
        by_name[name]["notes"] = note

    body = {
        "name": wf["name"],
        "nodes": stickies + nodes,
        "connections": wf["connections"],
        "settings": wf["settings"],
    }
    saved = body if dry_run else api("PUT", f"/workflows/{WORKFLOW_ID}", body)

    out = HERE / "workflows" / "facebook-page-handler.json"
    out.parent.mkdir(exist_ok=True)
    keep = json.loads(json.dumps({k: saved[k] for k in ("name", "nodes", "connections", "settings")}))
    # The verify token is a password. Keep it out of the repo.
    for n in keep["nodes"]:
        if n["name"] == "Token OK?":
            for c in n["parameters"]["conditions"]["conditions"]:
                c["rightValue"] = "YOUR_VERIFY_TOKEN"
    out.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved", len(saved["nodes"]), "nodes. active:", saved.get("active"),
          "| version:", saved.get("versionId"), "| live version:", saved.get("activeVersionId"))
    for k in ("message", "reason"):
        if k in saved:
            print(k, saved[k])


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="write the JSON file only, do not save to n8n")
    p.add_argument("--source", help="read the workflow from this JSON file instead of n8n")
    a = p.parse_args()
    main(a.dry_run, a.source)
