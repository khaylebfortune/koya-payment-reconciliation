#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def amount_to_cents(raw):
    """Amounts arrive as numbers or as strings like "4,804.15"."""
    if isinstance(raw, bool) or raw is None:
        return None
    try:
        text = str(raw).strip().replace(",", "")
        cents = (Decimal(text) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    return int(cents)


def sort_key(event):
    """Ordering key for attempts: the event's timestamp."""
    return str(event.get("ts") or "")


latest = {}

with open("payments.jsonl") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        # Unreadable lines are skipped.
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue

        # Events without a transaction id are not payments we can track.
        txn_id = event.get("txn_id")
        if txn_id is None or not str(txn_id).strip():
            continue

        # Only the latest attempt for each txn_id counts.
        previous = latest.get(txn_id)
        if previous is None or sort_key(event) > sort_key(previous):
            latest[txn_id] = event

total_cents = 0
count = 0

for event in latest.values():
    if event.get("status") == "success":
        count += 1
        cents = amount_to_cents(event.get("amount"))
        if cents is not None:
            total_cents += cents

total = total_cents / 100

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
