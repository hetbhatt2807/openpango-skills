#!/usr/bin/env python3
"""Red Team QA Tester - Simplified version for submission."""
import subprocess
import json
import os
import sys
import re
from datetime import datetime

class RedTeamAgent:
    def __init__(self, target_path):
        self.target_path = target_path
        self.vulnerabilities = []
    
    def run_security_scan(self):
        print(f"[*] Scanning: {self.target_path}")
        self._test_sql_injection()
        self._test_xss()
        self._test_auth_bypass()
        self._test_command_injection()
        return {
            "vulnerabilities_found": len(self.vulnerabilities),
            "critical_count": len([v for v in self.vulnerabilities if v['severity'] == "critical"]),
            "vulnerabilities": self.vulnerabilities
        }
    
    def _test_sql_injection(self):
        patterns = [r"SELECT.*FROM.*WHERE.*\$", r"\.execute\s*\(\s*[^,)]*\+"]
        self._scan_patterns(patterns, "sql_injection", "critical")
    
    def _test_xss(self):
        patterns = [r"innerHTML\s*=", r"dangerouslySetInnerHTML"]
        self._scan_patterns(patterns, "xss", "high")
    
    def _test_auth_bypass(self):
        patterns = [r"password\s*=\s*['\"]", r"api_key\s*=\s*['\"]"]
        self._scan_patterns(patterns, "auth_bypass", "critical")
    
    def _test_command_injection(self):
        patterns = [r"os\.system\s*\(", r"subprocess\.call\s*\("]
        self._scan_patterns(patterns, "command_injection", "critical")
    
    def _scan_patterns(self, patterns, category, severity):
        for root, dirs, files in os.walk(self.target_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    self.vulnerabilities.append({
                                        "severity": severity,
                                        "category": category,
                                        "file": filepath,
                                        "timestamp": datetime.now().isoformat()
                                    })
                    except: pass

if __name__ == "__main__":
    agent = RedTeamAgent(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(agent.run_security_scan(), indent=2))
