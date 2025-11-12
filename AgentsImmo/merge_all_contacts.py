#!/usr/bin/env python3
"""
Merge master_contacts_tracking.csv with all CSVs in already_contacted_immo/
Creates a complete consolidated master file with all contacts.
Preserves existing data from master (dates, status, answered) when email already exists.
"""
import csv
import os
from datetime import datetime
from collections import defaultdict

def read_csv_rows_with_dialect(csv_path):
    """Read CSV and auto-detect delimiter"""
    with open(csv_path, newline="", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t"])
        except Exception:
            class _D: delimiter = ';'
            dialect = _D()
        reader = csv.DictReader(f, delimiter=getattr(dialect, 'delimiter', ';'))
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
        return rows, dialect, fieldnames

def extract_contact_from_row(row):
    """Extract contact info from a CSV row (handles different column name variations)"""
    # Try different possible column names
    email = (row.get('email') or row.get('Email') or row.get('EMAIL') or '').strip().lower()
    if not email or '@' not in email:
        return None
    
    first_name = (row.get('first_name') or row.get('firstName') or row.get('First Name') or 
                  row.get('cleanFirstName') or row.get('fullName', '').split()[0] if row.get('fullName') else '').strip()
    
    last_name = (row.get('last_name') or row.get('lastName') or row.get('Last Name') or 
                 ' '.join(row.get('fullName', '').split()[1:]) if row.get('fullName') else '').strip()
    
    company_name = (row.get('company_name') or row.get('companyName') or row.get('Company Name') or '').strip()
    
    return {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'company_name': company_name,
    }

def load_master_contacts(master_path):
    """Load existing master contacts"""
    if not os.path.exists(master_path):
        print(f"⚠️  Master file not found: {master_path}")
        return {}
    
    contacts = {}
    rows, _, _ = read_csv_rows_with_dialect(master_path)
    
    for row in rows:
        email = (row.get('email') or '').strip().lower()
        if email and '@' in email:
            contacts[email] = {
                'email': email,
                'first_name': (row.get('first_name') or '').strip(),
                'last_name': (row.get('last_name') or '').strip(),
                'company_name': (row.get('company_name') or '').strip(),
                'premier_envoi_date': (row.get('premier_envoi_date') or '').strip(),
                'nudge1_date': (row.get('nudge1_date') or '').strip(),
                'nudge2_date': (row.get('nudge2_date') or '').strip(),
                'answered': (row.get('answered') or 'no').strip().lower(),
                'status': (row.get('status') or 'contacted').strip(),
                'notes': (row.get('notes') or '').strip(),
            }
    
    return contacts

def merge_all_contacts(master_path, source_dir, output_path):
    """Merge master with all CSVs in source_dir"""
    
    print("🔄 Loading existing master contacts...")
    contacts = load_master_contacts(master_path)
    print(f"   ✅ Loaded {len(contacts)} contacts from master")
    
    # Track stats
    new_contacts = 0
    updated_contacts = 0
    files_processed = 0
    
    # Process all CSV files in already_contacted_immo/
    print(f"\n📂 Scanning {source_dir}...")
    for root, _, files in os.walk(source_dir):
        for filename in files:
            if not filename.lower().endswith('.csv'):
                continue
            
            filepath = os.path.join(root, filename)
            files_processed += 1
            print(f"\n   Processing: {filename}")
            
            try:
                rows, _, _ = read_csv_rows_with_dialect(filepath)
                file_new = 0
                file_updated = 0
                
                for row in rows:
                    contact_data = extract_contact_from_row(row)
                    if not contact_data:
                        continue
                    
                    email = contact_data['email']
                    
                    if email not in contacts:
                        # New contact - add with default values
                        contacts[email] = {
                            'email': email,
                            'first_name': contact_data['first_name'],
                            'last_name': contact_data['last_name'],
                            'company_name': contact_data['company_name'],
                            'premier_envoi_date': datetime.now().strftime('%Y-%m-%d'),  # Default to today
                            'nudge1_date': '',
                            'nudge2_date': '',
                            'answered': 'no',
                            'status': 'contacted',
                            'notes': '',
                        }
                        new_contacts += 1
                        file_new += 1
                    else:
                        # Contact exists - update only missing fields (preserve master data)
                        existing = contacts[email]
                        if not existing['first_name'] and contact_data['first_name']:
                            existing['first_name'] = contact_data['first_name']
                        if not existing['last_name'] and contact_data['last_name']:
                            existing['last_name'] = contact_data['last_name']
                        if not existing['company_name'] and contact_data['company_name']:
                            existing['company_name'] = contact_data['company_name']
                        file_updated += 1
                
                print(f"      ✅ {file_new} new, {file_updated} existing contacts")
                
            except Exception as e:
                print(f"      ❌ Error processing {filename}: {e}")
                continue
    
    print(f"\n📊 Summary:")
    print(f"   • Files processed: {files_processed}")
    print(f"   • New contacts added: {new_contacts}")
    print(f"   • Total contacts: {len(contacts)}")
    
    # Write consolidated master file
    print(f"\n💾 Saving consolidated master to: {output_path}")
    fieldnames = ['email', 'first_name', 'last_name', 'company_name', 
                  'premier_envoi_date', 'nudge1_date', 'nudge2_date', 
                  'answered', 'status', 'notes']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for contact in sorted(contacts.values(), key=lambda x: x['email']):
            writer.writerow(contact)
    
    print(f"✅ Consolidated master saved with {len(contacts)} contacts!")
    print(f"🎯 Ready to use with check_responses.py and campaign_manager.py")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_path = os.path.join(script_dir, 'master_contacts_tracking.csv')
    source_dir = os.path.join(script_dir, 'already_contacted_immo')
    output_path = os.path.join(script_dir, 'master_contacts_tracking.csv')  # Overwrite master
    
    merge_all_contacts(master_path, source_dir, output_path)

