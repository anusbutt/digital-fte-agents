"""Gmail watcher: polls Gmail API for actionable unread emails.

Extends BaseWatcher to monitor Gmail inbox via OAuth2, filter out
noise (OTPs, newsletters, promotions), classify sensitivity/priority,
and create EMAIL_ VaultItems in vault/Needs_Action/.
"""

import argparse
import base64
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from watchers.base_watcher import BaseWatcher
from watchers.logger import append_log_entry

logger = logging.getLogger(__name__)

# Gmail API scopes — readonly + modify (to mark as read)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Gmail query to filter inbox: unread, skip categories
GMAIL_QUERY = "is:unread -category:{promotions,social,updates,forums}"

# Patterns to skip (noise emails)
SKIP_SENDERS = re.compile(
    r"(noreply@|no-reply@|notifications@|mailer-daemon@|postmaster@)",
    re.IGNORECASE,
)
SKIP_SUBJECTS = re.compile(
    r"(OTP|verification code|verify your|confirm your email|password reset|"
    r"two-factor|2fa|sign-in attempt|login alert)",
    re.IGNORECASE,
)

# Sensitivity classification
FINANCIAL_KEYWORDS = re.compile(
    r"(invoice|payment|amount|\$\d|refund|billing|receipt|transfer|wire|remittance)",
    re.IGNORECASE,
)
URGENCY_KEYWORDS = re.compile(
    r"(urgent|asap|deadline|immediately|time-sensitive|critical|priority)",
    re.IGNORECASE,
)


def _authenticate(credentials_path: str, token_path: str, interactive: bool = False) -> Credentials:
    """Load or create OAuth2 credentials for Gmail API.

    Args:
        credentials_path: Path to Google Cloud OAuth2 credentials JSON.
        token_path: Path to store/load the token JSON.
        interactive: If True, open browser for consent flow.

    Returns:
        Valid Credentials object.
    """
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            logger.info("Gmail token refreshed successfully")
            return creds
        except Exception:
            logger.warning("Token refresh failed, need re-authentication")
            creds = None

    if not interactive:
        raise RuntimeError(
            f"Gmail token not found or expired at {token_path}. "
            "Run with --auth flag to authenticate interactively."
        )

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_path}. "
            "Download from Google Cloud Console."
        )

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(token_path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    logger.info("Gmail authentication successful, token saved to %s", token_path)

    return creds


def _classify_sensitivity(msg: dict) -> str:
    """Classify email sensitivity based on sender, content, attachments.

    Returns 'sensitive' or 'non-sensitive'.
    """
    # Financial content → sensitive
    subject = msg.get("subject", "")
    body = msg.get("body", "")
    if FINANCIAL_KEYWORDS.search(subject) or FINANCIAL_KEYWORDS.search(body):
        return "sensitive"

    # Attachments → sensitive
    if msg.get("has_attachments", False):
        return "sensitive"

    # Default: sensitive for safety (per handbook: when uncertain, require approval)
    return "sensitive"


def _classify_priority(msg: dict) -> str:
    """Classify email priority based on content keywords.

    Returns 'high', 'medium', or 'low'.
    """
    subject = msg.get("subject", "")
    body = msg.get("body", "")

    # Urgency keywords → high
    if URGENCY_KEYWORDS.search(subject) or URGENCY_KEYWORDS.search(body):
        return "high"

    # Financial keywords → high
    if FINANCIAL_KEYWORDS.search(subject) or FINANCIAL_KEYWORDS.search(body):
        return "high"

    # Default
    return "medium"


class GmailWatcher(BaseWatcher):
    """Watches Gmail inbox for actionable unread emails.

    Polls Gmail API at configured intervals, filters noise,
    creates EMAIL_ VaultItems in vault/Needs_Action/.
    """

    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 60,
        credentials_path: str = "./credentials.json",
        token_path: str = "./token.json",
    ):
        super().__init__(vault_path, check_interval)

        self.credentials_path = credentials_path
        self.token_path = token_path
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.log_dir = self.vault_path / "Logs"

        self.needs_action_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        self._gmail = None
        self._processed_ids: set[str] = set()
        self._session_valid = True       # set False on 401/403; pause until re-authed
        self._auth_alert_written = False  # idempotent SYSTEM_ file guard

        # Load already-processed message IDs from existing vault files
        self._load_processed_ids()

    def _load_processed_ids(self) -> None:
        """Scan vault/Needs_Action/ for existing EMAIL_ files to avoid duplicates."""
        for f in self.needs_action_dir.iterdir():
            if f.is_file() and f.name.startswith("EMAIL_") and f.name.endswith(".md"):
                # Extract message_id from filename: EMAIL_{message_id}.md
                msg_id = f.stem.replace("EMAIL_", "", 1)
                self._processed_ids.add(msg_id)

        if self._processed_ids:
            logger.info("Loaded %d previously processed email IDs", len(self._processed_ids))

    def _write_auth_failure_alert(self, error_code: str = "UNKNOWN") -> None:
        """Write SYSTEM_AUTH_FAILURE_GMAIL_{timestamp}.md to Needs_Action/.

        Idempotent — writes only once per watcher session.
        """
        if self._auth_alert_written:
            return

        # Check for existing alert file
        existing = list(self.needs_action_dir.glob("SYSTEM_AUTH_FAILURE_GMAIL_*.md"))
        if existing:
            self._auth_alert_written = True
            return

        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        iso = now.isoformat()
        filename = f"SYSTEM_AUTH_FAILURE_GMAIL_{ts}.md"

        content = f"""---
type: system
priority: high
status: pending
detected_date: {iso}
error_code: {error_code}
---

## Gmail Authentication Failure

The Gmail watcher received a `{error_code}` error from the Gmail API.
The watcher has paused and will not poll until re-authenticated.

## Resolution Steps

1. Re-run Gmail authentication:
   ```
   python main.py setup gmail
   ```
   Or from the Gmail watcher directly:
   ```
   python -m watchers.gmail_watcher --auth
   ```
2. After successful authentication, move this file to `vault/Done/` to clear the alert.
3. Restart the Gmail watcher: `python main.py email`

*Alert generated: {iso}*
"""

        target = self.needs_action_dir / filename
        try:
            import tempfile as _tempfile
            with _tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8",
                dir=self.needs_action_dir, suffix=".tmp", delete=False,
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            tmp_path.rename(target)
            self._auth_alert_written = True
            logger.warning("Wrote Gmail auth failure alert: %s", filename)
        except Exception:
            logger.exception("Failed to write Gmail auth failure alert")

    def _ensure_gmail_client(self) -> None:
        """Initialize Gmail API client if not already done."""
        if self._gmail is not None:
            return

        creds = _authenticate(self.credentials_path, self.token_path, interactive=False)
        self._gmail = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API client initialized")

    def _get_message_detail(self, message_id: str) -> dict | None:
        """Fetch full message details from Gmail API.

        Returns a dict with: id, from, from_name, to, subject, snippet,
        body, received_date, labels, has_attachments, thread_id.
        Returns None if message should be skipped.
        """
        try:
            msg = self._gmail.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()
        except Exception:
            logger.exception("Failed to fetch message %s", message_id)
            return None

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

        from_header = headers.get("from", "")
        to_header = headers.get("to", "")
        subject = headers.get("subject", "(no subject)")

        # Skip noise senders
        if SKIP_SENDERS.search(from_header):
            logger.debug("Skipping noise sender: %s", from_header)
            return None

        # Skip noise subjects
        if SKIP_SUBJECTS.search(subject):
            logger.debug("Skipping noise subject: %s", subject)
            return None

        # Parse sender name and email
        from_name = from_header
        from_email = from_header
        match = re.match(r"^(.+?)\s*<(.+?)>$", from_header)
        if match:
            from_name = match.group(1).strip().strip('"')
            from_email = match.group(2).strip()

        # Extract body text
        body = _extract_body(msg.get("payload", {}))

        # Check for attachments
        has_attachments = _has_attachments(msg.get("payload", {}))

        # Get labels
        labels = msg.get("labelIds", [])

        # Parse received date
        try:
            internal_date_ms = int(msg.get("internalDate", "0"))
            received_date = datetime.fromtimestamp(
                internal_date_ms / 1000, tz=timezone.utc
            ).isoformat()
        except (ValueError, OSError):
            received_date = datetime.now(timezone.utc).isoformat()

        return {
            "id": message_id,
            "from": from_email,
            "from_name": from_name,
            "to": to_header,
            "subject": subject,
            "snippet": msg.get("snippet", "")[:200],
            "body": body,
            "received_date": received_date,
            "labels": labels,
            "has_attachments": has_attachments,
            "thread_id": msg.get("threadId", ""),
        }

    def check_for_updates(self) -> list[dict]:
        """Query Gmail API for unread actionable messages.

        Filters out promotions, social, OTPs, newsletters.
        Returns list of message dicts ready for create_action_file().
        """
        if not self._session_valid:
            logger.warning("Gmail session invalid — skipping poll (run: python main.py setup gmail)")
            return []

        try:
            self._ensure_gmail_client()
        except RuntimeError as exc:
            # Token expired or missing — treat as auth failure
            logger.error("Gmail auth error during client init: %s", exc)
            self._session_valid = False
            self._write_auth_failure_alert("TOKEN_EXPIRED")
            append_log_entry(
                log_dir=self.log_dir,
                action_type="auth_failure",
                actor="gmail_watcher",
                target="gmail_session",
                parameters={"event": "token_expired", "error": str(exc)[:200]},
                result="failure",
            )
            return []

        try:
            results = self._gmail.users().messages().list(
                userId="me", q=GMAIL_QUERY, maxResults=20
            ).execute()
        except HttpError as exc:
            status = exc.resp.status if exc.resp else 0
            if status in (401, 403):
                logger.error("Gmail API returned %d — session expired or unauthorized", status)
                self._session_valid = False
                self._gmail = None  # Force re-init on next valid session
                self._write_auth_failure_alert(f"HTTP_{status}")
                append_log_entry(
                    log_dir=self.log_dir,
                    action_type="auth_failure",
                    actor="gmail_watcher",
                    target="gmail_session",
                    parameters={"event": "api_auth_error", "status": status},
                    result="failure",
                )
                return []
            logger.exception("Gmail API query failed (HTTP %d)", status)
            raise  # Let BaseWatcher handle backoff for transient errors
        except Exception:
            logger.exception("Gmail API query failed")
            raise  # Let BaseWatcher handle backoff

        messages = results.get("messages", [])
        if not messages:
            return []

        actionable = []
        for msg_ref in messages:
            msg_id = msg_ref["id"]

            # Skip already-processed
            if msg_id in self._processed_ids:
                continue

            # Fetch full details
            detail = self._get_message_detail(msg_id)
            if detail is not None:
                actionable.append(detail)

        if actionable:
            logger.info("Found %d actionable email(s)", len(actionable))

        return actionable

    def create_action_file(self, source: dict) -> Path | None:
        """Create EMAIL_ VaultItem in vault/Needs_Action/.

        Args:
            source: Message dict from check_for_updates().

        Returns:
            Path to the created .md file, or None if duplicate.
        """
        msg_id = source["id"]

        # Duplicate detection
        if msg_id in self._processed_ids:
            logger.debug("Duplicate email skipped: %s", msg_id)
            return None

        # Classify
        sensitivity = _classify_sensitivity(source)
        priority = _classify_priority(source)

        # Build EMAIL_ VaultItem content per data-model.md
        now = datetime.now(timezone.utc).isoformat()
        content = f"""---
type: email
email_id: "{msg_id}"
from: "{source['from']}"
from_name: "{source['from_name']}"
to: "{source['to']}"
subject: "{source['subject'].replace('"', '\\"')}"
snippet: "{source['snippet'].replace('"', '\\"')}"
received_date: {source['received_date']}
priority: {priority}
status: pending
sensitivity: {sensitivity}
labels: {source['labels']}
has_attachments: {str(source['has_attachments']).lower()}
---

## Email Content

{source['body']}

## Suggested Actions

- [ ] Review and respond to this email
"""

        # Atomic write
        filename = f"EMAIL_{msg_id}.md"
        target_path = self.needs_action_dir / filename

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.needs_action_dir,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            tmp_path.rename(target_path)
        except Exception:
            if "tmp_path" in locals() and tmp_path.exists():
                tmp_path.unlink()
            raise

        # Track as processed
        self._processed_ids.add(msg_id)

        # Mark email as read in Gmail
        self._mark_as_read(msg_id)

        logger.info(
            "Created EMAIL_%s.md (sensitivity=%s, priority=%s, from=%s)",
            msg_id, sensitivity, priority, source["from"],
        )

        # Audit log
        append_log_entry(
            log_dir=self.log_dir,
            action_type="email_triage",
            actor="gmail_watcher",
            target=filename,
            parameters={
                "from": source["from"],
                "subject": source["subject"][:80],
                "sensitivity": sensitivity,
                "priority": priority,
                "has_attachments": source["has_attachments"],
            },
            result="success",
        )

        return target_path

    def _mark_as_read(self, message_id: str) -> None:
        """Mark a Gmail message as read by removing UNREAD label."""
        try:
            self._gmail.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
        except Exception:
            logger.exception("Failed to mark message %s as read", message_id)

    def _get_source_name(self, source: dict) -> str:
        """Human-readable name for logging."""
        return f"{source.get('from', 'unknown')}:{source.get('subject', '')[:40]}"


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from Gmail message payload."""
    mime_type = payload.get("mimeType", "")

    # Direct text/plain part
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Multipart: recurse into parts
    parts = payload.get("parts", [])
    for part in parts:
        # Prefer text/plain
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Fallback: try any text part
    for part in parts:
        result = _extract_body(part)
        if result:
            return result

    return "(no text body)"


def _has_attachments(payload: dict) -> bool:
    """Check if message has file attachments (not inline images)."""
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("filename") and part.get("body", {}).get("attachmentId"):
            return True
        # Recurse into multipart
        if _has_attachments(part):
            return True
    return False


# --- CLI entry point ---

def main() -> None:
    """Run the Gmail watcher from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Gmail Watcher — monitor inbox for actionable emails")
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run OAuth2 authentication flow (opens browser for consent)",
    )
    args = parser.parse_args()

    # Load .env from repo root
    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    vault_path = Path(os.getenv("VAULT_PATH", repo_root / "vault"))
    if not vault_path.is_absolute():
        vault_path = repo_root / vault_path

    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", str(repo_root / "credentials.json"))
    token_path = os.getenv("GMAIL_TOKEN_PATH", str(repo_root / "token.json"))
    poll_interval = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))

    # --auth mode: just authenticate and exit
    if args.auth:
        logger.info("Starting OAuth2 authentication flow...")
        _authenticate(credentials_path, token_path, interactive=True)
        logger.info("Authentication complete. You can now run the watcher without --auth.")
        return

    logger.info("Vault path: %s", vault_path)
    logger.info("Credentials: %s", credentials_path)
    logger.info("Token: %s", token_path)
    logger.info("Poll interval: %ds", poll_interval)

    watcher = GmailWatcher(
        vault_path=vault_path,
        check_interval=poll_interval,
        credentials_path=credentials_path,
        token_path=token_path,
    )

    # Log watcher start
    append_log_entry(
        log_dir=vault_path / "Logs",
        action_type="email_triage",
        actor="gmail_watcher",
        target="gmail_watcher",
        parameters={"event": "start", "poll_interval": poll_interval},
        result="success",
    )

    try:
        watcher.run()
    except KeyboardInterrupt:
        pass
    finally:
        append_log_entry(
            log_dir=vault_path / "Logs",
            action_type="email_triage",
            actor="gmail_watcher",
            target="gmail_watcher",
            parameters={"event": "stop"},
            result="success",
        )


if __name__ == "__main__":
    main()
