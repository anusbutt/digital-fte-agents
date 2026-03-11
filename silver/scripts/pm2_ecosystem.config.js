/**
 * PM2 Ecosystem Config — Digital FTE Silver
 *
 * AD-7: PM2 manages all 5 long-running processes with auto-restart.
 *
 * Usage:
 *   pm2 start scripts/pm2_ecosystem.config.js
 *   pm2 save                          # persist process list
 *   pm2 startup                       # install PM2 as Windows service
 *   pm2 list                          # view status
 *   pm2 logs                          # tail all logs
 *
 * Environment: all sensitive vars loaded from .env at repo root.
 * Each process inherits the repo root as cwd.
 */

const path = require("path");
const repoRoot = path.resolve(__dirname, "..");

module.exports = {
  apps: [
    // ── 1. Filesystem Watcher ───────────────────────────────────────────────
    {
      name: "filesystem-watcher",
      script: "python",
      args: "-m watchers.filesystem_watcher",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-filesystem-watcher-error.log"),
      out_file: path.join(repoRoot, "vault", "Logs", "pm2-filesystem-watcher-out.log"),
      merge_logs: true,
    },

    // ── 2. Gmail Watcher ────────────────────────────────────────────────────
    {
      name: "gmail-watcher",
      script: "python",
      args: "-m watchers.gmail_watcher",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-gmail-watcher-error.log"),
      out_file: path.join(repoRoot, "vault", "Logs", "pm2-gmail-watcher-out.log"),
      merge_logs: true,
    },

    // ── 3. WhatsApp Watcher ─────────────────────────────────────────────────
    {
      name: "whatsapp-watcher",
      script: "python",
      args: "-m watchers.whatsapp_watcher",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
        // WhatsApp Playwright needs a display; on Windows this is the default session
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-whatsapp-watcher-error.log"),
      out_file: path.join(repoRoot, "vault", "Logs", "pm2-whatsapp-watcher-out.log"),
      merge_logs: true,
    },

    // ── 4. Orchestrator ─────────────────────────────────────────────────────
    {
      name: "orchestrator",
      script: "python",
      args: "-m watchers.orchestrator",
      cwd: repoRoot,
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-orchestrator-error.log"),
      out_file: path.join(repoRoot, "vault", "Logs", "pm2-orchestrator-out.log"),
      merge_logs: true,
    },

    // ── 5. Email MCP Server (Node.js/TypeScript) ────────────────────────────
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
        GOOGLE_CREDENTIALS_PATH: path.join(repoRoot, "credentials.json"),
        EMAIL_MCP_TOKEN_PATH: path.join(repoRoot, "token-mcp.json"),
      },
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      error_file: path.join(repoRoot, "vault", "Logs", "pm2-email-mcp-error.log"),
      out_file: path.join(repoRoot, "vault", "Logs", "pm2-email-mcp-out.log"),
      merge_logs: true,
    },
  ],
};
