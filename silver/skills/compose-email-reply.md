# Skill: Compose Email Reply

## Purpose

Read an EMAIL_ VaultItem from `/Needs_Action/`, consult `Company_Handbook.md` for tone and approval rules, draft a professional reply, and send or draft it via the email MCP tools based on sensitivity classification.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the EMAIL_ VaultItem

Read the EMAIL_ `.md` file provided as context from `/Needs_Action/`. Extract the YAML frontmatter fields:
- `email_id` — Gmail message ID
- `from` — sender email address
- `from_name` — sender display name
- `to` — recipient (our email)
- `subject` — email subject line
- `sensitivity` — sensitive or non-sensitive
- `priority` — high, medium, or low
- `has_attachments` — true or false

Read the full email body from the `## Email Content` section.

### Step 2: Consult the Company Handbook

Read `Company_Handbook.md` from the vault root. Check:
- **Communication tone**: Professional, helpful, concise
- **Approval rules for email**:
  - Email to unknown recipient → approval required
  - Email with financial content → approval required
  - Email reply to known, non-sensitive → auto-send (no approval)
  - WhatsApp reply → always requires approval
- **Sensitivity classification** (already in frontmatter):
  - `sensitive`: new/unknown sender, financial content, attachments
  - `non-sensitive`: known sender, informational, no financial content

### Step 3: Draft the Reply

Compose a professional email reply following these rules:
- Use the subject from the original email, prepend "Re: " if not already present
- Address the sender by name if available
- Keep the reply concise and action-oriented
- Match the tone guidance from Company Handbook
- If the email asks a question, provide a helpful answer or acknowledge and promise follow-up
- If the email contains a request, acknowledge receipt and outline next steps
- Never disclose internal processes or AI involvement
- Never commit to specific timelines unless explicitly authorized in the handbook

### Step 4: Determine Action Based on Sensitivity

**If `sensitivity: non-sensitive`** (known sender, no financial content, no attachments):
- Use the `send_email` MCP tool to send the reply directly
- Set `in_reply_to` to the original email's message ID for threading
- Set `thread_id` if available for Gmail thread grouping
- Log the action as `email_sent`

**If `sensitivity: sensitive`** (unknown sender, financial content, or attachments):
- Use the `draft_email` MCP tool to create a draft for human review
- The draft will appear in Gmail for the human to review and send manually
- Log the action as `email_drafted`

### Step 5: Log the Result

After sending or drafting, log the outcome. The orchestrator will handle audit logging.

## Reply Template

```
Subject: Re: {original_subject}
To: {from_address}

Hi {from_name},

{reply_body}

Best regards,
{Company name from handbook}
```

## Rules

- NEVER send sensitive emails directly. Always use draft_email for sensitive content.
- NEVER disclose that replies are AI-generated.
- ALWAYS include the original subject with "Re: " prefix.
- ALWAYS use `in_reply_to` for proper email threading.
- Keep replies under 200 words unless the context requires more detail.
- If you cannot determine an appropriate reply, create a draft with a note explaining why.

## Tools Required

- `Read` — to read EMAIL_ VaultItem and Company_Handbook.md
- `send_email` (MCP) — to send non-sensitive replies directly
- `draft_email` (MCP) — to create drafts for sensitive replies
