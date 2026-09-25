# Facebook Page Message Handler (v7 - human handoff)

When someone messages the BinAI Facebook Page, this workflow answers for you. An AI reads the message and writes a short reply. If the person needs a real human, the bot sends a "please wait" message and alerts the team in Slack. When a team member replies by hand, the bot stays quiet for that customer for 6 hours.

- n8n workflow: `iK2hDxMAtEt7DTVW` (on `robertgrove.app.n8n.cloud`, live)
- Export: `workflows/facebook-page-handler.json`
- Notes script: `add_notes.py` (adds the canvas notes and the grid layout, then saves to n8n)
  - `--dry-run` builds the JSON file only. It does not change n8n.
  - Without `--dry-run`, it saves to n8n. The workflow is live, so the save also makes the new version live (n8n 2.39 and later). See [Save and publish](https://docs.n8n.io/workflows/publish/).

## How it works

| # | Node | What it does |
|---|---|---|
| 1 | **FB Messages (POST)** | Facebook sends every new Page message here. |
| 1 | **Parse Message** | Pulls out the sender, text, and message ID. It skips empty messages and the bot's own replies. A reply typed by a team member becomes a `human_reply`. |
| 2 | **Human Reply?** | True: a team member replied by hand. False: a customer message. |
| 2 | **Mark Handoff** | Saves `Paused Until` = now + 6 hours in the `Handoffs` table. |
| 3 | **Loop Over Messages** | Handles one customer message at a time. **Done** runs when all are handled. |
| 4 | **Check Duplicate** + **New Message?** | Looks for the `Message ID` in `Conversations`. A repeat goes to **Skip Duplicate**. |
| 5 | **Check Handoff** + **Handoff Check** + **Bot Allowed?** | Checks if a human is on the chat. If yes, the bot stays quiet (**Human Handling (Stay Quiet)**). |
| 6 | **Get History** + **Build Context** | Gets the last 5 rows for this customer, so the AI knows the chat so far. |
| 6 | **Classify and Draft** + **OpenRouter Chat Model** | The AI picks the intent and confidence, decides `needs_human`, and writes a reply. If the AI fails, the flow goes on and step 7 sends it to a human. |
| 7 | **Parse JSON** | Reads the AI answer and applies the safety rules (below). Picks the holding reply. |
| 7 | **Human Needed?** | True: hand off. False: send the AI reply. |
| 8 | **Alert Team** | Posts the lead in the Slack channel `#new_fb_lead`. |
| 8 | **Send Holding Reply** | Tells the customer that Rey will reply soon. |
| 8 | **Send Reply** | Sends the AI reply on Facebook (Graph API `v21.0`). |
| 9 | **Log Row** | Saves the chat in `Conversations`. Status is `escalated` or `auto_replied`. Then it goes back to the loop. |
| – | **FB Verify (GET)**, **Token OK?**, **Echo Challenge**, **Reject** | One-time webhook check from Meta. If the verify token matches, it sends back Facebook's test code. If not, it answers `403 Forbidden`. |

## Safety rules (in Parse JSON)

The code rules win over what the AI decided.

- A plain greeting is never spam. It always gets a reply.
- "Talk to Rey", "are you a bot", and similar words always go to a human.
- Spam needs confidence 0.9 or more. Under that, it becomes `other`.
- `pricing`, `demo_request`, `timeline`, and `complaint` always go to a human.
- Confidence under 0.7 goes to a human.
- An empty reply or a broken AI answer goes to a human.

## Settings (top of Handoff Check)

| Setting | Now | What it does |
|---|---|---|
| `PAUSE_HOURS` | `6` | How long the bot stays quiet after a human replies. (**Mark Handoff** also has `6` in its formula. Change both.) |
| `OFFICE_HOURS_ONLY` | `false` | `true` = the bot only answers when the team is offline. |
| `TZ_OFFSET` | `8` | Time zone. Philippines is UTC+8. |
| `OFFICE_START` / `OFFICE_END` | `9` / `18` | Office hours, Monday to Friday. |

## Setup

1. In Airtable base `Facebook Responder`, make two tables:
   - `Conversations`: `Message ID`, `Sender ID`, `Sender Name`, `Message`, `Intent` (single select), `Confidence`, `Needs Human`, `Reply Sent`, `Reason`, `Status`, `Timestamp`.
   - `Handoffs`: `Sender ID`, `Last Human Reply` (date and time), `Paused Until` (date and time), `Conversation`.
2. Connect credentials for Airtable, OpenRouter, Slack, and Facebook Graph API. Use a Page access token.
3. In the Meta app, set the webhook URL to the production URL of **FB Messages (POST)**. Subscribe to `messages` and `message_echoes`.
4. Put your verify token in **Token OK?**. Use the same token in the Meta app.
5. Put your Meta App ID in **Parse Message** (`APP_ID`). The bot uses it to tell its own replies from team replies.
6. Set the Slack channel in **Alert Team**.

## Words to know

- **Webhook**: a web address. Facebook sends new messages to it.
- **Verify token**: a password you pick. Meta sends it once to prove the webhook is yours.
- **Echo**: a copy of a message your Page sent out. Facebook sends it back, so we can see who sent it (the bot or a person).
- **Handoff**: when a real person takes over the chat from the bot.
- **Intent**: what the person wants, such as `pricing` or `greeting`.
- **Confidence**: how sure the AI is, from 0 (not sure) to 1 (very sure).
- **Holding reply**: a short "please wait, Rey will reply" message.
- **Graph API**: the Facebook service that sends messages from your Page.

## Known limits

- **Token OK?** uses a verify token that is easy to guess. Change it to a long random word, in n8n and in the Meta app.
- **Send Reply** goes on after an error. If Facebook fails, **Log Row** still saves `auto_replied`.
- Spam with confidence 0.9 or more and a non-empty reply gets that reply sent. Spam with an empty reply goes to a human, so the team gets a Slack alert. The comment "Only confirmed spam gets silence" is not true now. `send_holding` is set but no node uses it.
- **OpenRouter Chat Model** has no model set. It uses the node default.
