---
name: email
description: "Native email management with IMAP/SMTP support for autonomous communication."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - email/read
    - email/send
    - email/thread
    - email/attachment
  author: "OpenPango Contributor"
  license: "MIT"
---

# Email Management Skill

Autonomous email management with IMAP and SMTP.

## Features

- **IMAP**: Read and monitor inbox
- **SMTP**: Send emails with CC, BCC, attachments
- **Thread Tracking**: Maintain conversation context
- **Secure Credentials**: Integration with agent_integrations

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `EMAIL_IMAP_HOST` | IMAP server host |
| `EMAIL_IMAP_PORT` | IMAP server port (default: 993) |
| `EMAIL_SMTP_HOST` | SMTP server host |
| `EMAIL_SMTP_PORT` | SMTP server port (default: 587) |
| `EMAIL_USER` | Email address |
| `EMAIL_PASSWORD` | App password |

## Usage

```python
from skills.email.email_handler import EmailHandler

# Initialize
handler = EmailHandler()

# Read unread emails
emails = handler.read_unread()

# Send email
handler.send(
    to="recipient@example.com",
    subject="Hello",
    body="This is a test email",
    cc=["cc@example.com"],
    attachments=["file.pdf"]
)
```
