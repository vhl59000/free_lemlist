#!/usr/bin/env python3
"""
Automatically mark all found responses and add new contacts to master CSV
"""
import csv
import os
import subprocess
import sys
from datetime import datetime

def load_master_contacts(csv_path):
    """Load master contacts"""
    contacts = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                email = row.get('email', '').strip().lower()
                if email:
                    contacts[email] = row
    except Exception as e:
        print(f"❌ Error reading {csv_path}: {e}")
        return {}

    return contacts

def save_master_contacts(csv_path, contacts):
    """Save updated contacts to CSV"""
    if not contacts:
        return

    # Get fieldnames from first contact
    fieldnames = list(contacts[next(iter(contacts))].keys())

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for contact in contacts.values():
                writer.writerow(contact)
        print(f"💾 Saved {len(contacts)} contacts to {csv_path}")
    except Exception as e:
        print(f"❌ Error saving {csv_path}: {e}")

def auto_mark_responses(response_file="response_analysis.txt"):
    """Automatically mark all responses found in the analysis file"""

    # Read the response analysis file
    responses_to_mark = []
    new_contacts_to_add = []

    try:
        with open(response_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the section with new responses from existing contacts
        in_existing_responses = False
        in_new_contacts = False
        
        for line in lines:
            line = line.strip()

            if "NEW REAL RESPONSES FROM EXISTING CONTACTS" in line:
                in_existing_responses = True
                in_new_contacts = False
                continue
            elif "NEW CONTACTS WHO RESPONDED" in line:
                in_existing_responses = False
                in_new_contacts = True
                continue
            elif "ALREADY MARKED" in line or "AUTOMATIC RESPONSES" in line:
                in_existing_responses = False
                in_new_contacts = False
                continue

            if in_existing_responses and line.startswith("• "):
                # Extract email from line like: "• email@domain.com - Name (Company)"
                try:
                    email_part = line.split(" - ")[0].replace("• ", "").strip()
                    responses_to_mark.append(email_part)
                except:
                    continue
            
            if in_new_contacts and line.startswith("• "):
                # Extract email from new contacts section
                try:
                    email_part = line.split(" - ")[0].replace("• ", "").strip()
                    if email_part and "@" in email_part:
                        new_contacts_to_add.append(email_part)
                except:
                    continue

    except FileNotFoundError:
        print(f"❌ {response_file} not found. Run check_responses.py first!")
        return
    except Exception as e:
        print(f"❌ Error reading {response_file}: {e}")
        return

    if not responses_to_mark and not new_contacts_to_add:
        print("❌ No responses found to mark")
        return

    print(f"🎯 Found {len(responses_to_mark)} responses to mark from existing contacts")
    print(f"🆕 Found {len(new_contacts_to_add)} new contacts to add")

    # Load current contacts
    csv_path = "master_contacts_tracking.csv"
    contacts = load_master_contacts(csv_path)
    print(f"📊 Loaded {len(contacts)} existing contacts")

    # Mark responses from existing contacts
    marked_count = 0
    for email in responses_to_mark:
        if email in contacts:
            # Update existing contact
            contacts[email]['answered'] = 'yes'
            contacts[email]['status'] = 'responded'
            if not contacts[email].get('notes'):
                contacts[email]['notes'] = 'Auto-marked from email response'
            marked_count += 1
            print(f"✅ Marked existing contact: {email}")
        else:
            print(f"⚠️  Warning: {email} not found in CSV (should not happen)")

    # Add new contacts who responded
    added_count = 0
    for email in new_contacts_to_add:
        if email not in contacts:
            # This is a new contact that responded but wasn't in our list
            new_contact = {
                'email': email,
                'first_name': 'Unknown',  # We'll extract from email if possible
                'last_name': 'Unknown',
                'company_name': 'Unknown',
                'premier_envoi_date': datetime.now().strftime('%Y-%m-%d'),
                'nudge1_date': '',
                'nudge2_date': '',
                'answered': 'yes',
                'status': 'responded',
                'notes': 'Added automatically from email response'
            }

            # Try to extract name from email if it's a common format
            email_parts = email.split('@')[0].split('.')
            if len(email_parts) >= 2:
                new_contact['first_name'] = email_parts[0].capitalize()
                new_contact['last_name'] = email_parts[1].capitalize()

            contacts[email] = new_contact
            added_count += 1
            print(f"🆕 Added new contact: {email}")
        else:
            print(f"⚠️  Warning: {email} already in CSV (marking as responded)")
            contacts[email]['answered'] = 'yes'
            contacts[email]['status'] = 'responded'

    # Save updated contacts
    save_master_contacts(csv_path, contacts)

    print("\n🎉 SUMMARY:")
    print(f"   • Marked {marked_count} existing contacts as responded")
    print(f"   • Added {added_count} new contacts who responded")
    print(f"   • Total contacts now: {len(contacts)}")

    if added_count > 0:
        print("\n🆕 NEW CONTACTS ADDED:")
        for email in new_contacts_to_add:
            if email in contacts:
                contact = contacts[email]
                print(f"   • {email} - {contact['first_name']} {contact['last_name']}")

    print("\n✅ All responses have been marked and new contacts added!")
    print("🚀 Ready to run nudges on remaining contacts!")

if __name__ == "__main__":
    auto_mark_responses()
