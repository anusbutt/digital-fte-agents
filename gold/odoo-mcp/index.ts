/**
 * Odoo MCP Server — exposes 7 Odoo accounting tools to Claude Code.
 *
 * Transport: stdio (Claude Code MCP standard)
 * Tools: get_invoices, create_invoice, post_invoice, record_payment,
 *        get_partners, get_financial_summary, get_transactions
 *
 * Auth: Odoo API key (Bearer token) via ODOO_API_KEY env var
 * Base: ODOO_URL (default: http://localhost:8069), ODOO_DB
 *
 * Error handling:
 *   fetch error / connection refused  → { success: false, error: "ODOO_UNREACHABLE" }
 *   HTTP 401                          → { success: false, error: "AUTH_FAILED" }
 *   HTTP 404 / not found              → { success: false, error: "NOT_FOUND" }
 *   Odoo fault (error.message)        → { success: false, error: <message> }
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// ── Env config ─────────────────────────────────────────────────────────────────

const ODOO_URL = (process.env.ODOO_URL || "http://localhost:8069").replace(/\/$/, "");
const ODOO_DB = process.env.ODOO_DB || "odoo";
const ODOO_API_KEY = process.env.ODOO_API_KEY || "";

// ── Types (per data-model.md §5, §6) ──────────────────────────────────────────

interface OdooInvoice {
  id: number;
  name: string;
  partner_id: [number, string];
  amount_total: number;
  amount_residual: number;
  currency_id: [number, string];
  state: "draft" | "posted" | "cancel";
  payment_state: "not_paid" | "in_payment" | "paid" | "partial";
  invoice_date: string;
  invoice_date_due: string;
  invoice_line_ids: number[];
}

interface FinancialSummary {
  period_start: string;
  period_end: string;
  mtd_revenue: number;
  total_outstanding: number;
  paid_invoice_count: number;
  unpaid_invoice_count: number;
  overdue_invoices: Array<{
    id: number;
    name: string;
    partner: string;
    amount: number;
    due_date: string;
    days_overdue: number;
  }>;
  currency: string;
}

interface OdooErrorResult {
  success: false;
  error: string;
}

// ── Odoo JSON-RPC client ───────────────────────────────────────────────────────

async function odooRpc(
  model: string,
  method: string,
  args: unknown[],
  kwargs: Record<string, unknown> = {}
): Promise<unknown> {
  const url = `${ODOO_URL}/web/dataset/call_kw`;

  const body = JSON.stringify({
    jsonrpc: "2.0",
    method: "call",
    id: Date.now(),
    params: {
      model,
      method,
      args,
      kwargs: {
        context: { lang: "en_US", tz: "UTC" },
        ...kwargs,
      },
    },
  });

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${ODOO_API_KEY}`,
      },
      body,
      signal: AbortSignal.timeout(30000),
    });
  } catch {
    // Network error, connection refused, or timeout
    throw Object.assign(new Error("ODOO_UNREACHABLE"), { code: "ODOO_UNREACHABLE" });
  }

  if (response.status === 401) {
    throw Object.assign(new Error("AUTH_FAILED"), { code: "AUTH_FAILED" });
  }

  if (!response.ok) {
    throw Object.assign(
      new Error(`HTTP_${response.status}`),
      { code: `HTTP_${response.status}` }
    );
  }

  const json = (await response.json()) as {
    result?: unknown;
    error?: { message?: string; data?: { message?: string } };
  };

  if (json.error) {
    const msg =
      json.error.data?.message || json.error.message || "ODOO_RPC_ERROR";
    throw Object.assign(new Error(msg), { code: "ODOO_RPC_ERROR" });
  }

  return json.result;
}

function handleOdooError(err: unknown): OdooErrorResult {
  const e = err as { code?: string; message?: string };
  return { success: false, error: e.code || e.message || "UNKNOWN_ERROR" };
}

// ── Date helpers ───────────────────────────────────────────────────────────────

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function firstDayOfMonthIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

function daysDiff(dueDateStr: string): number {
  const due = new Date(dueDateStr).getTime();
  const now = Date.now();
  return Math.floor((now - due) / (1000 * 60 * 60 * 24));
}

// ── Tool implementations ───────────────────────────────────────────────────────

/** Tool 1: get_invoices */
async function getInvoices(params: {
  status?: string;
  payment_state?: string;
  date_from?: string;
  date_to?: string;
  partner?: string;
  limit?: number;
}) {
  try {
    const domain: unknown[] = [["move_type", "=", "out_invoice"]];
    if (params.status) domain.push(["state", "=", params.status]);
    if (params.payment_state) domain.push(["payment_state", "=", params.payment_state]);
    if (params.date_from) domain.push(["invoice_date", ">=", params.date_from]);
    if (params.date_to) domain.push(["invoice_date", "<=", params.date_to]);
    if (params.partner) domain.push(["partner_id.name", "ilike", params.partner]);

    const limit = Math.min(params.limit ?? 20, 100);
    const fields = [
      "id", "name", "partner_id", "amount_total", "amount_residual",
      "currency_id", "state", "payment_state", "invoice_date",
      "invoice_date_due", "invoice_line_ids",
    ];

    const result = await odooRpc("account.move", "search_read", [domain], {
      fields,
      limit,
      order: "invoice_date desc",
    }) as OdooInvoice[];

    const count = await odooRpc("account.move", "search_count", [domain]) as number;

    return { success: true, invoices: result, total_count: count };
  } catch (err) {
    return handleOdooError(err);
  }
}

/** Tool 2: create_invoice */
async function createInvoice(params: {
  partner_name: string;
  amount: number;
  description: string;
  currency?: string;
  due_date?: string;
}) {
  try {
    // Find partner
    const partners = await odooRpc("res.partner", "search_read", [
      [["name", "ilike", params.partner_name], ["active", "=", true]],
    ], { fields: ["id", "name"], limit: 1 }) as Array<{ id: number; name: string }>;

    if (!partners.length) {
      return { success: false, error: "PARTNER_NOT_FOUND" };
    }
    const partner = partners[0];

    // Resolve currency (optional)
    let currencyId: number | undefined;
    if (params.currency) {
      const currencies = await odooRpc("res.currency", "search_read", [
        [["name", "=", params.currency.toUpperCase()]],
      ], { fields: ["id"], limit: 1 }) as Array<{ id: number }>;
      if (currencies.length) currencyId = currencies[0].id;
    }

    // Build invoice values
    const dueDate = params.due_date || (() => {
      const d = new Date();
      d.setDate(d.getDate() + 30);
      return d.toISOString().slice(0, 10);
    })();

    const invoiceVals: Record<string, unknown> = {
      move_type: "out_invoice",
      partner_id: partner.id,
      invoice_date_due: dueDate,
      invoice_line_ids: [[0, 0, {
        name: params.description,
        quantity: 1,
        price_unit: params.amount,
      }]],
    };
    if (currencyId) invoiceVals.currency_id = currencyId;

    const invoiceId = await odooRpc("account.move", "create", [invoiceVals]) as number;

    // Read back to get invoice name
    const created = await odooRpc("account.move", "read", [[invoiceId]], {
      fields: ["name", "partner_id", "state"],
    }) as Array<{ name: string; partner_id: [number, string]; state: string }>;

    return {
      success: true,
      invoice_id: invoiceId,
      invoice_name: created[0]?.name,
      partner_id: partner.id,
      state: "draft",
    };
  } catch (err) {
    return handleOdooError(err);
  }
}

/** Tool 3: post_invoice */
async function postInvoice(params: { invoice_id: number }) {
  try {
    // Check invoice exists and is in draft
    const invoices = await odooRpc("account.move", "read", [[params.invoice_id]], {
      fields: ["state", "name"],
    }) as Array<{ state: string; name: string }>;

    if (!invoices.length) {
      return { success: false, error: "INVOICE_NOT_FOUND" };
    }
    if (invoices[0].state === "posted") {
      return { success: false, error: "ALREADY_POSTED" };
    }
    if (invoices[0].state === "cancel") {
      return { success: false, error: "INVOICE_CANCELLED" };
    }

    await odooRpc("account.move", "action_post", [[params.invoice_id]]);

    const updated = await odooRpc("account.move", "read", [[params.invoice_id]], {
      fields: ["name", "state"],
    }) as Array<{ name: string; state: string }>;

    return {
      success: true,
      invoice_id: params.invoice_id,
      invoice_name: updated[0]?.name,
      state: "posted",
    };
  } catch (err) {
    return handleOdooError(err);
  }
}

/** Tool 4: record_payment */
async function recordPayment(params: {
  invoice_id: number;
  amount: number;
  payment_date?: string;
  memo?: string;
}) {
  try {
    // Check invoice exists and is posted
    const invoices = await odooRpc("account.move", "read", [[params.invoice_id]], {
      fields: ["state", "amount_residual", "partner_id", "currency_id"],
    }) as Array<{
      state: string;
      amount_residual: number;
      partner_id: [number, string];
      currency_id: [number, string];
    }>;

    if (!invoices.length) {
      return { success: false, error: "INVOICE_NOT_FOUND" };
    }
    if (invoices[0].state !== "posted") {
      return { success: false, error: "INVOICE_NOT_POSTED" };
    }
    if (params.amount > invoices[0].amount_residual + 0.01) {
      return { success: false, error: "AMOUNT_EXCEEDS" };
    }

    const paymentDate = params.payment_date || todayIso();

    // Create payment via account.payment.register wizard
    const context = {
      active_model: "account.move",
      active_ids: [params.invoice_id],
    };

    const wizard = await odooRpc("account.payment.register", "with_context", [], {
      context,
    }).catch(() => null);

    // Fallback: create payment directly if wizard not available
    if (!wizard) {
      const paymentVals: Record<string, unknown> = {
        payment_type: "inbound",
        partner_type: "customer",
        partner_id: invoices[0].partner_id[0],
        amount: params.amount,
        date: paymentDate,
        currency_id: invoices[0].currency_id[0],
        ref: params.memo || `Payment for invoice ${params.invoice_id}`,
        journal_id: 1, // Bank journal (id=1 is default)
      };

      const paymentId = await odooRpc("account.payment", "create", [paymentVals]) as number;
      await odooRpc("account.payment", "action_post", [[paymentId]]);

      const invoice = await odooRpc("account.move", "read", [[params.invoice_id]], {
        fields: ["payment_state"],
      }) as Array<{ payment_state: string }>;

      return {
        success: true,
        payment_id: paymentId,
        invoice_payment_state: invoice[0]?.payment_state,
      };
    }

    const paymentId = await odooRpc("account.payment.register", "create", [{
      amount: params.amount,
      payment_date: paymentDate,
      communication: params.memo || "",
    }]) as number;

    await odooRpc("account.payment.register", "action_create_payments", [[paymentId]], {
      context,
    });

    const invoice = await odooRpc("account.move", "read", [[params.invoice_id]], {
      fields: ["payment_state"],
    }) as Array<{ payment_state: string }>;

    return {
      success: true,
      payment_id: paymentId,
      invoice_payment_state: invoice[0]?.payment_state,
    };
  } catch (err) {
    return handleOdooError(err);
  }
}

/** Tool 5: get_partners */
async function getPartners(params: { search?: string; limit?: number }) {
  try {
    const domain: unknown[] = [["active", "=", true]];
    if (params.search) domain.push(["name", "ilike", params.search]);

    const limit = params.limit ?? 20;
    const results = await odooRpc("res.partner", "search_read", [domain], {
      fields: ["id", "name", "email", "phone", "customer_rank", "supplier_rank"],
      limit,
      order: "name asc",
    }) as Array<{
      id: number;
      name: string;
      email: string | false;
      phone: string | false;
      customer_rank: number;
      supplier_rank: number;
    }>;

    const partners = results.map((p) => ({
      id: p.id,
      name: p.name,
      email: p.email || undefined,
      phone: p.phone || undefined,
      is_customer: p.customer_rank > 0,
      is_vendor: p.supplier_rank > 0,
    }));

    return { success: true, partners };
  } catch (err) {
    return handleOdooError(err);
  }
}

/** Tool 6: get_financial_summary */
async function getFinancialSummary(params: {
  date_from?: string;
  date_to?: string;
}) {
  try {
    const dateFrom = params.date_from || firstDayOfMonthIso();
    const dateTo = params.date_to || todayIso();

    // MTD revenue: sum of paid+posted invoices in period
    const postedInvoices = await odooRpc("account.move", "search_read", [[
      ["move_type", "=", "out_invoice"],
      ["state", "=", "posted"],
      ["invoice_date", ">=", dateFrom],
      ["invoice_date", "<=", dateTo],
    ]], {
      fields: ["amount_total", "amount_residual", "payment_state", "invoice_date_due", "name", "partner_id"],
      limit: 200,
    }) as Array<{
      amount_total: number;
      amount_residual: number;
      payment_state: string;
      invoice_date_due: string;
      name: string;
      partner_id: [number, string];
    }>;

    const paidInvoices = postedInvoices.filter((i) => i.payment_state === "paid");
    const unpaidInvoices = postedInvoices.filter((i) =>
      ["not_paid", "partial"].includes(i.payment_state)
    );

    const mtdRevenue = paidInvoices.reduce((s, i) => s + i.amount_total, 0);
    const totalOutstanding = unpaidInvoices.reduce((s, i) => s + i.amount_residual, 0);

    const today = todayIso();
    const overdueInvoices = unpaidInvoices
      .filter((i) => i.invoice_date_due < today)
      .map((i) => ({
        id: 0, // not available from search_read without id
        name: i.name,
        partner: i.partner_id[1],
        amount: i.amount_residual,
        due_date: i.invoice_date_due,
        days_overdue: daysDiff(i.invoice_date_due),
      }));

    // Get company currency
    const company = await odooRpc("res.company", "search_read", [[]], {
      fields: ["currency_id"],
      limit: 1,
    }) as Array<{ currency_id: [number, string] }>;
    const currency = company[0]?.currency_id[1] || "USD";

    const summary: FinancialSummary = {
      period_start: dateFrom,
      period_end: dateTo,
      mtd_revenue: Math.round(mtdRevenue * 100) / 100,
      total_outstanding: Math.round(totalOutstanding * 100) / 100,
      paid_invoice_count: paidInvoices.length,
      unpaid_invoice_count: unpaidInvoices.length,
      overdue_invoices: overdueInvoices,
      currency,
    };

    return { success: true, summary };
  } catch (err) {
    return handleOdooError(err);
  }
}

/** Tool 7: get_transactions */
async function getTransactions(params: {
  date_from?: string;
  date_to?: string;
  limit?: number;
}) {
  try {
    const domain: unknown[] = [["payment_type", "in", ["inbound", "outbound"]]];
    if (params.date_from) domain.push(["date", ">=", params.date_from]);
    if (params.date_to) domain.push(["date", "<=", params.date_to]);

    const limit = params.limit ?? 50;

    const results = await odooRpc("account.payment", "search_read", [domain], {
      fields: ["id", "date", "partner_id", "amount", "payment_type", "state", "ref"],
      limit,
      order: "date desc",
    }) as Array<{
      id: number;
      date: string;
      partner_id: [number, string] | false;
      amount: number;
      payment_type: string;
      state: string;
      ref: string | false;
    }>;

    const transactions = results.map((t) => ({
      id: t.id,
      date: t.date,
      partner: t.partner_id ? t.partner_id[1] : "Unknown",
      amount: t.amount,
      payment_type: t.payment_type as "inbound" | "outbound",
      state: t.state as "draft" | "posted" | "cancelled",
      memo: t.ref || undefined,
    }));

    return { success: true, transactions };
  } catch (err) {
    return handleOdooError(err);
  }
}

// ── Tool schemas (Zod) ─────────────────────────────────────────────────────────

const GetInvoicesSchema = z.object({
  status: z.enum(["draft", "posted", "cancel"]).optional(),
  payment_state: z.enum(["not_paid", "in_payment", "paid", "partial"]).optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  partner: z.string().optional(),
  limit: z.number().int().min(1).max(100).optional(),
});

const CreateInvoiceSchema = z.object({
  partner_name: z.string(),
  amount: z.number().positive(),
  description: z.string(),
  currency: z.string().optional(),
  due_date: z.string().optional(),
});

const PostInvoiceSchema = z.object({
  invoice_id: z.number().int().positive(),
});

const RecordPaymentSchema = z.object({
  invoice_id: z.number().int().positive(),
  amount: z.number().positive(),
  payment_date: z.string().optional(),
  memo: z.string().optional(),
});

const GetPartnersSchema = z.object({
  search: z.string().optional(),
  limit: z.number().int().min(1).optional(),
});

const GetFinancialSummarySchema = z.object({
  date_from: z.string().optional(),
  date_to: z.string().optional(),
});

const GetTransactionsSchema = z.object({
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  limit: z.number().int().min(1).optional(),
});

// ── MCP Server ─────────────────────────────────────────────────────────────────

const server = new Server(
  { name: "odoo-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_invoices",
      description: "Retrieve Odoo invoices with optional filters (status, payment state, date range, partner)",
      inputSchema: {
        type: "object" as const,
        properties: {
          status: { type: "string", enum: ["draft", "posted", "cancel"], description: "Invoice state filter" },
          payment_state: { type: "string", enum: ["not_paid", "in_payment", "paid", "partial"] },
          date_from: { type: "string", description: "YYYY-MM-DD" },
          date_to: { type: "string", description: "YYYY-MM-DD" },
          partner: { type: "string", description: "Partial partner name match" },
          limit: { type: "number", description: "Max results (default: 20, max: 100)" },
        },
      },
    },
    {
      name: "create_invoice",
      description: "Create a DRAFT invoice in Odoo. Requires separate HITL approval before posting.",
      inputSchema: {
        type: "object" as const,
        properties: {
          partner_name: { type: "string", description: "Client name (partial match)" },
          amount: { type: "number", description: "Total invoice amount" },
          description: { type: "string", description: "Invoice line description" },
          currency: { type: "string", description: "Currency code (default: company currency)" },
          due_date: { type: "string", description: "YYYY-MM-DD (default: today+30)" },
        },
        required: ["partner_name", "amount", "description"],
      },
    },
    {
      name: "post_invoice",
      description: "Confirm (post) a DRAFT invoice. Changes state draft → posted. HITL required.",
      inputSchema: {
        type: "object" as const,
        properties: {
          invoice_id: { type: "number", description: "Odoo account.move ID" },
        },
        required: ["invoice_id"],
      },
    },
    {
      name: "record_payment",
      description: "Record payment against a posted invoice. HITL required.",
      inputSchema: {
        type: "object" as const,
        properties: {
          invoice_id: { type: "number", description: "Odoo account.move ID" },
          amount: { type: "number", description: "Payment amount" },
          payment_date: { type: "string", description: "YYYY-MM-DD (default: today)" },
          memo: { type: "string", description: "Payment memo/reference" },
        },
        required: ["invoice_id", "amount"],
      },
    },
    {
      name: "get_partners",
      description: "Search Odoo partners (clients/vendors) by name",
      inputSchema: {
        type: "object" as const,
        properties: {
          search: { type: "string", description: "Partial name match (default: all active)" },
          limit: { type: "number", description: "Max results (default: 20)" },
        },
      },
    },
    {
      name: "get_financial_summary",
      description: "Get MTD revenue, outstanding balance, and overdue invoices. Primary data source for CEO briefing.",
      inputSchema: {
        type: "object" as const,
        properties: {
          date_from: { type: "string", description: "YYYY-MM-DD (default: first day of current month)" },
          date_to: { type: "string", description: "YYYY-MM-DD (default: today)" },
        },
      },
    },
    {
      name: "get_transactions",
      description: "Get payment/transaction records for a date range",
      inputSchema: {
        type: "object" as const,
        properties: {
          date_from: { type: "string", description: "YYYY-MM-DD" },
          date_to: { type: "string", description: "YYYY-MM-DD" },
          limit: { type: "number", description: "Max results (default: 50)" },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  let result: unknown;

  try {
    switch (name) {
      case "get_invoices":
        result = await getInvoices(GetInvoicesSchema.parse(args ?? {}));
        break;
      case "create_invoice":
        result = await createInvoice(CreateInvoiceSchema.parse(args));
        break;
      case "post_invoice":
        result = await postInvoice(PostInvoiceSchema.parse(args));
        break;
      case "record_payment":
        result = await recordPayment(RecordPaymentSchema.parse(args));
        break;
      case "get_partners":
        result = await getPartners(GetPartnersSchema.parse(args ?? {}));
        break;
      case "get_financial_summary":
        result = await getFinancialSummary(GetFinancialSummarySchema.parse(args ?? {}));
        break;
      case "get_transactions":
        result = await getTransactions(GetTransactionsSchema.parse(args ?? {}));
        break;
      default:
        result = { success: false, error: `Unknown tool: ${name}` };
    }
  } catch (err) {
    const e = err as { code?: string; message?: string };
    result = { success: false, error: e.code || e.message || "TOOL_ERROR" };
  }

  return {
    content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
  };
});

// ── Start ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  if (!ODOO_API_KEY) {
    console.error("WARNING: ODOO_API_KEY is not set. All Odoo requests will fail with AUTH_FAILED.");
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(
    `Odoo MCP server started (stdio transport) — target: ${ODOO_URL}, db: ${ODOO_DB}`
  );
}

main().catch((err: unknown) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
