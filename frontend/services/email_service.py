"""Brevo transactional email service for RPRMS.

Email delivery is deliberately best-effort: a Brevo/API failure must never
undo a successful registration, paper submission, or review decision.
"""
from __future__ import annotations

import html
import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()
_base_app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_app = os.path.join(_base_app, ".env")
if os.path.exists(_env_app):
    load_dotenv(_env_app)

logger = logging.getLogger(__name__)
BREVO_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to_email: str, to_name: str, subject: str,
               html_content: str, text_content: str | None = None) -> bool:
    """Send one transactional email using Brevo's HTTP API.

    Returns True when Brevo accepts the request, False otherwise. Never logs
    the API key or full message content.
    """
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("BREVO_SENDER_EMAIL", "").strip()
    sender_name = os.getenv("BREVO_SENDER_NAME", "RPRMS Team").strip()

    if not api_key or not sender_email:
        logger.warning("Brevo email skipped: BREVO_API_KEY or BREVO_SENDER_EMAIL is missing.")
        return False
    if not to_email or "@" not in to_email:
        logger.warning("Brevo email skipped: recipient address is missing or invalid.")
        return False

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content or "Please view this email in an HTML-capable email client.",
    }
    request = Request(
        BREVO_EMAIL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            if 200 <= response.status < 300:
                logger.info("Brevo accepted email to %s (subject: %s).", to_email, subject)
                return True
            logger.warning("Brevo returned unexpected HTTP status %s.", response.status)
    except HTTPError as exc:
        # Do not log request headers or credentials. Brevo's response can help
        # identify permission/sender issues without exposing the API key.
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = "No response details available."
        logger.warning("Brevo rejected email (HTTP %s): %s", exc.code, detail)
    except (URLError, TimeoutError, OSError) as exc:
        logger.warning("Brevo email request failed: %s", type(exc).__name__)
    except Exception:
        logger.exception("Unexpected error while sending email through Brevo.")
    return False


def _email_shell(title: str, body_html: str) -> str:
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif;color:#172033;">
  <div style="max-width:640px;margin:24px auto;padding:0 12px;">
    <div style="background:#173b67;color:#fff;padding:22px 26px;border-radius:12px 12px 0 0;">
      <div style="font-size:12px;letter-spacing:1.5px;text-transform:uppercase;opacity:.85;">Research Paper Repository</div>
      <h1 style="font-size:24px;margin:8px 0 0;">RPRMS</h1>
    </div>
    <div style="background:#fff;padding:26px;border:1px solid #e5eaf0;border-top:0;">
      <h2 style="font-size:21px;margin:0 0 16px;">{safe_title}</h2>
      {body_html}
    </div>
    <div style="text-align:center;color:#667085;font-size:12px;padding:16px;">Automated notification from RPRMS. Please do not reply to this email.</div>
  </div>
</body></html>"""


def _paragraph(text: str) -> str:
    return f'<p style="font-size:15px;line-height:1.65;margin:0 0 14px;">{html.escape(str(text))}</p>'


def _details(rows: list[tuple[str, str]]) -> str:
    parts = ['<table role="presentation" style="width:100%;border-collapse:collapse;margin:18px 0;">']
    for label, value in rows:
        parts.append(
            '<tr>'
            f'<td style="padding:10px;border-bottom:1px solid #edf0f4;color:#667085;width:34%;font-size:13px;">{html.escape(label)}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #edf0f4;font-size:14px;font-weight:600;">{html.escape(str(value or "—"))}</td>'
            '</tr>'
        )
    parts.append('</table>')
    return ''.join(parts)


def send_registration_email(name: str, email: str) -> bool:
    safe_name = html.escape(name or "there")
    body = _paragraph(f"Hello {name or 'there'},")
    body += _paragraph("Your student account has been created successfully. You can now sign in to RPRMS to search the research repository and bookmark papers.")
    body += _paragraph("Thank you for joining RPRMS.")
    return send_email(email, name, "Welcome to RPRMS | Registration Successful",
                      _email_shell("Registration successful", body),
                      f"Hello {name or 'there'}, your RPRMS student account has been created successfully.")


def send_submission_email(name: str, email: str, paper: dict) -> bool:
    title = paper.get("title", "Research paper")
    code = paper.get("paper_code", "Pending")
    body = _paragraph(f"Hello {name or 'Faculty Member'},")
    body += _paragraph("We have received your research paper. It is now awaiting review by an administrator.")
    body += _details([("Paper title", title), ("Paper code", code), ("Status", "Pending Review")])
    body += _paragraph("You will receive another email when the review decision is recorded in RPRMS.")
    return send_email(email, name, f"RPRMS | Paper Submission Received – {code}",
                      _email_shell("Paper submission received", body),
                      f"Your paper '{title}' ({code}) was received and is pending review.")


def send_review_email(name: str, email: str, paper: dict, status: str,
                      comments: str = "") -> bool:
    code = paper.get("paper_code", "Paper")
    title = paper.get("title", "Research paper")
    labels = {
        "approved": ("Paper Approved", "RPRMS | Paper Approved"),
        "rejected": ("Paper Review Decision", "RPRMS | Paper Review Decision"),
        "changes_requested": ("Changes Required", "RPRMS | Changes Required"),
    }
    heading, subject_prefix = labels.get(status, ("Paper Status Updated", "RPRMS | Paper Status Updated"))
    body = _paragraph(f"Hello {name or 'Faculty Member'},")
    if status == "approved":
        body += _paragraph("Good news! Your research paper has been approved by the administrator.")
        next_step = "Your paper is now approved in RPRMS. Its availability follows the repository's access rules."
    elif status == "rejected":
        body += _paragraph("The administrator has reviewed your research paper and marked it as rejected.")
        next_step = "Please review the administrator's comments below. Contact the administrator if you need clarification."
    else:
        body += _paragraph("The administrator has requested changes to your research paper before it can proceed.")
        next_step = "Please sign in to RPRMS, review the feedback below, and upload a revised version."
    body += _details([("Paper title", title), ("Paper code", code), ("Decision", status.replace("_", " ").title())])
    if comments and comments.strip():
        body += '<div style="background:#f7f9fc;border-left:4px solid #64748b;padding:14px 16px;margin:18px 0;">'
        body += '<div style="font-size:12px;color:#667085;margin-bottom:6px;font-weight:700;">ADMINISTRATOR COMMENTS</div>'
        body += f'<div style="font-size:14px;line-height:1.6;white-space:pre-wrap;">{html.escape(comments.strip())}</div></div>'
    body += _paragraph(next_step)
    return send_email(email, name, f"{subject_prefix} – {code}",
                      _email_shell(heading, body),
                      f"Paper: {title}\nCode: {code}\nStatus: {status}\nComments: {comments or 'None'}\n{next_step}")
