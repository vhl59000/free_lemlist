#!/usr/bin/env python3
"""
Check email responses by analyzing sent emails vs master_contacts_tracking.csv
Identifies who hasn't responded yet
"""
import imaplib
import email
import email.header
import csv
import os
import re
import unicodedata
from email.mime.text import MIMEText
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sys

def load_env():
    """Load environment variables"""
    load_dotenv()
    parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(parent_env):
        load_dotenv(parent_env)
    return {
        "IMAP_HOST": os.getenv("IMAP_HOST", "webmail.polytechnique.fr"),  # Polytechnique IMAP host
        "IMAP_USER": os.getenv("SMTP_USER"),  # Reuse SMTP credentials
        "IMAP_PASS": os.getenv("SMTP_PASS"),
        "SENT_FOLDER": os.getenv("SENT_FOLDER", '"Sent"'),
    }

def decode_header(header_str):
    """Decode email header properly"""
    if not header_str:
        return ""
    decoded_parts = email.header.decode_header(header_str)
    decoded_str = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            decoded_str += str(part)
    return decoded_str

def extract_emails_from_header(header_value):
    """Extract email addresses from To/Cc/Bcc headers"""
    if not header_value:
        return []

    emails = []
    # Regex to find email addresses
    email_pattern = r'<([^>]+)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    matches = re.findall(email_pattern, header_value)

    for match in matches:
        email_addr = match[0] or match[1]  # Take the angled bracket version first, then plain
        if email_addr and '@' in email_addr:
            emails.append(email_addr.lower().strip())

    return list(set(emails))  # Remove duplicates

def is_system_email(email_address):
    """Check if an email is from a system/non-prospect source"""
    if not email_address:
        return True
    
    email_lower = email_address.lower()
    
    # Filter out system emails
    system_patterns = [
        'postmaster',
        'mailer-daemon',
        'noreply',
        'no-reply',
        'donotreply',
        'reponse.auto',  # Auto-reply addresses
        'reponse-auto',
        'auto-reponse',
        'invitations.mailinblack.com',  # Email relay system
        'onmicrosoft.com',  # Microsoft system emails
        'mailinblack.com',
        'undeliverable',
        'bounce',
        'returned',
        'delivery failure',
    ]
    
    for pattern in system_patterns:
        if pattern in email_lower:
            return True
    
    return False

def is_automatic_response(subject, content=""):
    """Check if an email is an automatic response (out of office, etc.)"""
    # Common patterns for automatic responses
    auto_patterns = [
        "réponse automatique",
        "automatic reply",
        "auto-reply",
        "out of office",
        "absence",
        "absent",  # "Absent jusqu'au..."
        "congés",
        "vacation",
        "vacances",
        "en congé",
        "away from office",
        "ne fait plus partie",
        "no longer with",
        "has left",
        "n'est plus",
        "déménagement",
        "transfert",
        "redirection",
        "forward",
        "automatique",
        "automated",
        "robot",
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "undeliverable",  # Delivery failures
    ]

    subject_lower = subject.lower() if subject else ""
    content_lower = content.lower() if content else ""

    # Check subject for automatic response indicators
    for pattern in auto_patterns:
        if pattern in subject_lower or pattern in content_lower:
            return True

    return False

def get_received_responses(imap_cfg, search_subject=None):
    """Get all received emails (responses), optionally filtered by subject"""
    try:
        mail = imaplib.IMAP4_SSL(imap_cfg["IMAP_HOST"])
        mail.login(imap_cfg["IMAP_USER"], imap_cfg["IMAP_PASS"])

        # Use INBOX for received emails
        inbox_folder = os.getenv("INBOX_FOLDER", "INBOX")
        mail.select(inbox_folder)

        # Search criteria
        if search_subject:
            # Search for emails containing key words (IMAP doesn't handle accents well)
            # We'll filter more precisely after fetching
            search_criteria = 'OR SUBJECT "Ecole Polytechnique" SUBJECT "Projet de logiciel"'
            print(f"🔍 Searching for emails with subject: '{search_subject}'")
            print(f"   (Using broad IMAP search, will filter precisely after)")
        else:
            # Default: search from last 90 days
            date_since = (datetime.now() - timedelta(days=90)).strftime("%d-%b-%Y")
            search_criteria = f'SINCE {date_since}'
            print(f"🔍 Searching for emails from last 90 days")

        status, data = mail.search(None, search_criteria)

        responses = []
        automatic_responses = []
        if status == 'OK' and data[0]:
            email_nums = data[0].split()
            print(f"📧 Found {len(email_nums)} emails matching criteria")

            for num in email_nums:  # Process all matching emails
                try:
                    # Get headers first
                    typ, msg_data = mail.fetch(num, '(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])')
                    if typ != 'OK':
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])

                    # Extract sender
                    from_header = decode_header(msg.get("From", ""))
                    sender_emails = extract_emails_from_header(from_header)

                    # Skip emails from yourself
                    your_email = imap_cfg["IMAP_USER"].lower()
                    sender_emails = [email for email in sender_emails if email.lower() != your_email]
                    
                    # Filter out system emails (postmaster, mailinblack, etc.)
                    sender_emails = [email for email in sender_emails if not is_system_email(email)]

                    if sender_emails:  # Only if it's from someone else (prospect response)
                        subject = decode_header(msg.get("Subject", ""))
                        date_received = decode_header(msg.get("Date", ""))

                        # FILTER: Only keep emails with the exact campaign subject
                        # The subject should be "École Polytechnique - Projet de logiciel pour agences immobilières"
                        # We check for the key parts to handle encoding variations
                        subject_lower = subject.lower()
                        # Remove accents for comparison (handle "immobilières" vs "immobilieres")
                        subject_normalized = unicodedata.normalize('NFKD', subject_lower)
                        subject_ascii = subject_normalized.encode('ascii', 'ignore').decode('ascii')
                        
                        campaign_keywords = [
                            "ecole polytechnique",
                            "projet de logiciel",
                            "agences immobili"  # Match "immobilières" or "immobilieres"
                        ]
                        
                        # Check if subject contains all key parts of the campaign
                        is_campaign_email = all(keyword in subject_ascii for keyword in campaign_keywords)
                        
                        if not is_campaign_email:
                            # Skip this email - not related to our campaign
                            continue

                        # Try to get a bit of content to check for automatic responses
                        content_preview = ""
                        try:
                            # Fetch body preview
                            typ2, body_data = mail.fetch(num, '(BODY[TEXT]<0.1000>)')
                            if typ2 == 'OK' and body_data[0]:
                                if isinstance(body_data[0][1], bytes):
                                    content_preview = body_data[0][1].decode('utf-8', errors='ignore')[:500]
                        except:
                            pass

                        # Check if this is an automatic response
                        is_auto = is_automatic_response(subject, content_preview)

                        response_data = {
                            'sender': sender_emails[0],  # Take first sender email
                            'subject': subject,
                            'date': date_received,
                            'is_automatic': is_auto,
                            'content_preview': content_preview[:100] + "..." if len(content_preview) > 100 else content_preview
                        }

                        if is_auto:
                            automatic_responses.append(response_data)
                        else:
                            responses.append(response_data)

                except Exception as e:
                    print(f"⚠️ Error processing email {num}: {e}")
                    continue

        mail.logout()

        print(f"✅ Found {len(responses)} real responses from prospects")
        print(f"🤖 Found {len(automatic_responses)} automatic responses (filtered out)")

        # Return both real responses and automatic ones for reporting
        return responses, automatic_responses

    except Exception as e:
        print(f"❌ IMAP Error: {e}")
        print(f"🔧 Trying to connect to: {imap_cfg['IMAP_HOST']} with user: {imap_cfg['IMAP_USER'][:10]}...")
        print("💡 Tips: Check IMAP_HOST in .env (try: webmail.polytechnique.fr)")
        print("💡 Tips: Check INBOX_FOLDER in .env (default: INBOX)")
        return [], []

def load_master_contacts(csv_path):
    """Load master contacts and their response status"""
    contacts = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                email = row.get('email', '').strip().lower()
                if email:
                    contacts[email] = {
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'company_name': row.get('company_name', ''),
                        'answered': row.get('answered', 'no').lower() == 'yes',
                        'status': row.get('status', ''),
                        'notes': row.get('notes', ''),
                        'premier_envoi_date': row.get('premier_envoi_date', '')
                    }
    except Exception as e:
        print(f"❌ Error reading {csv_path}: {e}")
        return {}

    return contacts

def main():
    print("🔍 Checking received email responses...")
    print("=" * 50)

    # Load config
    imap_cfg = load_env()
    if not imap_cfg["IMAP_PASS"]:
        print("❌ No IMAP password found in .env")
        return

    # Load master contacts
    csv_path = "master_contacts_tracking.csv"
    contacts = load_master_contacts(csv_path)
    print(f"📊 Loaded {len(contacts)} contacts from {csv_path}")

    # Get received responses - search for campaign emails
    campaign_subject = "École Polytechnique - Projet de logiciel pour agences immobilières"
    print(f"📧 Connecting to {imap_cfg['IMAP_HOST']}...")
    real_responses, auto_responses = get_received_responses(imap_cfg, search_subject=campaign_subject)

    # Analyze responses - who has really responded (excluding automatic responses)
    responders_in_csv = set()
    responders_not_in_csv = set()
    response_details = []
    new_contacts_to_add = []

    for response in real_responses:
        sender_email = response['sender']
        
        if sender_email in contacts:
            # Contact exists in CSV
            if not contacts[sender_email]['answered']:
                # This is a new real response from an existing contact
                responders_in_csv.add(sender_email)
                response_details.append({
                    'email': sender_email,
                    'name': f"{contacts[sender_email]['first_name']} {contacts[sender_email]['last_name']}".strip(),
                    'company': contacts[sender_email]['company_name'],
                    'subject': response['subject'],
                    'date': response['date'],
                    'in_csv': True
                })
            # else: already marked as answered, skip
        else:
            # Contact NOT in CSV - this is a new contact who responded
            responders_not_in_csv.add(sender_email)
            new_contacts_to_add.append({
                'email': sender_email,
                'name': 'Unknown',  # Will extract from email if possible
                'company': 'Unknown',
                'subject': response['subject'],
                'date': response['date'],
                'in_csv': False
            })

    print(f"✅ Found {len(real_responses)} total real responses:")
    print(f"   • {len(responders_in_csv)} from existing contacts (not yet marked)")
    print(f"   • {len(responders_not_in_csv)} from NEW contacts (not in CSV)")

    # Find who still hasn't responded (all contacts who haven't answered)
    no_response = []
    already_responded = []

    for email_addr, contact_info in contacts.items():
        if contact_info['answered']:
            already_responded.append({
                'email': email_addr,
                'name': f"{contact_info['first_name']} {contact_info['last_name']}".strip(),
                'company': contact_info['company_name'],
                'status': contact_info['status'],
                'notes': contact_info['notes']
            })
        else:
            no_response.append({
                'email': email_addr,
                'name': f"{contact_info['first_name']} {contact_info['last_name']}".strip(),
                'company': contact_info['company_name'],
                'status': contact_info['status']
            })

    # Report
    print("\n" + "=" * 60)
    print("📈 RESPONSE ANALYSIS REPORT")
    print("=" * 60)

    print(f"\n🆕 NEW REAL RESPONSES FROM EXISTING CONTACTS ({len(response_details)}):")
    print("-" * 40)
    for response in response_details[:10]:  # Show first 10
        print(f"• {response['email']} - {response['name']} ({response['company']})")
        print(f"  📧 Subject: {response['subject']}")
        print(f"  📅 Date: {response['date']}")
    if len(response_details) > 10:
        print(f"... and {len(response_details) - 10} more")

    print(f"\n🆕 NEW CONTACTS WHO RESPONDED (NOT IN CSV) ({len(new_contacts_to_add)}):")
    print("-" * 40)
    for contact in new_contacts_to_add[:10]:  # Show first 10
        print(f"• {contact['email']}")
        print(f"  📧 Subject: {contact['subject']}")
        print(f"  📅 Date: {contact['date']}")
        print(f"  ⚠️  Will be added to CSV automatically")
    if len(new_contacts_to_add) > 10:
        print(f"... and {len(new_contacts_to_add) - 10} more")

    print(f"\n🤖 AUTOMATIC RESPONSES FILTERED OUT ({len(auto_responses)}):")
    print("-" * 40)
    for response in auto_responses[:10]:  # Show first 10
        print(f"• {response['sender']} - {response['subject']}")
        print(f"  🤖 Reason: Automatic response detected")
    if len(auto_responses) > 10:
        print(f"... and {len(auto_responses) - 10} more")

    print(f"\n✅ ALREADY MARKED AS RESPONDED ({len(already_responded)}):")
    print("-" * 40)
    for contact in already_responded[:10]:  # Show first 10
        print(f"• {contact['email']} - {contact['name']} ({contact['company']})")
        if contact['notes']:
            print(f"  📝 {contact['notes']}")
    if len(already_responded) > 10:
        print(f"... and {len(already_responded) - 10} more")

    print(f"\n❌ NO RESPONSE YET ({len(no_response)}):")
    print("-" * 40)
    for contact in no_response[:20]:  # Show first 20
        print(f"• {contact['email']} - {contact['name']} ({contact['company']}) - Status: {contact['status']}")
    if len(no_response) > 20:
        print(f"... and {len(no_response) - 20} more")

    print(f"\n📊 SUMMARY:")
    print(f"• Total contacts in CSV: {len(contacts)}")
    print(f"• Total real responses found: {len(real_responses)}")
    print(f"  - From existing contacts (to mark): {len(response_details)}")
    print(f"  - From NEW contacts (to add): {len(new_contacts_to_add)}")
    print(f"• Automatic responses filtered: {len(auto_responses)}")
    print(f"• Already marked responded: {len(already_responded)}")
    print(f"• Still no response: {len(no_response)}")

    if real_responses:
        total_responded = len(already_responded) + len(response_details) + len(new_contacts_to_add)
        total_contacts = len(contacts) + len(new_contacts_to_add)
        real_response_rate = total_responded / total_contacts * 100 if total_contacts > 0 else 0
        print(f"• Real response rate: {real_response_rate:.1f}% ({total_responded}/{total_contacts})")

    if response_details or new_contacts_to_add:
        print("\n⚠️  ACTION NEEDED:")
        if response_details:
            print("Mark existing contacts who responded:")
            for response in response_details[:5]:  # Show first 5
                print(f"  python mark_answered.py master_contacts_tracking.csv single {response['email']} --status responded --notes \"Response received\"")
            if len(response_details) > 5:
                print(f"  ... and {len(response_details) - 5} more")
        
        if new_contacts_to_add:
            print(f"\nAdd {len(new_contacts_to_add)} new contacts who responded:")
            print(f"  python auto_mark_responses.py  # Will add them automatically")

    # Save to file
    with open('response_analysis.txt', 'w', encoding='utf-8') as f:
        f.write("RESPONSE ANALYSIS REPORT\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"NEW REAL RESPONSES FROM EXISTING CONTACTS ({len(response_details)}):\n")
        f.write("-" * 40 + "\n")
        for response in response_details:
            f.write(f"• {response['email']} - {response['name']} ({response['company']})\n")
            f.write(f"  📧 Subject: {response['subject']}\n")
            f.write(f"  📅 Date: {response['date']}\n\n")

        f.write(f"NEW CONTACTS WHO RESPONDED (NOT IN CSV) ({len(new_contacts_to_add)}):\n")
        f.write("-" * 40 + "\n")
        for contact in new_contacts_to_add:
            f.write(f"• {contact['email']}\n")
            f.write(f"  📧 Subject: {contact['subject']}\n")
            f.write(f"  📅 Date: {contact['date']}\n")
            f.write(f"  ⚠️  Will be added to CSV automatically\n\n")

        f.write(f"AUTOMATIC RESPONSES FILTERED ({len(auto_responses)}):\n")
        f.write("-" * 40 + "\n")
        for response in auto_responses:
            f.write(f"• {response['sender']} - {response['subject']}\n")
            f.write(f"  🤖 Automatic response (filtered out)\n\n")

        f.write(f"ALREADY MARKED AS RESPONDED ({len(already_responded)}):\n")
        f.write("-" * 40 + "\n")
        for contact in already_responded:
            f.write(f"• {contact['email']} - {contact['name']} ({contact['company']})\n")
            if contact['notes']:
                f.write(f"  📝 {contact['notes']}\n")
            f.write("\n")

        f.write(f"NO RESPONSE YET ({len(no_response)}):\n")
        f.write("-" * 40 + "\n")
        for contact in no_response:
            f.write(f"• {contact['email']} - {contact['name']} ({contact['company']}) - Status: {contact['status']}\n")

    print("\n💾 Report saved to 'response_analysis.txt'")
    if response_details:
        print("🎯 New responses detected - mark them to avoid sending nudges!")
    else:
        print("🎯 Ready for nudge campaigns!")

if __name__ == "__main__":
    main()
