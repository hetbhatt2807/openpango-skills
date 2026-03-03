#!/usr/bin/env python3
"""
email_handler.py - Native email management with IMAP/SMTP.

Provides email reading, sending, and thread tracking.
"""

import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Email")

DB_PATH = os.getenv("AGENT_INTEGRATIONS_DB", str(Path.home() / ".openclaw" / "agent_integrations.db"))


class EmailError(Exception):
    """Base exception for email errors."""
    pass


class IMAPError(EmailError):
    """IMAP connection error."""
    pass


class SMTPError(EmailError):
    """SMTP connection error."""
    pass


class EmailHandler:
    """
    Email handler with IMAP/SMTP support.
    
    Features:
    - Read unread emails via IMAP
    - Send emails via SMTP
    - Thread tracking
    - Attachment support
    - Secure credential storage
    """
    
    def __init__(
        self,
        imap_host: Optional[str] = None,
        imap_port: int = 993,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = True
    ):
        """
        Initialize email handler.
        
        Args:
            imap_host: IMAP server host
            imap_port: IMAP server port
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            user: Email address
            password: App password
            use_ssl: Use SSL/TLS
        """
        self.imap_host = imap_host or os.getenv("EMAIL_IMAP_HOST", "")
        self.imap_port = imap_port
        self.smtp_host = smtp_host or os.getenv("EMAIL_SMTP_HOST", "")
        self.smtp_port = smtp_port
        self.user = user or os.getenv("EMAIL_USER", "")
        self.password = password or os.getenv("EMAIL_PASSWORD", "")
        self.use_ssl = use_ssl
        
        self._imap = None
        self._smtp = None
        
        if not self.user:
            logger.warning("No EMAIL_USER set. Running in MOCK mode.")
            self._mock = True
        else:
            self._mock = False
        
        self._init_db()
    
    def _init_db(self):
        """Initialize thread tracking database."""
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_threads (
                thread_id TEXT PRIMARY KEY,
                subject TEXT,
                participants TEXT,
                last_message_id TEXT,
                last_message_date TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_messages (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT,
                from_addr TEXT,
                to_addrs TEXT,
                subject TEXT,
                body TEXT,
                date TEXT,
                unread INTEGER,
                FOREIGN KEY (thread_id) REFERENCES email_threads(thread_id)
            )
        """)
        conn.commit()
        conn.close()
    
    # ─── IMAP Operations ───────────────────────────────────────────
    
    def _connect_imap(self):
        """Connect to IMAP server."""
        if self._mock:
            return None
        
        try:
            if self.use_ssl:
                self._imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            else:
                self._imap = imaplib.IMAP4(self.imap_host, self.imap_port)
            
            self._imap.login(self.user, self.password)
            logger.info(f"Connected to IMAP: {self.imap_host}")
            return self._imap
        except Exception as e:
            raise IMAPError(f"IMAP connection failed: {e}")
    
    def _disconnect_imap(self):
        """Disconnect from IMAP server."""
        if self._imap:
            try:
                self._imap.close()
                self._imap.logout()
            except:
                pass
            self._imap = None
    
    def read_unread(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Read unread emails from inbox.
        
        Args:
            limit: Maximum number of emails to read
            
        Returns:
            List of email dicts
        """
        if self._mock:
            return self._mock_read_unread(limit)
        
        emails = []
        
        try:
            self._connect_imap()
            self._imap.select("INBOX")
            
            # Search for unread messages
            status, messages = self._imap.search(None, "UNSEEN")
            
            if status != "OK":
                return emails
            
            message_ids = messages[0].split()[:limit]
            
            for msg_id in message_ids:
                status, msg_data = self._imap.fetch(msg_id, "(RFC822)")
                
                if status == "OK":
                    raw_email = msg_data[0][1]
                    parsed = self._parse_email(raw_email)
                    emails.append(parsed)
                    
                    # Store in thread tracking
                    self._track_message(parsed)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error reading emails: {e}")
            return emails
        finally:
            self._disconnect_imap()
    
    def _parse_email(self, raw_email: bytes) -> Dict[str, Any]:
        """Parse raw email into dict."""
        msg = email.message_from_bytes(raw_email)
        
        # Get body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        
        return {
            "message_id": msg.get("Message-ID", ""),
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "cc": msg.get("Cc", ""),
            "subject": msg.get("Subject", ""),
            "date": msg.get("Date", ""),
            "body": body,
            "unread": True
        }
    
    def _mock_read_unread(self, limit: int) -> List[Dict[str, Any]]:
        """Mock read unread emails."""
        return [
            {
                "message_id": f"<mock-{i}@example.com>",
                "from": f"sender{i}@example.com",
                "to": self.user or "me@example.com",
                "cc": "",
                "subject": f"[MOCK] Test Email {i}",
                "date": datetime.now().isoformat(),
                "body": f"This is mock email {i}.",
                "unread": True
            }
            for i in range(min(limit, 3))
        ]
    
    # ─── SMTP Operations ────────────────────────────────────────────
    
    def _connect_smtp(self):
        """Connect to SMTP server."""
        if self._mock:
            return None
        
        try:
            if self.use_ssl:
                self._smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                self._smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
                self._smtp.starttls()
            
            self._smtp.login(self.user, self.password)
            logger.info(f"Connected to SMTP: {self.smtp_host}")
            return self._smtp
        except Exception as e:
            raise SMTPError(f"SMTP connection failed: {e}")
    
    def _disconnect_smtp(self):
        """Disconnect from SMTP server."""
        if self._smtp:
            try:
                self._smtp.quit()
            except:
                pass
            self._smtp = None
    
    def send(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (text or HTML)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
            reply_to: Message ID to reply to
            
        Returns:
            Send result dict
        """
        if self._mock:
            return self._mock_send(to, subject, body)
        
        try:
            self._connect_smtp()
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.user
            msg["To"] = to
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            if reply_to:
                msg["In-Reply-To"] = reply_to
                msg["References"] = reply_to
            
            # Add body
            msg.attach(MIMEText(body, "plain"))
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {Path(filepath).name}"
                        )
                        msg.attach(part)
            
            # Send
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            self._smtp.sendmail(self.user, recipients, msg.as_string())
            
            result = {
                "success": True,
                "to": to,
                "subject": subject,
                "sent_at": datetime.now().isoformat()
            }
            
            # Track in thread
            self._track_sent(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._disconnect_smtp()
    
    def _mock_send(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Mock send email."""
        return {
            "success": True,
            "to": to,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "mock": True
        }
    
    # ─── Thread Tracking ─────────────────────────────────────────────
    
    def _track_message(self, email_data: Dict[str, Any]):
        """Track message in thread database."""
        conn = sqlite3.connect(DB_PATH)
        
        message_id = email_data.get("message_id", "")
        subject = email_data.get("subject", "")
        
        # Try to find existing thread
        cursor = conn.execute(
            "SELECT thread_id FROM email_threads WHERE subject = ?",
            (subject,)
        )
        row = cursor.fetchone()
        
        if row:
            thread_id = row[0]
        else:
            # Create new thread
            import uuid
            thread_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO email_threads 
                   (thread_id, subject, participants, last_message_id, last_message_date, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (thread_id, subject, email_data.get("from", ""), message_id, 
                 email_data.get("date", ""), datetime.now().isoformat(), datetime.now().isoformat())
            )
        
        # Store message
        conn.execute(
            """INSERT OR REPLACE INTO email_messages
               (message_id, thread_id, from_addr, to_addrs, subject, body, date, unread)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (message_id, thread_id, email_data.get("from", ""), email_data.get("to", ""),
             subject, email_data.get("body", ""), email_data.get("date", ""), 1)
        )
        
        conn.commit()
        conn.close()
    
    def _track_sent(self, email_data: Dict[str, Any]):
        """Track sent email."""
        # Similar to _track_message but for sent emails
        pass
    
    def get_thread(self, subject: str) -> List[Dict[str, Any]]:
        """
        Get all messages in a thread.
        
        Args:
            subject: Email subject to search
            
        Returns:
            List of messages in thread
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            """SELECT * FROM email_messages 
               WHERE subject LIKE ? 
               ORDER BY date DESC""",
            (f"%{subject}%",)
        )
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return messages
    
    def list_threads(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List all threads.
        
        Args:
            limit: Maximum threads to return
            
        Returns:
            List of thread dicts
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            """SELECT * FROM email_threads 
               ORDER BY updated_at DESC 
               LIMIT ?""",
            (limit,)
        )
        
        threads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return threads


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    handler = EmailHandler()
    
    if len(sys.argv) < 2:
        print("Usage: python email_handler.py <command> [args]")
        print("\nCommands:")
        print("  read [limit]          Read unread emails")
        print("  send <to> <subject>   Send email")
        print("  threads               List threads")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "read":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        emails = handler.read_unread(limit)
        print(json.dumps(emails, indent=2, default=str))
    
    elif cmd == "send":
        to = sys.argv[2]
        subject = sys.argv[3]
        body = sys.argv[4] if len(sys.argv) > 4 else "Test email"
        result = handler.send(to, subject, body)
        print(json.dumps(result, indent=2))
    
    elif cmd == "threads":
        threads = handler.list_threads()
        print(json.dumps(threads, indent=2, default=str))
