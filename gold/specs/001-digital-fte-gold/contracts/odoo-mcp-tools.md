# Contract: odoo-mcp Tool Definitions

**MCP Server**: `odoo-mcp/index.ts`
**Transport**: stdio (Claude Code MCP standard)
**Base URL**: `http://localhost:8069` (configurable via `ODOO_URL` env var)

---

## Tool 1: get_invoices

**Purpose**: Retrieve list of invoices from Odoo with optional filters.

**Input schema**:
```typescript
{
  status?: "draft" | "posted" | "cancel",   // default: all
  payment_state?: "not_paid" | "in_payment" | "paid" | "partial",
  date_from?: string,   // YYYY-MM-DD
  date_to?: string,     // YYYY-MM-DD
  partner?: string,     // partial name match
  limit?: number        // default: 20, max: 100
}
```

**Output schema**:
```typescript
{
  success: boolean,
  invoices: OdooInvoice[],
  total_count: number,
  error?: string
}
```

**Error codes**: `ODOO_UNREACHABLE`, `AUTH_FAILED`, `INVALID_PARAMS`

---

## Tool 2: create_invoice

**Purpose**: Create a draft invoice in Odoo. HITL required before posting.

**Input schema**:
```typescript
{
  partner_name: string,       // exact or partial match against res.partner
  amount: number,             // total invoice amount
  description: string,        // invoice line description
  currency?: string,          // default: company currency (USD)
  due_date?: string           // YYYY-MM-DD, default: today + 30 days
}
```

**Output schema**:
```typescript
{
  success: boolean,
  invoice_id?: number,
  invoice_name?: string,      // e.g. "INV/2026/001"
  partner_id?: number,
  state: "draft",
  error?: string
}
```

**Error codes**: `PARTNER_NOT_FOUND`, `ODOO_UNREACHABLE`, `AUTH_FAILED`,
`CREATE_FAILED`

**Note**: Always creates in `draft` state. `post_invoice` tool required to
confirm. Both steps require separate HITL approval per constitution Principle IV.

---

## Tool 3: post_invoice

**Purpose**: Confirm (post) a draft invoice. Changes state draft → posted.
HITL required.

**Input schema**:
```typescript
{
  invoice_id: number    // Odoo account.move ID
}
```

**Output schema**:
```typescript
{
  success: boolean,
  invoice_id: number,
  invoice_name?: string,
  state?: "posted",
  error?: string
}
```

**Error codes**: `INVOICE_NOT_FOUND`, `ALREADY_POSTED`, `ODOO_UNREACHABLE`,
`AUTH_FAILED`

---

## Tool 4: record_payment

**Purpose**: Record payment against a posted invoice. HITL required.

**Input schema**:
```typescript
{
  invoice_id: number,
  amount: number,
  payment_date?: string,   // YYYY-MM-DD, default: today
  memo?: string
}
```

**Output schema**:
```typescript
{
  success: boolean,
  payment_id?: number,
  invoice_payment_state?: "paid" | "partial",
  error?: string
}
```

**Error codes**: `INVOICE_NOT_FOUND`, `INVOICE_NOT_POSTED`, `AMOUNT_EXCEEDS`,
`ODOO_UNREACHABLE`, `AUTH_FAILED`

---

## Tool 5: get_partners

**Purpose**: Search Odoo partners (clients/vendors) by name.

**Input schema**:
```typescript
{
  search?: string,    // partial name match, default: all active
  limit?: number      // default: 20
}
```

**Output schema**:
```typescript
{
  success: boolean,
  partners: Array<{
    id: number,
    name: string,
    email?: string,
    phone?: string,
    is_customer: boolean,
    is_vendor: boolean
  }>,
  error?: string
}
```

**Error codes**: `ODOO_UNREACHABLE`, `AUTH_FAILED`

---

## Tool 6: get_financial_summary

**Purpose**: Get MTD revenue, outstanding balance, and overdue invoices.
Primary data source for CEO briefing.

**Input schema**:
```typescript
{
  date_from?: string,   // YYYY-MM-DD, default: first day of current month
  date_to?: string      // YYYY-MM-DD, default: today
}
```

**Output schema**:
```typescript
{
  success: boolean,
  summary?: FinancialSummary,
  error?: string
}
```

*(FinancialSummary schema defined in data-model.md §6)*

**Error codes**: `ODOO_UNREACHABLE`, `AUTH_FAILED`

---

## Tool 7: get_transactions

**Purpose**: Get payment/transaction records for the period.

**Input schema**:
```typescript
{
  date_from?: string,   // YYYY-MM-DD
  date_to?: string,     // YYYY-MM-DD
  limit?: number        // default: 50
}
```

**Output schema**:
```typescript
{
  success: boolean,
  transactions: Array<{
    id: number,
    date: string,
    partner: string,
    amount: number,
    payment_type: "inbound" | "outbound",
    state: "draft" | "posted" | "cancelled",
    memo?: string
  }>,
  error?: string
}
```

**Error codes**: `ODOO_UNREACHABLE`, `AUTH_FAILED`
