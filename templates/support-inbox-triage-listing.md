# Creator Portal listing: Support Inbox Triage

File: `templates/support-inbox-triage-clean.json`

## Title

Triage support emails with AI drafts, human review, and error recovery using Gmail, Airtable and OpenRouter

## Description

### Who is this for
Small support teams that get customer emails in Gmail and want a first sort and a first draft, without sending anything by accident.

### What it does
- Checks your Gmail inbox every minute.
- Skips newsletters, auto-replies, and no-reply senders, so you do not pay for AI on junk.
- Reads HTML-only emails too.
- Handles each email once. Emails already in Airtable are skipped.
- Logs every email in Airtable, so nothing gets lost.
- Uses an AI model (through OpenRouter) to pick a category, give a confidence score, write a summary, and write a draft reply. If that model fails, a ChatGPT model (OpenAI) takes over.
- Puts the draft reply in the Gmail thread. It never sends it. A person checks and sends.
- Emails your team when a person must look: low confidence, refund requests, angry customers, legal threats, or a possible account break-in.
- Every step retries 3 times. If a step still fails, the row is marked Error, your team gets an email that names the failed step, and the next email is handled.
- Every 15 minutes, it finds emails that got stuck (for example, after a server restart) and alerts your team.

Default categories: Billing, Access, Scheduling, Technical Support, Refund Request, General Question. You change them in one place.

### Requirements
- Gmail account (OAuth2)
- Airtable account and a Personal Access Token
- OpenRouter API key for the main model (you can swap in any other chat model node)
- OpenAI API key for the fallback model

## How to set up

1. Import the workflow.
2. Add a Gmail OAuth2 credential to **Gmail Trigger** and the 4 Gmail nodes.
3. Add an Airtable Personal Access Token credential to the 7 Airtable nodes.
4. Add an OpenRouter credential to **OpenRouter Response Model** and pick a model.
5. Add an OpenAI credential to **Fallback to OpenAI Model**.
6. Make an Airtable table with these fields:
   - `Message ID`, `Thread ID`, `From`, `Subject`, `Review Reason`, `Execution ID` (single line text)
   - `Message`, `AI Summary`, `Draft Response`, `Error Message` (long text)
   - `Status`, `Category` (single select)
   - `Received At` (date and time), `Confidence` (number)
   - `Needs Review`, `Alert Sent` (checkbox)
7. Open **Set Field Parameters**. Set `alertEmail`, `airtableBaseId`, and `airtableTableId`.
8. Open **Gmail Trigger**. In the search filter, change `alerts@example.com` to your alert address.
9. Send yourself a test email. Check the Airtable row and the Gmail draft.
10. Activate the workflow.

## How to customize
Everything is in the **Set Field Parameters** node:
- Keep the Airtable `Status` options as they are (Processing, Drafted, Needs Review, Error). The workflow depends on these names.
- `categories`: one per line, as `Name: when to use it`.
- `alwaysReviewCategories`: categories that always alert a person (default: Refund Request).
- `confidenceThreshold`: alert below this score (default 0.8).
- `skipSenderPatterns` and `skipBulkEmail`: what mail to skip.
- `stuckAfterMinutes`: when a row counts as stuck (default 30).
- The AI prompt and reply rules are in `systemPrompt`.
