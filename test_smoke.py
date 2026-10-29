#!/usr/bin/env python3
"""Quick smoke test for Netckore prototype.

This verifies that the core modules load, the HTML interface exists,
and basic diagnostics work without launching the full pywebview window.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Netckore Smoke Test ===")

# 1. Imports
print("[1/6] Checking imports...")
from netckore.core import monitoring
print("  OK: monitoring imported")

# 2. Translation manager
print("[2/6] Checking translations...")
from netckore.i18n import TranslationManager, LANGUAGE_OPTIONS
TranslationManager()
print(f"  OK: {len(LANGUAGE_OPTIONS)} languages available ({', '.join(LANGUAGE_OPTIONS.keys())})")

# 3. Basic diagnostics
print("[3/6] Running connectivity check...")
results = monitoring.diagnosis_categories()
print(f"  OK: {len(results)} categories defined")

# 4. Ping
print("[4/6] Running ping (may take a few seconds)...")
results = monitoring.diagnose_ping()
print(f"  OK: ping result = {results}")

# 5. DNS
print("[5/6] Checking DNS resolution...")
results = monitoring.diagnose_dns()
print(f"  OK: dns result = {results}")

# 6. HTML interface
print("[6/6] Checking frontend file...")
from netckore.core.system import frontend_path
path = frontend_path()
assert os.path.exists(path), f"Frontend not found: {path}"
print(f"  OK: {path} exists ({os.path.getsize(path)} bytes)")

print("\nAll smoke tests passed!")
print("To run full prototype: python -m netckore")
