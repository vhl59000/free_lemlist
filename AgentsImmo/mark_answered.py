#!/usr/bin/env python3
"""
Helper script to mark contacts as answered or update their status
Usage: python mark_answered.py master_contacts_tracking.csv email@example.com --answered yes
"""
import csv
import sys
import os

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

def write_csv_rows(csv_path, rows, dialect, fieldnames):
    delimiter = getattr(dialect, 'delimiter', ';')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def mark_answered(csv_path, email, answered='yes', status=None, notes=None):
    """Mark a contact as answered/not interested"""
    rows, dialect, fieldnames = read_csv_rows_with_dialect(csv_path)
    
    email = email.strip().lower()
    found = False
    
    for row in rows:
        row_email = (row.get('email') or '').strip().lower()
        if row_email == email:
            found = True
            row['answered'] = answered
            if status:
                row['status'] = status
            if notes:
                row['notes'] = notes
            print(f"✅ Updated {email}:")
            print(f"   - answered: {answered}")
            if status:
                print(f"   - status: {status}")
            if notes:
                print(f"   - notes: {notes}")
            break
    
    if not found:
        print(f"❌ Email not found: {email}")
        return False
    
    write_csv_rows(csv_path, rows, dialect, fieldnames)
    print(f"💾 Saved to {csv_path}")
    return True

def bulk_mark_not_interested(csv_path, email_list_file):
    """Mark multiple emails as not interested from a file (one email per line)"""
    with open(email_list_file, 'r') as f:
        emails = [line.strip() for line in f if line.strip()]
    
    count = 0
    for email in emails:
        if mark_answered(csv_path, email, answered='yes', status='not_interested'):
            count += 1
    
    print(f"\n🎯 Marked {count}/{len(emails)} contacts as not interested")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Mark contacts as answered or update status')
    parser.add_argument('csv_file', help='Path to master_contacts_tracking.csv')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Single email command
    single_parser = subparsers.add_parser('single', help='Mark a single email')
    single_parser.add_argument('email', help='Email address to update')
    single_parser.add_argument('--answered', choices=['yes', 'no'], default='yes', help='Set answered status')
    single_parser.add_argument('--status', help='Set status (responded/not_interested/qualified)')
    single_parser.add_argument('--notes', help='Add notes')
    
    # Bulk command
    bulk_parser = subparsers.add_parser('bulk', help='Mark multiple emails from file')
    bulk_parser.add_argument('email_list', help='File with emails (one per line)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    if args.command == 'single':
        mark_answered(args.csv_file, args.email, args.answered, args.status, args.notes)
    elif args.command == 'bulk':
        bulk_mark_not_interested(args.csv_file, args.email_list)
    else:
        parser.print_help()

