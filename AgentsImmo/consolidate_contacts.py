#!/usr/bin/env python3
"""
Consolidate all already contacted CSVs into a master tracking file with new columns:
- premier_envoi_date: date of first contact
- nudge1_date: date of first nudge
- nudge2_date: date of second nudge  
- answered: yes/no (manually updated when they respond)
- status: contacted/nudge1_sent/nudge2_sent/responded/not_interested
"""
import csv
import os
from datetime import datetime
from collections import defaultdict

def read_csv_rows_with_dialect(csv_path):
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

def consolidate_already_contacted(source_dir, output_file):
    """Consolidate all CSVs in source_dir into one master tracking file"""
    
    # Dictionary to deduplicate by email
    contacts = {}
    
    # Walk through all CSV files
    for root, _, files in os.walk(source_dir):
        for filename in files:
            if not filename.lower().endswith('.csv'):
                continue
            
            filepath = os.path.join(root, filename)
            print(f"Processing: {filepath}")
            
            try:
                rows, _, _ = read_csv_rows_with_dialect(filepath)
                
                for row in rows:
                    # Extract email (handle different column names)
                    email = (row.get('email') or row.get('Email') or '').strip().lower()
                    if not email:
                        continue
                    
                    # If email not yet in our master list, add it
                    if email not in contacts:
                        # Extract key fields
                        contacts[email] = {
                            'email': email,
                            'first_name': (row.get('first_name') or row.get('firstName') or row.get('First Name') or '').strip(),
                            'last_name': (row.get('last_name') or row.get('lastName') or row.get('Last Name') or '').strip(),
                            'company_name': (row.get('company_name') or row.get('companyName') or row.get('Company Name') or '').strip(),
                            'premier_envoi_date': datetime.now().strftime('%Y-%m-%d'),  # Assume they were all sent recently
                            'nudge1_date': '',
                            'nudge2_date': '',
                            'answered': 'no',
                            'status': 'contacted',
                            'notes': '',
                        }
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                continue
    
    # Write consolidated file
    if not contacts:
        print("No contacts found!")
        return
    
    fieldnames = ['email', 'first_name', 'last_name', 'company_name', 
                  'premier_envoi_date', 'nudge1_date', 'nudge2_date', 
                  'answered', 'status', 'notes']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for contact in sorted(contacts.values(), key=lambda x: x['email']):
            writer.writerow(contact)
    
    print(f"\n✅ Consolidated {len(contacts)} unique contacts into: {output_file}")
    print(f"📧 Ready for nudge campaigns!")

if __name__ == "__main__":
    source_dir = os.path.join(os.path.dirname(__file__), 'already_contacted_immo')
    output_file = os.path.join(os.path.dirname(__file__), 'master_contacts_tracking.csv')
    
    consolidate_already_contacted(source_dir, output_file)

