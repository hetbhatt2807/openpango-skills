---
name: "Secure Enclaves Sandbox"
description: "Executes untrusted 3rd-party third-party skills in a highly restricted containerized environment."
version: "1.0.0"
user-invocable: false
system-daemon: true
metadata:
  capabilities:
    - security/sandbox
    - system/execution
  author: "Antigravity (OpenPango Core)"
  license: "MIT"
---

# Secure Enclaves Sandbox

Enterprise compliance requires that an agent downloading a 3rd-party skill from the Decentralized Registry does not compromise the host machine. This runner executes untrusted code in a highly restricted sandbox that blocks network access, env variable dumping, and sensitive file system reads.

## Usage

```python
from skills.security.enclave_runner import EnclaveRunner, SandboxPolicy

sandbox = EnclaveRunner()

# Tries to read /etc/passwd or steal os.environ
malicious_code = \"\"\"
import os
print(os.environ)
with open('/etc/passwd') as f:
    print(f.read())
\"\"\"

result = sandbox.execute(
    code_string=malicious_code, 
    policy=SandboxPolicy.STRICT
)

print(f"Status: {result['status']}") # error: policy violation
print(f"Logs: {result['stderr']}")
```

## Features
- **File System Jails**: Mounts an isolated temporary directory.
- **Network Blackholing**: Blocks egress traffic to prevent data exfiltration.
- **Process Isolation**: Drops capabilities and restricts memory/CPU quotas.
