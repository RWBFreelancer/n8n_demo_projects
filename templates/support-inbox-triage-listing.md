# Creator Portal listing: Support Inbox Triage

File: `templates/support-inbox-triage-clean.json`

## Title

Triage support emails with AI, log them in Airtable, and draft Gmail replies

## Description

### Who is this for
Small support teams that get customer emails in Gmail and want a first sort and a first draft, without sending anything by accident.

### What it does
- Checks your Gmail inbox every minute.
- Handles each email once. Emails already in Airtable are skipped.
- Logs every email in Airtable, so nothing gets lost.
- Uses an AI model (through OpenRouter) to pick a category, give a confidence score, write a summary, and write a draft reply.
- Puts the draft reply in the Gmail thread. It never sends it. A person checks and sends.
- Emails your team when a person must look: low confidence, refund requests, angry customers, legal threats, or a possible account break-in.
- If the AI fails, it marks the row as Error and emails your team.

Categories: Billing, Access, Scheduling, Technical Support, Refund Request, General Question.

### Requirements
- Gmail account (OAuth2)
- Airtable account and a Personal Access Token
- OpenRouter API key (you can swap in any other chat model node)

## How to set up

1. Import the workflow.
2. Add a Gmail OAuth2 credential to the 4 Gmail nodes.
3. Add an Airtable Personal Access Token credential to the 5 Airtable nodes.
4. Add an OpenRouter credential to **OpenRouter Chat Model** and pick a model.
5. Make an Airtable table with these fields:
   - `Message ID`, `Thread ID`, `From`, `Subject`, `Review Reason`, `Execution ID` (single line text)
   - `Message`, `AI Summary`, `Draft Response`, `Error Message` (long text)
   - `Status`, `Category` (single select)
   - `Received At` (date and time), `Confidence` (number)
   - `Needs Review`, `Alert Sent` (checkbox)
6. Open **Settings**. Set `alertEmail`, `airtableBaseId`, and `airtableTableId`.
7. Open **Gmail Trigger**. In the search filter, change `alerts@example.com` to your alert address.
8. Send yourself a test email. Check the Airtable row and the Gmail draft.
9. Activate the workflow.

## How to customize
- Change the categories and reply rules in the prompt in **Settings**.
- Change `confidenceThreshold` (default 0.8) to get more or fewer alerts.
- If you change the category list, also update **Structured Output Parser** and **Check AI Answer**.
