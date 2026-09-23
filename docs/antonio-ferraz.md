# Antonio Ferraz — AI support inbox triage (job test)

## Brief
A company gets customer requests in a shared inbox. Build an n8n flow that:
classifies each email with AI (6 categories), drafts a reply, saves everything in a database,
and alerts a person when confidence is below 80%, the email is a refund, or it needs review.
Must have: duplicate prevention, error handling, editable prompts, clean layout, status tracking.
Deliver to maria@antonioferraz.co: Loom (5–10 min), prompts, assumptions, time spent. Time cap: 120 min.

## Chosen route
Gmail (trigger, drafts, alerts) → OpenRouter `openai/gpt-6-luna` → Airtable.

| Item | Value |
|---|---|
| Main workflow | `DcisRFWqJau42YlV` — Support Inbox Triage (Antonio Ferraz demo) |
| Error workflow | `E6ZnhNKJvC5yA7vv` — Support Inbox Triage - Error Alert |
| Test sender | `Y0t0EzKIT4E6ZK11` — Support Inbox Triage - Send Test Emails |
| Airtable | base `appVl3yjG9npCQ5Rz`, table `tblXRz41XCCWiRrKx` (Support Requests) |
| Support inbox | rwbfreelancer@gmail.com |
| Alerts | rwbfreelancer+alerts@gmail.com (the trigger skips this address) |
| Builder | `scripts/build_antonio_ferraz.py` → `workflows/antonio-ferraz/*.json` |
| Prompt | `workflows/antonio-ferraz/system-prompt.md` |

## Docs and versions checked (n8n 2.40.5)
- Gmail Trigger 1.4, Gmail 2.2, Airtable 2.2, Set 3.5, If 2.3, Code 2, Loop Over Items 3,
  Basic LLM Chain 1.9, OpenRouter Chat Model 1, Structured Output Parser 1.3.
- https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.gmailtrigger/
- https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.airtable/
- https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatopenrouter/
- https://developers.openai.com/api/docs/guides/latest-model (GPT-6 Luna: lean prompts, schema for shape)
- https://developers.openai.com/api/docs/guides/structured-outputs

## Test results (2026-09-23)
Prompt test, direct API, 7 emails: 7/7 correct categories. The injection line was ignored.

End to end, 8 emails from the test sender:

| Email | Category | Conf. | Status | Alert |
|---|---|---|---|---|
| Charged twice this month | Billing | 98% | Drafted | no |
| Can't log in after password reset | Access | 99% | Drafted | no |
| Move my appointment | Scheduling | 98% | Drafted | no |
| Export button gives error 500 | Technical Support | 99% | Drafted | no |
| Office in Lisbon? | General Question | 98% | Drafted | no |
| Refund please | Refund Request | 99% | Needs Review | yes (refund) |
| THIS IS A JOKE (angry, lawyer, injection) | Billing | 78% | Needs Review | yes (review + low conf.) |
| quick question (vague) | General Question | 45% | Needs Review | yes (low conf.) |

## Issues found and fixed
1. `-from:me` skipped all test mail. The test account is an alias of the inbox. Fix: send alerts to `+alerts` and skip only that address.
2. "Multiple matches found" on 8 emails at once. The Airtable search returns 1 empty item for many inputs, and item links break. Fix: Loop Over Items, one email at a time.
3. Gmail search lag: 2 of 8 emails came in the first poll, 6 in the next. No email was lost.

## Loom talk track (5–10 min)
1. **What I built (1 min).** Show Airtable with rows, one Gmail draft, one alert email.
2. **Start to finish (3 min).** Walk the 5 colored steps on the canvas, left to right.
3. **Why this structure (1 min).** One AI call, not two. The prompt is in one Settings node. The row is logged before the AI runs. The AI only drafts. A person sends.
4. **Edge cases and errors (2 min).**
   - Duplicates: the Message ID check in Airtable.
   - Alert loop: alerts go to `+alerts`, and the trigger skips that address.
   - Bad AI output: the schema, then Check AI Answer (unknown category, empty draft, score outside 0–1).
   - AI down: 3 retries, then the row is set to Error and the team gets an email.
   - Any other failure: the error workflow emails the team with a link to the run.
   - Prompt injection: the email is treated as data. The angry test email proves it.
   - Empty or long emails: default text, and the body is cut at 6,000 characters.
   - Gmail search lag: emails that arrive late are caught on the next poll.
5. **Before production (1 min).**
   - Test on 50–100 real past emails, then tune the categories and the 80% rule.
   - Give the AI the real policies (refunds, prices, hours), so drafts can answer more.
   - Use Gmail push (instant) instead of a 1-minute poll, and use a real shared inbox.
   - Send alerts to Slack. Add an Airtable view per status.
   - Track how much people edit the drafts, to measure quality.
   - Set data retention for customer emails, and add monitoring for failed runs.
