#!/usr/bin/env python3
"""CLI utility to explore, test, and register free LLM APIs from awesome-freellm-apis.

Usage:
  python setup_free_apis.py list
  python setup_free_apis.py test <provider_id> <api_key>
  python setup_free_apis.py add <provider_id> <api_key> [--priority 10]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

CATALOG_PATH = backend_dir / "seed_data" / "awesome_freellm_apis.json"


def load_catalog():
    if not CATALOG_PATH.exists():
        print(f"Error: Catalog not found at {CATALOG_PATH}")
        sys.exit(1)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_list(args):
    catalog = load_catalog()
    print("=" * 80)
    print("AWESOME FREE LLM APIs CATALOG (open-free-llm-api/awesome-freellm-apis)")
    print("=" * 80)
    for p in catalog:
        print(f"\nID: {p['id']} [{p['category']}]")
        print(f"Name: {p['name']}")
        print(f"Base URL: {p['base_url']}")
        print(f"Models: {', '.join(p['models'])}")
        print(f"Rate Limits: {p.get('rpm_limit', 0)} RPM")
        if p.get("key_url"):
            print(f"Get Free Key: {p['key_url']}")
        print(f"Description: {p['description']}")
    print("\n" + "=" * 80)


async def cmd_test(args):
    import httpx

    catalog = {p["id"]: p for p in load_catalog()}
    pid = args.provider_id.lower()
    if pid not in catalog:
        print(f"Unknown provider '{pid}'. Run 'list' to see valid IDs.")
        return

    p = catalog[pid]
    model = p["models"][0]
    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["Authorization"] = f"Bearer {args.api_key.strip()}"

    url = p["base_url"].rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with 'API is working!' and nothing else."}],
        "temperature": 0.1,
        "max_tokens": 50,
    }

    print(f"Testing {p['name']} using model '{model}'...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=body)
            if res.status_code == 200:
                data = res.json()
                reply = data["choices"][0]["message"]["content"]
                print(f"[SUCCESS] Response received:\n{reply}")
            else:
                print(f"[FAILED] HTTP {res.status_code}:\n{res.text[:300]}")
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")


async def cmd_add(args):
    from app.db import db
    from app.security import encrypt
    from datetime import datetime, timezone

    catalog = {p["id"]: p for p in load_catalog()}
    pid = args.provider_id.lower()
    if pid not in catalog:
        print(f"Unknown provider '{pid}'. Run 'list' to see valid IDs.")
        return

    p = catalog[pid]
    doc = {
        "name": p["name"],
        "base_url": p["base_url"].rstrip("/"),
        "model": ", ".join(p["models"]),
        "api_key_enc": encrypt(args.api_key.strip()) if args.api_key else "",
        "priority": args.priority,
        "enabled": True,
        "trusted": pid == "ollama",
        "rpm_limit": p.get("rpm_limit", 0),
        "rpd_limit": p.get("rpd_limit", 0) or 0,
        "timeout_seconds": 300 if pid == "ollama" else 0,
        "extra_headers": {},
        "stats": {"success": 0, "failure": 0},
        "created_at": datetime.now(timezone.utc),
    }

    res = await db.providers.insert_one(doc)
    print(f"[OK] Added provider '{p['name']}' (ID: {res.inserted_id}) with priority {args.priority}.")


def main():
    parser = argparse.ArgumentParser(description="Awesome Free LLM APIs Helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List all free LLM API providers")
    p_list.set_defaults(func=lambda args: cmd_list(args))

    p_test = sub.add_parser("test", help="Test an API key against a provider")
    p_test.add_argument("provider_id", help="Provider ID from the catalog")
    p_test.add_argument("api_key", nargs="?", default="", help="Provider API key")
    p_test.set_defaults(func=lambda args: asyncio.run(cmd_test(args)))

    p_add = sub.add_parser("add", help="Add a provider directly to MongoDB")
    p_add.add_argument("provider_id", help="Provider ID from the catalog")
    p_add.add_argument("api_key", nargs="?", default="", help="Provider API key")
    p_add.add_argument("--priority", type=int, default=10, help="Priority (default: 10)")
    p_add.set_defaults(func=lambda args: asyncio.run(cmd_add(args)))

    parsed = parser.parse_args()
    parsed.func(parsed)


if __name__ == "__main__":
    main()

