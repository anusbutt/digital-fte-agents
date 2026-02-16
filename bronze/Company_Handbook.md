# Company Handbook

> This document defines the rules of engagement for the AI Employee.
> All AI actions MUST consult this handbook before making decisions.

## Business Profile

- **Business Type**: Freelance Software Development & Consulting
- **Owner**: Solo Operator
- **Tier**: Bronze (Local-first, file-based operations)

## File Classification Rules

| Keyword / Pattern | Classification | Priority |
|-------------------|---------------|----------|
| `invoice`, `inv_`, `bill` | invoice | high |
| `receipt`, `rcpt_`, `payment_confirmation` | receipt | medium |
| `brief`, `client_brief`, `project_brief` | client_brief | high |
| `contract`, `agreement`, `nda`, `sow` | contract | high |
| Everything else | unknown | low |

## Approval Thresholds

> Actions exceeding these thresholds REQUIRE human approval before execution.

| Action Type | Threshold | Approval Required |
|-------------|-----------|-------------------|
| Invoice payment | > $500 | Yes |
| Any external email | Always | Yes |
| Social media post | Always | Yes |
| File deletion | Always | Yes |
| External API call | Always | Yes |
| Invoice payment | <= $500 | No (log only) |
| Internal file move | Never | No |
| Dashboard update | Never | No |
| Log entry creation | Never | No |

## Communication Tone

- **Client-facing**: Professional, concise, warm
- **Internal notes**: Direct, action-oriented
- **Briefings**: Executive summary style, data-driven
- **Plans**: Clear steps with checkboxes, no jargon

## Client Priority Tiers

| Tier | Criteria | Response Time | Priority |
|------|----------|---------------|----------|
| Tier 1 | Active retainer clients | Same day | high |
| Tier 2 | Project-based clients | 2 business days | medium |
| Tier 3 | One-time / new inquiries | 5 business days | low |

## General Rules

1. **Never auto-execute** sensitive actions. Always create an approval request.
2. **Always log** every action taken, including skipped duplicates.
3. **When uncertain**, classify as `unknown` and set priority to `low`.
4. **Preserve original files** -- never modify or delete files in /Inbox.
5. **DRY_RUN mode** must be respected. When active, log intentions but take no real action.
