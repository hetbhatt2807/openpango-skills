#!/usr/bin/env python3
"""
Google Workspace manager for OpenPango.

Implements OAuth2 auth + Calendar/Docs/Drive helpers:
- schedule_meeting
- read_document
- create_document
- search_drive_files (pagination + basic retry/rate-limit handling)
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except Exception:  # pragma: no cover
    Credentials = None  # type: ignore
    Flow = None  # type: ignore
    Request = None  # type: ignore
    build = None  # type: ignore
    HttpError = Exception  # type: ignore


SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.readonly",
]


@dataclass
class GoogleWorkspaceConfig:
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8765/callback"


class GoogleWorkspaceError(RuntimeError):
    pass


class GSuiteManager:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.config = self._load_config()
        self.db_path = db_path or str(Path.home() / ".openclaw" / "workspace" / "agent_integrations.db")
        self._init_db()

    def _load_config(self) -> GoogleWorkspaceConfig:
        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
        redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8765/callback").strip()

        if not client_id or not client_secret:
            raise GoogleWorkspaceError(
                "Missing GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET env vars"
            )
        return GoogleWorkspaceConfig(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_integrations (
                    provider TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def _store_tokens(self, token_data: Dict[str, Any]) -> None:
        payload = json.dumps(token_data)
        ts = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO agent_integrations(provider, data_json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    data_json=excluded.data_json,
                    updated_at=excluded.updated_at
                """,
                ("google-workspace", payload, ts),
            )
            conn.commit()

    def _load_tokens(self) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data_json FROM agent_integrations WHERE provider=?",
                ("google-workspace",),
            ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def build_oauth_authorize_url(self, state: str = "openpango") -> str:
        if not Flow:
            raise GoogleWorkspaceError("google-auth-oauthlib not installed")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.redirect_uri],
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = self.config.redirect_uri
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )
        return auth_url

    def exchange_code(self, code: str) -> Dict[str, Any]:
        if not Flow:
            raise GoogleWorkspaceError("google-auth-oauthlib not installed")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.redirect_uri],
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = self.config.redirect_uri
        flow.fetch_token(code=code)
        creds = flow.credentials

        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes or SCOPES),
        }
        self._store_tokens(token_data)
        return {"ok": True, "scopes": token_data["scopes"]}

    def _credentials(self) -> Credentials:
        if not Credentials:
            raise GoogleWorkspaceError("google-auth not installed")

        token_data = self._load_tokens()
        if not token_data:
            raise GoogleWorkspaceError("No stored Google OAuth tokens. Run OAuth flow first.")

        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        if creds.expired and creds.refresh_token:
            if not Request:
                raise GoogleWorkspaceError("google-auth transport not installed")
            creds.refresh(Request())
            self._store_tokens(
                {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": list(creds.scopes or SCOPES),
                }
            )
        return creds

    def _build_service(self, service_name: str, version: str):
        if not build:
            raise GoogleWorkspaceError("google-api-python-client not installed")
        return build(service_name, version, credentials=self._credentials(), cache_discovery=False)

    def _execute_with_retry(self, fn, retries: int = 4):
        delay = 1.0
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except HttpError as err:  # type: ignore
                status = getattr(getattr(err, "resp", None), "status", None)
                if status in (429, 500, 502, 503, 504) and attempt < retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise

    def schedule_meeting(
        self,
        emails: List[str],
        time_iso: str,
        duration_minutes: int = 30,
        summary: str = "OpenPango Meeting",
    ) -> Dict[str, Any]:
        calendar = self._build_service("calendar", "v3")
        event = {
            "summary": summary,
            "start": {"dateTime": time_iso},
            "end": {"dateTime": self._add_minutes_iso(time_iso, duration_minutes)},
            "attendees": [{"email": email} for email in emails],
        }

        created = self._execute_with_retry(
            lambda: calendar.events().insert(calendarId="primary", body=event).execute()
        )
        return {
            "id": created.get("id"),
            "htmlLink": created.get("htmlLink"),
            "status": created.get("status"),
        }

    def read_document(self, doc_id: str) -> Dict[str, Any]:
        docs = self._build_service("docs", "v1")
        doc = self._execute_with_retry(lambda: docs.documents().get(documentId=doc_id).execute())

        content = []
        for block in doc.get("body", {}).get("content", []):
            para = block.get("paragraph")
            if not para:
                continue
            for element in para.get("elements", []):
                text_run = element.get("textRun")
                if text_run and text_run.get("content"):
                    content.append(text_run["content"])

        return {
            "documentId": doc.get("documentId"),
            "title": doc.get("title"),
            "content": "".join(content).strip(),
        }

    def create_document(self, title: str, content: str) -> Dict[str, Any]:
        docs = self._build_service("docs", "v1")
        created = self._execute_with_retry(lambda: docs.documents().create(body={"title": title}).execute())

        doc_id = created.get("documentId")
        if content and doc_id:
            self._execute_with_retry(
                lambda: docs.documents()
                .batchUpdate(
                    documentId=doc_id,
                    body={
                        "requests": [
                            {
                                "insertText": {
                                    "location": {"index": 1},
                                    "text": content,
                                }
                            }
                        ]
                    },
                )
                .execute()
            )

        return {
            "documentId": doc_id,
            "title": created.get("title", title),
            "url": f"https://docs.google.com/document/d/{doc_id}/edit" if doc_id else None,
        }

    def search_drive_files(
        self,
        query: str,
        page_size: int = 25,
        max_pages: int = 5,
    ) -> Dict[str, Any]:
        drive = self._build_service("drive", "v3")
        files: List[Dict[str, Any]] = []
        page_token = None
        pages = 0

        while pages < max_pages:
            response = self._execute_with_retry(
                lambda: drive.files()
                .list(
                    q=query,
                    pageSize=page_size,
                    pageToken=page_token,
                    fields="nextPageToken, files(id,name,mimeType,modifiedTime,webViewLink)",
                )
                .execute()
            )

            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            pages += 1
            if not page_token:
                break

        return {
            "count": len(files),
            "pagesFetched": pages,
            "files": files,
        }

    @staticmethod
    def _add_minutes_iso(iso_value: str, minutes: int) -> str:
        from datetime import datetime, timedelta

        dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return (dt + timedelta(minutes=minutes)).isoformat()


__all__ = ["GSuiteManager", "GoogleWorkspaceError"]
