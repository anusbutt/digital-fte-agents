# Contract: Email MCP Server Tools

**Server**: email-mcp
**Transport**: stdio
**Date**: 2026-02-18

## Tool: send_email

Send an email via Gmail API.

**Input Schema**:

```json
{
  "type": "object",
  "properties": {
    "to": { "type": "string", "description": "Recipient email address" },
    "subject": { "type": "string", "description": "Email subject line" },
    "body": { "type": "string", "description": "Email body (plain text)" },
    "cc": { "type": "string", "description": "CC recipients (comma-separated)", "optional": true },
    "bcc": { "type": "string", "description": "BCC recipients (comma-separated)", "optional": true },
    "in_reply_to": { "type": "string", "description": "Message-ID to reply to", "optional": true },
    "thread_id": { "type": "string", "description": "Gmail thread ID for threading", "optional": true }
  },
  "required": ["to", "subject", "body"]
}
```

**Output Schema (success)**:

```json
{
  "success": true,
  "messageId": "msg-id-from-gmail",
  "threadId": "thread-id"
}
```

**Output Schema (error)**:

```json
{
  "success": false,
  "error": "Error description",
  "code": "AUTH_EXPIRED | RATE_LIMIT | INVALID_RECIPIENT | SEND_FAILED"
}
```

**Error Codes**:
- `AUTH_EXPIRED`: OAuth2 token expired. Attempt refresh. If refresh fails, return this error.
- `RATE_LIMIT`: Gmail API 429. Return error, caller should retry.
- `INVALID_RECIPIENT`: Bad email address format. Do NOT retry.
- `SEND_FAILED`: Gmail API 5xx. Retry once after 5s. If still failing, return error.

## Tool: draft_email

Create a Gmail draft (not sent).

**Input Schema**:

```json
{
  "type": "object",
  "properties": {
    "to": { "type": "string", "description": "Recipient email address" },
    "subject": { "type": "string", "description": "Email subject line" },
    "body": { "type": "string", "description": "Email body (plain text)" },
    "cc": { "type": "string", "description": "CC recipients (comma-separated)", "optional": true },
    "bcc": { "type": "string", "description": "BCC recipients (comma-separated)", "optional": true }
  },
  "required": ["to", "subject", "body"]
}
```

**Output Schema (success)**:

```json
{
  "success": true,
  "draftId": "draft-id-from-gmail",
  "messageId": "msg-id"
}
```

**Output Schema (error)**:

```json
{
  "success": false,
  "error": "Error description",
  "code": "AUTH_EXPIRED | RATE_LIMIT | DRAFT_FAILED"
}
```
