---
name: google-workspace
version: 0.1.0
description: "Google Workspace integration skill for Calendar, Drive, and Docs via Google APIs."
entrypoint: "gsuite_manager.py"
requires:
  python:
    - google-auth
    - google-auth-oauthlib
    - google-api-python-client
---

# Google Workspace Skill

Provides secure OAuth2 integration for Google Workspace services with these tools:

- `schedule_meeting(emails, time_iso, duration_minutes=30, summary="OpenPango Meeting")`
- `read_document(doc_id)`
- `create_document(title, content)`
- `search_drive_files(query, page_size=25, max_pages=5)`

## Auth model

- OAuth2 consent flow (installed app)
- refresh/access tokens stored in local `agent_integrations` SQLite table
- token auto-refresh via google-auth credentials object

## Environment

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI` (optional, default: `http://localhost:8765/callback`)
