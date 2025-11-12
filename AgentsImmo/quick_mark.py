#!/usr/bin/env python3
"""
Quick interactive script to mark responses
Usage: python quick_mark.py
"""
import os
import sys

def mark_response():
    csv_path = "master_contacts_tracking.csv"
    if not os.path.exists(csv_path):
        print(f"❌ {csv_path} not found!")
        return

    print("🎯 Quick Response Marker")
    print("=" * 30)

    while True:
        email = input("Email (or 'quit' to exit): ").strip()
        if email.lower() in ['quit', 'q', 'exit']:
            break

        if not email:
            continue

        status = input("Status (responded/not_interested/qualified) [responded]: ").strip() or "responded"
        notes = input("Notes (optional): ").strip()

        # Build command
        cmd = f"python mark_answered.py {csv_path} single {email} --status {status}"
        if notes:
            cmd += f' --notes "{notes}"'

        print(f"\n🔧 Running: {cmd}")
        os.system(cmd)
        print()

if __name__ == "__main__":
    mark_response()
