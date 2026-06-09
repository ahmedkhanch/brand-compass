"""Email service stub — Resend or Ora SMTP."""


async def send_email(to: str, subject: str, body: str) -> dict:
    """Send a transactional email. Stub for now."""
    # Real implementation:
    # import resend
    # resend.Emails.send({"from": "...", "to": to, "subject": subject, "html": body})
    return {"sent": True, "to": to, "subject": subject, "provider": "stub"}
