#!/usr/bin/env python3
"""
Test different IMAP hostnames for Polytechnique
"""
import imaplib
import os
from dotenv import load_dotenv

def test_imap_connection(host, user, password):
    """Test IMAP connection to a specific host"""
    try:
        print(f"🔍 Testing {host}...")
        mail = imaplib.IMAP4_SSL(host)
        mail.login(user, password)
        mail.logout()
        print(f"✅ SUCCESS: {host} works!")
        return True
    except Exception as e:
        print(f"❌ FAILED: {host} - {str(e)[:50]}...")
        return False

def main():
    # Load credentials
    load_dotenv()
    parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(parent_env):
        load_dotenv(parent_env)

    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")

    if not user or not password:
        print("❌ No SMTP credentials found in .env")
        return

    print("🔧 Testing IMAP connections for Polytechnique...")
    print("=" * 50)

    # Common Polytechnique IMAP hostnames to test
    hostnames_to_test = [
        "imap.polytechnique.edu",
        "mail.polytechnique.edu",
        "webmail.polytechnique.edu",
        "zimbra.polytechnique.edu",
        "outlook.office365.com",  # If using Office 365
    ]

    working_hosts = []

    for host in hostnames_to_test:
        if test_imap_connection(host, user, password):
            working_hosts.append(host)

    print("\n" + "=" * 50)
    if working_hosts:
        print("✅ WORKING HOSTNAMES:")
        for host in working_hosts:
            print(f"   IMAP_HOST={host}")
        print(f"\n🎯 Use one of these in your .env file!")
    else:
        print("❌ No working IMAP hostnames found")
        print("💡 Check your Polytechnique email settings for IMAP configuration")
        print("💡 Or contact Polytechnique IT support")

if __name__ == "__main__":
    main()
