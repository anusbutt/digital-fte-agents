/**
 * Email MCP Server — sends and drafts emails via Gmail API.
 *
 * Transport: stdio
 * Tools: send_email, draft_email
 * Auth: OAuth2 via googleapis
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google, type gmail_v1 } from "googleapis";
import fs from "fs";
import path from "path";

// --- Types ---

interface EmailParams {
  to: string;
  subject: string;
  body: string;
  cc?: string;
  bcc?: string;
  in_reply_to?: string;
  thread_id?: string;
}

interface EmailResult {
  success: boolean;
  messageId?: string | null;
  threadId?: string | null;
  draftId?: string | null;
  error?: string;
  code?: string;
}

interface OAuthCredentials {
  client_id: string;
  client_secret: string;
  redirect_uris?: string[];
}

// --- OAuth2 Setup ---

const SCOPES: string[] = [
  "https://www.googleapis.com/auth/gmail.send",
  "https://www.googleapis.com/auth/gmail.compose",
];

function getCredentialsPath(): string {
  return (
    process.env.GOOGLE_CREDENTIALS_PATH ||
    path.join(process.cwd(), "credentials.json")
  );
}

function getTokenPath(): string {
  return (
    process.env.EMAIL_MCP_TOKEN_PATH ||
    path.join(process.cwd(), "token-mcp.json")
  );
}

function loadCredentials(): OAuthCredentials {
  const credPath = getCredentialsPath();
  if (!fs.existsSync(credPath)) {
    throw new Error(
      `Credentials file not found: ${credPath}. Download from Google Cloud Console.`
    );
  }
  const content = JSON.parse(fs.readFileSync(credPath, "utf-8"));
  return content.installed || content.web;
}

function createOAuth2Client() {
  const creds = loadCredentials();
  const oauth2Client = new google.auth.OAuth2(
    creds.client_id,
    creds.client_secret,
    creds.redirect_uris?.[0] || "http://localhost"
  );

  const tokenPath = getTokenPath();
  if (fs.existsSync(tokenPath)) {
    const token = JSON.parse(fs.readFileSync(tokenPath, "utf-8"));
    oauth2Client.setCredentials(token);
  } else {
    throw new Error(
      `Token file not found: ${tokenPath}. Run Gmail watcher --auth first to generate tokens.`
    );
  }

  // Auto-refresh token on expiry
  oauth2Client.on("tokens", (tokens) => {
    const existing = fs.existsSync(tokenPath)
      ? JSON.parse(fs.readFileSync(tokenPath, "utf-8"))
      : {};
    const updated = { ...existing, ...tokens };
    fs.writeFileSync(tokenPath, JSON.stringify(updated, null, 2));
  });

  return oauth2Client;
}

// --- Email Helpers ---

function buildRawEmail({ to, subject, body, cc, bcc, in_reply_to }: EmailParams): string {
  const lines: string[] = [];
  lines.push(`To: ${to}`);
  if (cc) lines.push(`Cc: ${cc}`);
  if (bcc) lines.push(`Bcc: ${bcc}`);
  lines.push(`Subject: ${subject}`);
  lines.push("Content-Type: text/plain; charset=utf-8");
  if (in_reply_to) lines.push(`In-Reply-To: ${in_reply_to}`);
  lines.push("");
  lines.push(body);

  const raw = lines.join("\r\n");
  return Buffer.from(raw).toString("base64url");
}

async function sendEmail(gmail: gmail_v1.Gmail, params: EmailParams): Promise<EmailResult> {
  const { to, subject, body, cc, bcc, in_reply_to, thread_id } = params;

  const raw = buildRawEmail({ to, subject, body, cc, bcc, in_reply_to });

  const requestBody: { raw: string; threadId?: string } = { raw };
  if (thread_id) requestBody.threadId = thread_id;

  try {
    const res = await gmail.users.messages.send({
      userId: "me",
      requestBody,
    });
    return {
      success: true,
      messageId: res.data.id,
      threadId: res.data.threadId,
    };
  } catch (err: unknown) {
    return handleGmailError(err, "SEND_FAILED");
  }
}

async function draftEmail(gmail: gmail_v1.Gmail, params: EmailParams): Promise<EmailResult> {
  const { to, subject, body, cc, bcc } = params;

  const raw = buildRawEmail({ to, subject, body, cc, bcc });

  try {
    const res = await gmail.users.drafts.create({
      userId: "me",
      requestBody: {
        message: { raw },
      },
    });
    return {
      success: true,
      draftId: res.data.id,
      messageId: res.data.message?.id || null,
    };
  } catch (err: unknown) {
    return handleGmailError(err, "DRAFT_FAILED");
  }
}

function handleGmailError(err: unknown, defaultCode: string): EmailResult {
  const error = err as { response?: { status?: number }; code?: number; message?: string };
  const status = error.response?.status || error.code;

  if (status === 401) {
    return {
      success: false,
      error: "OAuth2 token expired or invalid",
      code: "AUTH_EXPIRED",
    };
  }
  if (status === 429) {
    return {
      success: false,
      error: "Gmail API rate limit exceeded",
      code: "RATE_LIMIT",
    };
  }
  if (status === 400 && error.message?.includes("recipient")) {
    return {
      success: false,
      error: `Invalid recipient: ${error.message}`,
      code: "INVALID_RECIPIENT",
    };
  }
  return {
    success: false,
    error: error.message || String(err),
    code: defaultCode,
  };
}

// --- MCP Server ---

const server = new Server(
  { name: "email-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "send_email",
      description: "Send an email via Gmail API",
      inputSchema: {
        type: "object" as const,
        properties: {
          to: { type: "string", description: "Recipient email address" },
          subject: { type: "string", description: "Email subject line" },
          body: { type: "string", description: "Email body (plain text)" },
          cc: {
            type: "string",
            description: "CC recipients (comma-separated)",
          },
          bcc: {
            type: "string",
            description: "BCC recipients (comma-separated)",
          },
          in_reply_to: {
            type: "string",
            description: "Message-ID to reply to",
          },
          thread_id: {
            type: "string",
            description: "Gmail thread ID for threading",
          },
        },
        required: ["to", "subject", "body"],
      },
    },
    {
      name: "draft_email",
      description:
        "Create a Gmail draft (not sent) for human review before sending",
      inputSchema: {
        type: "object" as const,
        properties: {
          to: { type: "string", description: "Recipient email address" },
          subject: { type: "string", description: "Email subject line" },
          body: { type: "string", description: "Email body (plain text)" },
          cc: {
            type: "string",
            description: "CC recipients (comma-separated)",
          },
          bcc: {
            type: "string",
            description: "BCC recipients (comma-separated)",
          },
        },
        required: ["to", "subject", "body"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  let auth;
  try {
    auth = createOAuth2Client();
  } catch (err: unknown) {
    const error = err as Error;
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({
            success: false,
            error: error.message,
            code: "AUTH_EXPIRED",
          }),
        },
      ],
    };
  }

  const gmail = google.gmail({ version: "v1", auth });

  let result: EmailResult;
  if (name === "send_email") {
    result = await sendEmail(gmail, args as unknown as EmailParams);

    // Retry once on 5xx
    if (!result.success && result.code === "SEND_FAILED") {
      await new Promise((r) => setTimeout(r, 5000));
      result = await sendEmail(gmail, args as unknown as EmailParams);
    }
  } else if (name === "draft_email") {
    result = await draftEmail(gmail, args as unknown as EmailParams);
  } else {
    result = { success: false, error: `Unknown tool: ${name}`, code: "UNKNOWN" };
  }

  return {
    content: [{ type: "text" as const, text: JSON.stringify(result) }],
  };
});

// Start server
async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Email MCP server started (stdio transport)");
}

main().catch((err: unknown) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
