# Skill: Compose WhatsApp Reply

## Purpose

Read a WHATSAPP_ VaultItem from `/Needs_Action/`, consult `Company_Handbook.md` for tone and business rules, draft a professional reply. WhatsApp replies **always require human approval** before sending.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Read the WHATSAPP_ VaultItem

Read the WHATSAPP_ `.md` file provided as context from `/Needs_Action/`. Extract the YAML frontmatter fields:
- `contact` — sender contact name
- `phone` — sender phone number (if available)
- `message_text` — full message text
- `keywords_matched` — which business keywords triggered this item
- `priority` — high, medium, or low

Read the full message from the `## Message Details` section.

### Step 2: Consult the Company Handbook

Read `Company_Handbook.md` from the vault root. Check:
- **Communication tone**: Professional, helpful, concise
- **Approval rules**: WhatsApp replies **always require approval** — no exceptions
- **Business keywords context**: Understand what each keyword implies:
  - `urgent/deadline` → acknowledge urgency, promise prompt follow-up
  - `invoice/payment` → acknowledge receipt, confirm review process
  - `pricing/quote` → thank for inquiry, outline next steps
  - `help` → offer assistance, ask for specifics
  - `project` → acknowledge update, confirm review

### Step 3: Draft the Reply

Compose a professional WhatsApp reply following these rules:
- Keep it concise (WhatsApp is informal — max 3-4 sentences)
- Address the contact by name
- Acknowledge their specific message topic (based on keywords)
- Provide a helpful, professional response
- Never disclose internal processes or AI involvement
- Never commit to specific timelines unless authorized in the handbook
- Use a friendly but professional tone (WhatsApp is less formal than email)

### Step 4: Create Approval Request

WhatsApp replies **always require approval**. Create an ApprovalRequest in `/Pending_Approval/` named `APPROVE_WHATSAPP_{contact_slug}_{timestamp}.md`:

```yaml
---
type: approval_request
action: whatsapp_reply
details: "Reply to WhatsApp message from {contact} about {keywords}"
amount: null
recipient: "{contact}"
reason: "Business keyword message requires response"
related_plan: "Plans/PLAN_WHATSAPP_{contact_slug}_{timestamp}.md"
reply_content: "{the drafted reply text}"
created: {current ISO 8601 timestamp}
expires: {24 hours from now ISO 8601}
status: pending
---

## Action Details

Reply to WhatsApp message from {contact} regarding: {keywords_matched}.

## Content to Send

{The actual WhatsApp reply text}

## To Approve

Move this file to the `/Approved/` folder.

## To Reject

Move this file to the `/Rejected/` folder.
```

### Step 5: Log the Result

Log the approval request creation. The orchestrator will handle sending after approval.

## Rules

- NEVER send WhatsApp replies without approval. Always create an approval request.
- NEVER disclose that replies are AI-generated.
- Keep replies under 100 words (WhatsApp style).
- Always acknowledge the specific topic the contact raised.
- If the message is unclear, draft a polite clarification request.

## Tools Required

- `Read` — to read WHATSAPP_ VaultItem and Company_Handbook.md
- `Write` — to create approval request file
- `Glob` — to check for existing plans/approvals
