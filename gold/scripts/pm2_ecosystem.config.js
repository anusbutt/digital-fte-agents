/**
 * PM2 Ecosystem Config — Digital FTE Gold
 *
 * Gold tier runs 8 long-running processes (Silver's 5 + 3 social-media watchers).
 *
 * Usage:
 *   pm2 start scripts/pm2_ecosystem.config.js   # start all 8 processes
 *   pm2 save                                     # persist process list across reboots
 *   pm2 startup                                  # install PM2 as Windows service
 *   pm2 list                                     # view status table
 *   pm2 logs                                     # tail all logs
 *   pm2 restart all                              # rolling restart
 *
 * Process list:
 *   1. filesystem-watcher  — watches vault/Inbox/ for dropped files
 *   2. gmail-watcher       — polls Gmail for business emails
 *   3. whatsapp-watcher    — polls WhatsApp Web for keyword DMs
 *   4. facebook-watcher    — polls Facebook Messenger for keyword DMs (Playwright)
 *   5. instagram-watcher   — polls Instagram DMs for keyword messages (Playwright)
 *   6. twitter-watcher     — monitors Twitter mentions + DMs (Playwright)
 *   7. orchestrator        — watches Needs_Action/, Approved/, Rejected/; calls Claude skills
 *   8. email-mcp           — stdio MCP server for Gmail send/draft (Node.js/TypeScript)
 *
 * Note: odoo-mcp is NOT a PM2 process — it runs on-demand as a Claude MCP subprocess.
 *
 * Environment: all sensitive vars are loaded from .env at repo root.
 * Each Python process runs with `cwd: repoRoot` so imports resolve correctly.
 */

const path = require("path");
const repoRoot = path.resolve(__dirname, "..");

module.exports = {
  apps: [
    // ── 1. Filesystem Watcher ─────────────────────────────────────────────────
    {
      name: "filesystem-watcher",
      script: "python",
      args: "main.py files",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-filesystem-watcher-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-filesystem-watcher-out.log"),
      merge_logs: true,
    },

    // ── 2. Gmail Watcher ──────────────────────────────────────────────────────
    {
      name: "gmail-watcher",
      script: "python",
      args: "main.py email",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-gmail-watcher-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-gmail-watcher-out.log"),
      merge_logs: true,
    },

    // ── 3. WhatsApp Watcher ───────────────────────────────────────────────────
    {
      name: "whatsapp-watcher",
      script: "python",
      args: "main.py whatsapp",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-whatsapp-watcher-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-whatsapp-watcher-out.log"),
      merge_logs: true,
    },

    // ── 4. Facebook Watcher (Gold) ────────────────────────────────────────────
    {
      name: "facebook-watcher",
      script: "python",
      args: "main.py facebook",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
        FACEBOOK_USER_DATA_DIR: process.env.FACEBOOK_USER_DATA_DIR ||
          path.join(repoRoot, "playwright-data", "facebook"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-facebook-watcher-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-facebook-watcher-out.log"),
      merge_logs: true,
    },

    // ── 5. Instagram Watcher (Gold) ───────────────────────────────────────────
    {
      name: "instagram-watcher",
      script: "python",
      args: "main.py instagram",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
        INSTAGRAM_USER_DATA_DIR: process.env.INSTAGRAM_USER_DATA_DIR ||
          path.join(repoRoot, "playwright-data", "instagram"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-instagram-watcher-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-instagram-watcher-out.log"),
      merge_logs: true,
    },

    // ── 6. Twitter Watcher (Gold) ─────────────────────────────────────────────
    {
      name: "twitter-watcher",
      script: "python",
      args: "main.py twitter",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
        TWITTER_USER_DATA_DIR: process.env.TWITTER_USER_DATA_DIR ||
          path.join(repoRoot, "playwright-data", "twitter"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-twitter-watcher-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-twitter-watcher-out.log"),
      merge_logs: true,
    },

    // ── 7. Orchestrator ───────────────────────────────────────────────────────
    {
      name: "orchestrator",
      script: "python",
      args: "main.py orchestrator",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        DRY_RUN: process.env.DRY_RUN || "false",
        VAULT_PATH: process.env.VAULT_PATH || path.join(repoRoot, "vault"),
        RALPH_MAX_ITER: process.env.RALPH_MAX_ITER || "10",
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-orchestrator-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-orchestrator-out.log"),
      merge_logs: true,
    },

    // ── 8. Email MCP Server (Node.js/TypeScript) ──────────────────────────────
    {
      name: "email-mcp",
      script: "npx",
      args: "tsx email-mcp/index.ts",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        GOOGLE_CREDENTIALS_PATH: process.env.GOOGLE_CREDENTIALS_PATH ||
          path.join(repoRoot, "credentials.json"),
        EMAIL_MCP_TOKEN_PATH: process.env.EMAIL_MCP_TOKEN_PATH ||
          path.join(repoRoot, "token-mcp.json"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-email-mcp-error.log"),
      out_file:   path.join(repoRoot, "vault", "Logs", "pm2-email-mcp-out.log"),
      merge_logs: true,
    },
  ],
};
