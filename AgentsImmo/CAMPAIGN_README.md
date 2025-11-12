# 📧 Multi-Stage Email Campaign System

Complete system for managing email campaigns with automatic follow-ups (nudges).

## 📁 Files Overview

- **`master_contacts_tracking.csv`** - Main tracking file with all contacts and their status
- **`campaign_manager.py`** - Main script for sending nudge campaigns
- **`consolidate_contacts.py`** - One-time script to consolidate old contacts
- **`mark_answered.py`** - Helper to mark contacts as answered
- **`template.html`** - Initial email template
- **`template_nudge1.html`** - First follow-up template
- **`template_nudge2.html`** - Second follow-up template

## 🎯 Campaign Flow

```
Initial Contact (from script.py with agents_immo.csv)
    ↓ (Wait 3 days, no response)
Nudge 1 (campaign_manager.py nudge1)
    ↓ (Wait 5 days, no response)
Nudge 2 (campaign_manager.py nudge2)
    ↓
Done or Responded
```

## 📊 CSV Columns Explained

- **`email`** - Contact email
- **`first_name`**, **`last_name`**, **`company_name`** - Contact details
- **`premier_envoi_date`** - Date of initial contact (YYYY-MM-DD)
- **`nudge1_date`** - Date of first nudge (YYYY-MM-DD)
- **`nudge2_date`** - Date of second nudge (YYYY-MM-DD)
- **`answered`** - yes/no (you update this manually when someone responds)
- **`status`** - contacted/nudge1_sent/nudge2_sent/responded/not_interested
- **`notes`** - Free text for your notes

## 🚀 Usage

### 1. Initial Setup (One Time)

Consolidate all previously contacted people:

```bash
cd /Users/valentinhenryleo/free_lemlist/AgentsImmo
source venv/bin/activate
python consolidate_contacts.py
```

This creates `master_contacts_tracking.csv` with 509 contacts.

### 2. Send First Nudge

After 3+ days from initial contact, send first nudge:

```bash
# Dry run first (to see who would receive it)
python campaign_manager.py master_contacts_tracking.csv nudge1 --dry-run

# Actually send
python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150
```

The script will:
- ✅ Only send to contacts where `premier_envoi_date` exists
- ✅ Only send if 3+ days have passed
- ✅ Skip if `answered=yes`
- ✅ Skip if already sent (nudge1_date exists)
- ✅ Wait 150 seconds (2m30s) between each email

### 3. Send Second Nudge

After 5+ days from first nudge:

```bash
python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 150
```

Same logic as nudge1, but requires `nudge1_date` to exist.

### 4. Mark Responses

When someone responds:

```bash
# Single contact
python mark_answered.py master_contacts_tracking.csv single email@example.com --answered yes --status responded --notes "Interested in demo"

# Mark as not interested
python mark_answered.py master_contacts_tracking.csv single email@example.com --answered yes --status not_interested

# Bulk update from file
python mark_answered.py master_contacts_tracking.csv bulk not_interested_emails.txt
```

## ⚙️ Configuration (.env)

Add these to your `.env` file:

```bash
# Campaign timing
DAYS_BEFORE_NUDGE1=3    # Wait 3 days before first nudge
DAYS_BEFORE_NUDGE2=5    # Wait 5 days before second nudge

# Email subjects
EMAIL_SUBJECT="École Polytechnique - Projet de logiciel pour agences immobilières"
EMAIL_SUBJECT_NUDGE1="Re: Projet IA pour agences immobilières"
EMAIL_SUBJECT_NUDGE2="Re: Dernier message - Projet IA immobilier"

# Video URL
VIDEO_URL="https://www.youtube.com/watch?v=eS6VZm7rzeM"
```

## 📈 Best Practices

1. **Always dry-run first**: Use `--dry-run` to see who will receive emails
2. **Monitor responses**: Regularly update `answered=yes` for people who reply
3. **Adjust timing**: Change `DAYS_BEFORE_NUDGE*` in `.env` based on response rates
4. **Backup**: Keep backups of `master_contacts_tracking.csv`
5. **Track metrics**: Export to Excel to analyze response rates by stage

## 🔍 Quick Commands

```bash
# Check who's ready for nudge1 (dry run)
python campaign_manager.py master_contacts_tracking.csv nudge1 --dry-run

# Send nudge1 with 2m30s delay
python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150

# Send nudge2 with 5m delay
python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 300

# Mark someone as responded
python mark_answered.py master_contacts_tracking.csv single their@email.com --answered yes --status responded

# View progress in CSV (count by status)
grep -o 'contacted\|nudge1_sent\|nudge2_sent\|responded' master_contacts_tracking.csv | sort | uniq -c
```

## 📝 Example Workflow

**Week 1:**
- Initial campaign runs with `script.py` → 50 contacts reached

**Week 1 + 3 days:**
```bash
python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150
```
- 5 people responded → mark them: `python mark_answered.py ... single email@... --answered yes`
- 45 people get nudge1

**Week 1 + 8 days:**
```bash
python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 150
```
- 8 more responded → mark them
- 37 people get final nudge2

**Results:**
- 13/50 responded (26% response rate)
- Track in CSV for future analysis

## 🎨 Customizing Templates

Edit these files to change email content:
- `template_nudge1.html` - First follow-up (friendly reminder)
- `template_nudge2.html` - Last follow-up (final attempt)

Variables available: `{{ first_name }}`, `{{ last_name }}`, `{{ company_name }}`, `{{ video_url }}`

## 🐛 Troubleshooting

**"No contacts eligible for nudge"**
- Check dates in CSV (format: YYYY-MM-DD)
- Verify enough days have passed
- Ensure `answered != yes`

**"SSL Error"**
- Normal, script automatically retries with insecure context
- Contact still gets sent successfully

**Want to re-send to someone**
- Clear their `nudge1_date` or `nudge2_date` in the CSV

