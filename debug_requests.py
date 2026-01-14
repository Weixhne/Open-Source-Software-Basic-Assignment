#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Simple script to debug the requests module structure
import requests

print("=== Requests Module Debug ===")
print(f"Requests version: {requests.__version__ if hasattr(requests, '__version__') else 'Unknown'}")
print(f"Module path: {requests.__file__ if hasattr(requests, '__file__') else 'Unknown'}")

print("\n=== Available attributes in requests module ===")
attrs = dir(requests)
print(f"Total attributes: {len(attrs)}")
for attr in sorted(attrs):
    if not attr.startswith('_'):
        print(f"  - {attr}")

print("\n=== Testing basic functionality ===")
try:
    # Test if we can import from requests
    from requests import get
    print("? Successfully imported get from requests")
except Exception as e:
    print(f"? Failed to import get: {e}")

try:
    # Test if the get function is directly available
    if hasattr(requests, 'get'):
        print("? requests.get is available")
    else:
        print("? requests.get is NOT available")
except Exception as e:
    print(f"? Error checking requests.get: {e}")

try:
    # Test session functionality
    if hasattr(requests, 'Session'):
        print("? requests.Session is available")
    else:
        print("? requests.Session is NOT available")
except Exception as e:
    print(f"? Error checking requests.Session: {e}")
