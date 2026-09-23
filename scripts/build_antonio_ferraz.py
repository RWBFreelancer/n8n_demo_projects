"""Build the n8n workflow JSON for the antonio-ferraz support triage demo.

Usage: python scripts/build_antonio_ferraz.py [credentials.json]
credentials.json (optional, not secret) maps credential type -> {"id": "...", "name": "..."}.
The system prompt is read from workflows/antonio-ferraz/system-prompt.md.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "workflows" / "antonio-ferraz"

BASE_ID = "appVl3yjG9npCQ5Rz"
TABLE_ID = "tblXRz41XCCWiRrKx"
MODEL = "openai/gpt-6-luna"
ALERT_EMAIL = "rwbfreelancer@gmail.com"
CATEGORIES = ["Billing", "Access", "Scheduling", "Technical Support", "General Question", "Refund Request"]
STATUSES = ["Processing", "Drafted", "Needs Review", "Error"]

creds = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}


def cred(ctype):
    c = creds.get(ctype)
    return {ctype: c} if c else {}


def node(name, ntype, version, pos, params, **extra):
    n = {"parameters": params, "name": name, "type": ntype, "typeVersion": version, "position": pos}
    n.update(extra)
    return n


def sticky(name, pos, w, h, text, color=7):
    return node(name, "n8n-nodes-base.stickyNote", 1, pos,
                {"content": text, "width": w, "height": h, "color": color})


def rl(value):
    return {"__rl": True, "value": value, "mode": "id"}


# ---------- Airtable helpers ----------
FIELD_TYPES = {
    "Message ID": "string", "Status": "options", "Received At": "dateTime", "From": "string",
    "Subject": "string", "Message": "string", "Category": "options", "Confidence": "number",
    "Needs Review": "boolean", "Review Reason": "string", "AI Summary": "string",
    "Draft Response": "string", "Alert Sent": "boolean", "Thread ID": "string",
    "Error Message": "string", "Execution ID": "string",
}


def schema_entry(fid, used):
    e = {"id": fid, "displayName": fid, "required": False, "defaultMatch": fid == "id",
         "canBeUsedToMatch": True, "display": True, "type": FIELD_TYPES.get(fid, "string"),
         "readOnly": False, "removed": not used}
    if fid == "Status":
        e["options"] = [{"name": s, "value": s} for s in STATUSES]
    if fid == "Category":
        e["options"] = [{"name": c, "value": c} for c in CATEGORIES]
    return e


def airtable(name, pos, operation, values=None, **extra):
    p = {"operation": operation, "base": rl(BASE_ID), "table": rl(TABLE_ID)}
    if values is not None:
        is_update = operation == "update"
        ids = (["id"] if is_update else []) + list(FIELD_TYPES)
        p["columns"] = {
            "mappingMode": "defineBelow",
            "value": values,
            "matchingColumns": ["id"] if is_update else [],
            "schema": [schema_entry(f, f in values) for f in ids],
            "attemptToConvertTypes": False,
            "convertFieldsToString": False,
        }
        p["options"] = {"typecast": True}
    return node(name, "n8n-nodes-base.airtable", 2.2, pos, p,
                credentials=cred("airtableTokenApi"), **extra)


def assign(name, value, vtype="string"):
    return {"id": name, "name": name, "value": value, "type": vtype}


def set_node(name, pos, assignments):
    return node(name, "n8n-nodes-base.set", 3.5, pos,
                {"assignments": {"assignments": assignments}, "options": {}})


def if_node(name, pos, expr):
    return node(name, "n8n-nodes-base.if", 2.3, pos, {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 3},
            "conditions": [{"id": name, "leftValue": expr, "rightValue": "",
                            "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
            "combinator": "and",
        },
        "options": {},
    })


def gmail_send(name, pos, to, subject, message):
    return node(name, "n8n-nodes-base.gmail", 2.2, pos, {
        "resource": "message", "operation": "send", "sendTo": to, "subject": subject,
        "emailType": "text", "message": message, "options": {"appendAttribution": False},
    }, credentials=cred("gmailOAuth2"), webhookId=name.lower().replace(" ", "-"))


# ---------- Expressions ----------
E = "$('Normalize Email').item.json"
REC = "$('Save Email').item.json.id"
AI = "$('Check AI Result').item.json"
RECORD_URL = f"https://airtable.com/{BASE_ID}/{TABLE_ID}/{{{{ {REC} }}}}"
THREAD_URL = f"https://mail.google.com/mail/u/0/#all/{{{{ {E}.threadId }}}}"

system_prompt = (OUT / "system-prompt.md").read_text(encoding="utf-8").strip()

USER_PROMPT = (
    "=<email>\n"
    f"From: {{{{ {E}.from }}}}\n"
    f"Subject: {{{{ {E}.subject }}}}\n\n"
    f"{{{{ {E}.body }}}}\n"
    "</email>"
)

OUTPUT_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "confidence": {"type": "number", "description": "0 to 1"},
        "needs_human_review": {"type": "boolean"},
        "review_reason": {"type": "string"},
        "summary": {"type": "string"},
        "draft_reply": {"type": "string"},
    },
    "required": ["category", "confidence", "needs_human_review", "review_reason", "summary", "draft_reply"],
}, indent=2)

CHECK_AI_CODE = """// Check the AI answer. Never trust it blindly.
const config = $('Config').item.json;
const ai = $json.output ?? {};
const allowed = %s;

const knownCategory = allowed.includes(ai.category);
const category = knownCategory ? ai.category : 'General Question';

let confidence = Number(ai.confidence);
if (!Number.isFinite(confidence)) confidence = 0;
confidence = Math.min(1, Math.max(0, confidence));

const draftReply = String(ai.draft_reply ?? '').trim();

// Collect every reason a person must look at this email.
const reasons = [];
if (ai.needs_human_review === true) reasons.push(ai.review_reason || 'AI asked for a human review.');
if (!knownCategory) reasons.push('AI gave an unknown category.');
if (!draftReply) reasons.push('AI did not write a draft.');
if (confidence < config.confidenceThreshold) reasons.push(`Low confidence (${Math.round(confidence * 100)}%%).`);
if (category === 'Refund Request') reasons.push('Refund request.');

const sendAlert = reasons.length > 0;

return {
  json: {
    category,
    confidence,
    summary: String(ai.summary ?? ''),
    draftReply,
    sendAlert,
    reviewReason: reasons.join(' '),
    status: sendAlert ? 'Needs Review' : 'Drafted',
  },
};""" % json.dumps(CATEGORIES)

ALERT_TEXT = (
    f"=A support email needs a person.\n\n"
    f"Why: {{{{ {AI}.reviewReason }}}}\n"
    f"Category: {{{{ {AI}.category }}}}\n"
    f"Confidence: {{{{ Math.round({AI}.confidence * 100) }}}}%\n\n"
    f"From: {{{{ {E}.from }}}}\n"
    f"Subject: {{{{ {E}.subject }}}}\n"
    f"Summary: {{{{ {AI}.summary }}}}\n\n"
    f"A draft reply is waiting in Gmail. Check it before you send it.\n\n"
    f"Open the email: {THREAD_URL}\n"
    f"Open the record: {RECORD_URL}\n"
)

ERROR_TEXT = (
    f"=The AI step failed for one support email. No draft was made.\n\n"
    f"Error: {{{{ $json.error?.message ?? $json.error ?? 'Unknown error' }}}}\n\n"
    f"From: {{{{ {E}.from }}}}\n"
    f"Subject: {{{{ {E}.subject }}}}\n\n"
    f"Open the email: {THREAD_URL}\n"
    f"Open the record: {RECORD_URL}\n"
)

# ---------- Nodes ----------
nodes = [
    sticky("Note: Intake", [-60, 80], 1220, 600,
           "## 1. New email in, duplicates out\n"
           "Checks Gmail every minute. Skips emails sent by us, so alerts never loop back.\n"
           "**Config** holds everything you may want to edit: the AI prompt, the 80% confidence rule, and the alert email.\n"
           "An email that is already in Airtable (same Message ID) is skipped.", 5),
    sticky("Note: AI", [1180, 80], 600, 640,
           "## 2. Log it, then let AI sort it and write a draft\n"
           "A row is saved first with status **Processing**, so every email is tracked even if the AI fails.\n"
           "The AI returns fixed JSON fields. **Check AI Result** cleans the answer and decides if a person must look.\n"
           "If the AI fails after 3 tries, the row is set to **Error** and an alert is sent.", 6),
    sticky("Note: Output", [1780, 80], 1100, 440,
           "## 3. Save, draft, alert\n"
           "Saves the category, confidence, and draft in Airtable. Puts the draft in the Gmail thread. It never sends the draft.\n"
           "Sends an alert if confidence is below 80%, it is a refund, or the AI asks for a person.", 4),

    node("Gmail Trigger", "n8n-nodes-base.gmailTrigger", 1.4, [0, 300], {
        "pollTimes": {"item": [{"mode": "everyMinute"}]},
        "simple": False,
        "filters": {"q": "in:inbox -from:me", "readStatus": "both"},
        "options": {},
    }, credentials=cred("gmailOAuth2")),

    set_node("Config", [220, 300], [
        assign("systemPrompt", system_prompt),
        assign("confidenceThreshold", 0.8, "number"),
        assign("alertEmail", ALERT_EMAIL),
    ]),

    set_node("Normalize Email", [440, 300], [
        assign("messageId", "={{ $('Gmail Trigger').item.json.id }}"),
        assign("threadId", "={{ $('Gmail Trigger').item.json.threadId }}"),
        assign("from", "={{ $('Gmail Trigger').item.json.from?.text ?? '' }}"),
        assign("fromEmail", "={{ $('Gmail Trigger').item.json.from?.value?.[0]?.address ?? '' }}"),
        assign("subject", "={{ $('Gmail Trigger').item.json.subject || '(no subject)' }}"),
        assign("body", "={{ ($('Gmail Trigger').item.json.text ?? '').trim().slice(0, 6000) || '(empty message)' }}"),
        assign("receivedAt", "={{ $('Gmail Trigger').item.json.date ?? $now.toISO() }}"),
    ]),

    node("Find Existing Record", "n8n-nodes-base.airtable", 2.2, [660, 300], {
        "operation": "search", "base": rl(BASE_ID), "table": rl(TABLE_ID),
        "filterByFormula": f"={{Message ID}} = '{{{{ {E}.messageId }}}}'",
        "returnAll": False, "limit": 1,
        "options": {"fields": ["Message ID"]},
    }, credentials=cred("airtableTokenApi"),
        alwaysOutputData=True, retryOnFail=True, maxTries=3, waitBetweenTries=2000),

    if_node("Is New Email?", [860, 300], "={{ !$json.id }}"),

    node("Skip Duplicate", "n8n-nodes-base.noOp", 1, [1060, 460], {}),

    airtable("Save Email", [1220, 280], "create", {
        "Message ID": f"={{{{ {E}.messageId }}}}",
        "Thread ID": f"={{{{ {E}.threadId }}}}",
        "Status": "Processing",
        "Received At": f"={{{{ {E}.receivedAt }}}}",
        "From": f"={{{{ {E}.from }}}}",
        "Subject": f"={{{{ {E}.subject }}}}",
        "Message": f"={{{{ {E}.body }}}}",
        "Execution ID": "={{ $execution.id }}",
    }, retryOnFail=True, maxTries=3, waitBetweenTries=2000),

    node("Classify & Draft Reply", "@n8n/n8n-nodes-langchain.chainLlm", 1.9, [1440, 280], {
        "promptType": "define",
        "text": USER_PROMPT,
        "hasOutputParser": True,
        "messages": {"messageValues": [{"message": "={{ $('Config').item.json.systemPrompt }}"}]},
    }, retryOnFail=True, maxTries=3, waitBetweenTries=5000, onError="continueErrorOutput"),

    node("OpenRouter Model", "@n8n/n8n-nodes-langchain.lmChatOpenRouter", 1, [1380, 520], {
        "model": MODEL,
        "options": {"temperature": 0.2, "responseFormat": "json_object", "timeout": 60000, "maxRetries": 2},
    }, credentials=cred("openRouterApi")),

    node("AI Output Format", "@n8n/n8n-nodes-langchain.outputParserStructured", 1.3, [1560, 520], {
        "schemaType": "manual",
        "inputSchema": OUTPUT_SCHEMA,
    }),

    node("Check AI Result", "n8n-nodes-base.code", 2, [1840, 280], {
        "mode": "runOnceForEachItem",
        "jsCode": CHECK_AI_CODE,
    }),

    airtable("Save AI Result", [2060, 280], "update", {
        "id": f"={{{{ {REC} }}}}",
        "Status": "={{ $json.status }}",
        "Category": "={{ $json.category }}",
        "Confidence": "={{ $json.confidence }}",
        "Needs Review": "={{ $json.sendAlert }}",
        "Review Reason": "={{ $json.reviewReason }}",
        "AI Summary": "={{ $json.summary }}",
        "Draft Response": "={{ $json.draftReply }}",
    }, retryOnFail=True, maxTries=3, waitBetweenTries=2000),

    node("Create Gmail Draft", "n8n-nodes-base.gmail", 2.2, [2280, 280], {
        "resource": "draft", "operation": "create",
        "subject": f"=Re: {{{{ {E}.subject }}}}",
        "emailType": "text",
        "message": f"={{{{ {AI}.draftReply }}}}",
        "options": {"threadId": f"={{{{ {E}.threadId }}}}", "sendTo": f"={{{{ {E}.fromEmail }}}}"},
    }, credentials=cred("gmailOAuth2")),

    if_node("Needs a Person?", [2500, 280], f"={{{{ {AI}.sendAlert }}}}"),

    gmail_send("Send Alert", [2720, 200],
               "={{ $('Config').item.json.alertEmail }}",
               f"=[Support] {{{{ {AI}.category }}}} needs a person: {{{{ {E}.subject }}}}",
               ALERT_TEXT),

    airtable("Mark Alert Sent", [2940, 200], "update", {
        "id": f"={{{{ {REC} }}}}",
        "Alert Sent": True,
    }, retryOnFail=True, maxTries=3, waitBetweenTries=2000),

    sticky("Note: AI error", [1780, 560], 660, 260,
           "## If the AI fails\nMarks the row as **Error** and emails the team.", 3),

    airtable("Log AI Error", [1840, 640], "update", {
        "id": f"={{{{ {REC} }}}}",
        "Status": "Error",
        "Needs Review": True,
        "Error Message": "={{ $json.error?.message ?? $json.error ?? 'Unknown error' }}",
    }),

    gmail_send("Send AI Error Alert", [2060, 640],
               "={{ $('Config').item.json.alertEmail }}",
               f"=[Support] AI failed: {{{{ {E}.subject }}}}",
               ERROR_TEXT),
]

def link(to, idx=0):
    return {"node": to, "type": "main", "index": idx}


connections = {
    "Gmail Trigger": {"main": [[link("Config")]]},
    "Config": {"main": [[link("Normalize Email")]]},
    "Normalize Email": {"main": [[link("Find Existing Record")]]},
    "Find Existing Record": {"main": [[link("Is New Email?")]]},
    "Is New Email?": {"main": [[link("Save Email")], [link("Skip Duplicate")]]},
    "Save Email": {"main": [[link("Classify & Draft Reply")]]},
    "Classify & Draft Reply": {"main": [[link("Check AI Result")], [link("Log AI Error")]]},
    "OpenRouter Model": {"ai_languageModel": [[{"node": "Classify & Draft Reply", "type": "ai_languageModel", "index": 0}]]},
    "AI Output Format": {"ai_outputParser": [[{"node": "Classify & Draft Reply", "type": "ai_outputParser", "index": 0}]]},
    "Check AI Result": {"main": [[link("Save AI Result")]]},
    "Save AI Result": {"main": [[link("Create Gmail Draft")]]},
    "Create Gmail Draft": {"main": [[link("Needs a Person?")]]},
    "Needs a Person?": {"main": [[link("Send Alert")], []]},
    "Send Alert": {"main": [[link("Mark Alert Sent")]]},
    "Log AI Error": {"main": [[link("Send AI Error Alert")]]},
}

settings = {"executionOrder": "v1", "saveDataErrorExecution": "all", "saveDataSuccessExecution": "all",
            "saveManualExecutions": True}
if creds.get("errorWorkflowId"):
    settings["errorWorkflow"] = creds["errorWorkflowId"]

main_wf = {"name": "Support Inbox Triage (Antonio Ferraz demo)", "nodes": nodes,
           "connections": connections, "settings": settings}

# ---------- Error workflow ----------
error_wf = {
    "name": "Support Inbox Triage - Error Alert",
    "nodes": [
        node("Error Trigger", "n8n-nodes-base.errorTrigger", 1, [0, 300], {}),
        gmail_send("Send Error Email", [240, 300], ALERT_EMAIL,
                   "=[Support] Workflow error: {{ $json.workflow.name }}",
                   "=The support triage workflow stopped with an error.\n\n"
                   "Node: {{ $json.execution.lastNodeExecuted }}\n"
                   "Error: {{ $json.execution.error.message }}\n\n"
                   "Open the run: {{ $json.execution.url }}\n"),
    ],
    "connections": {"Error Trigger": {"main": [[link("Send Error Email")]]}},
    "settings": {"executionOrder": "v1"},
}

(OUT / "support-triage.json").write_text(json.dumps(main_wf, indent=2), encoding="utf-8")
(OUT / "error-alert.json").write_text(json.dumps(error_wf, indent=2), encoding="utf-8")
print("wrote", OUT / "support-triage.json", "and", OUT / "error-alert.json")
