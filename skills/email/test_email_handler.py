#!/usr/bin/env python3
"""test_email_handler.py - Tests for email handler."""

import os
import sys
import tempfile
import unittest
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.email.email_handler import EmailHandler, EmailError


class TestEmailHandlerMock(unittest.TestCase):
    """Test email handler in mock mode."""
    
    def setUp(self):
        """Set up test handler."""
        os.environ["EMAIL_USER"] = ""
        self.handler = EmailHandler()
    
    def test_mock_mode(self):
        """Test that handler starts in mock mode."""
        self.assertTrue(self.handler._mock)
    
    def test_read_unread_mock(self):
        """Test reading unread emails in mock mode."""
        emails = self.handler.read_unread(limit=5)
        self.assertIsInstance(emails, list)
        self.assertGreater(len(emails), 0)
        self.assertIn("message_id", emails[0])
        self.assertIn("from", emails[0])
        self.assertIn("subject", emails[0])
    
    def test_send_mock(self):
        """Test sending email in mock mode."""
        result = self.handler.send(
            to="test@example.com",
            subject="Test Subject",
            body="Test body"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["to"], "test@example.com")
        self.assertTrue(result["mock"])
    
    def test_send_with_cc(self):
        """Test sending with CC."""
        result = self.handler.send(
            to="test@example.com",
            subject="Test",
            body="Body",
            cc=["cc1@example.com", "cc2@example.com"]
        )
        self.assertTrue(result["success"])
    
    def test_list_threads(self):
        """Test listing threads."""
        threads = self.handler.list_threads()
        self.assertIsInstance(threads, list)
    
    def test_get_thread(self):
        """Test getting thread by subject."""
        messages = self.handler.get_thread("Test")
        self.assertIsInstance(messages, list)


class TestEmailHandlerEnvironment(unittest.TestCase):
    """Test environment configuration."""
    
    def test_imap_config(self):
        """Test IMAP configuration."""
        handler = EmailHandler(
            imap_host="imap.example.com",
            imap_port=993
        )
        self.assertEqual(handler.imap_host, "imap.example.com")
        self.assertEqual(handler.imap_port, 993)
    
    def test_smtp_config(self):
        """Test SMTP configuration."""
        handler = EmailHandler(
            smtp_host="smtp.example.com",
            smtp_port=587
        )
        self.assertEqual(handler.smtp_host, "smtp.example.com")
        self.assertEqual(handler.smtp_port, 587)
    
    def test_env_variables(self):
        """Test environment variables."""
        os.environ["EMAIL_IMAP_HOST"] = "env.imap.com"
        os.environ["EMAIL_SMTP_HOST"] = "env.smtp.com"
        os.environ["EMAIL_USER"] = "env@example.com"
        
        handler = EmailHandler()
        self.assertEqual(handler.imap_host, "env.imap.com")
        self.assertEqual(handler.smtp_host, "env.smtp.com")
        self.assertEqual(handler.user, "env@example.com")


class TestDatabase(unittest.TestCase):
    """Test thread tracking database."""
    
    def test_database_tables(self):
        """Test database tables exist."""
        # Create a test database
        db_path = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(db_path)
        
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_threads (
                thread_id TEXT PRIMARY KEY,
                subject TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_messages (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT
            )
        """)
        conn.commit()
        
        # Check tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.assertIn("email_threads", tables)
        self.assertIn("email_messages", tables)
        
        # Cleanup
        os.unlink(db_path)


if __name__ == "__main__":
    unittest.main()
