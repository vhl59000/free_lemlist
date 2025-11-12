# 🚀 Quick Start Guide - Multi-Stage Campaign

## What Was Just Created

✅ **509 contacts** consolidated from `already_contacted_immo/` → `master_contacts_tracking.csv`  
✅ **2 nudge templates** with different messaging strategies  
✅ **Smart campaign system** with automatic timing (3 days → nudge1, +5 days → nudge2)  
✅ **Helper scripts** for marking responses

## 📅 Timeline

```
Today (Day 0):
├─ Initial contacts sent via script.py
├─ All marked in master_contacts_tracking.csv

Day 3+:
├─ Eligible for Nudge 1
└─ Run: python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150

Day 8+:
├─ Eligible for Nudge 2 (if no response to Nudge 1)
└─ Run: python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 150
```

## 🎯 Commands You'll Use

### 1. Check who's ready for nudges (dry run)
```bash
cd /Users/valentinhenryleo/free_lemlist/AgentsImmo
source venv/bin/activate

# Preview nudge1 candidates
python campaign_manager.py master_contacts_tracking.csv nudge1 --dry-run
```

### 2. Send Nudge 1 (after 3+ days)
```bash
python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150
```

### 3. Send Nudge 2 (after 5+ more days)
```bash
python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 150
```

### 4. Mark someone who responded
```bash
# Someone replied positively
python mark_answered.py master_contacts_tracking.csv single email@example.com --answered yes --status responded --notes "Wants demo next Tuesday"

# Someone replied but not interested
python mark_answered.py master_contacts_tracking.csv single email@example.com --answered yes --status not_interested
```

## 📊 Track Your Progress

Open `master_contacts_tracking.csv` in Excel/Numbers to see:
- Who you've contacted and when
- Who got nudge1 and nudge2
- Who responded (answered=yes)
- Current status of each contact

## 💡 Pro Tips

1. **Always dry-run first** before sending: `--dry-run`
2. **Adjust timing** in `.env` if needed:
   ```bash
   DAYS_BEFORE_NUDGE1=3  # Change to 4 or 5 if you want more time
   DAYS_BEFORE_NUDGE2=5  # Change to 7 for final nudge
   ```
3. **Check daily** who responded and mark them immediately
4. **Backup the CSV** before big campaigns

## 🎨 Customize Templates

Edit these files to change your messages:
- `template_nudge1.html` - Friendly reminder
- `template_nudge2.html` - Final attempt with friendly tone

Variables available: `{{ first_name }}`, `{{ last_name }}`, `{{ company_name }}`, `{{ video_url }}`

## 📈 Example Workflow

**Week 1:**
- 560 new contacts sent via `script.py` ✅

**Week 1 + 3 days:**
```bash
python campaign_manager.py master_contacts_tracking.csv nudge1 --dry-run
# Check output, then:
python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150
```
- 30 people responded → mark them!
- 530 get nudge1

**Week 1 + 8 days:**
```bash
python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 150
```
- 50 more responded total
- 480 get final nudge2

**Results:**
- Track in CSV for metrics
- Typical response rate: 15-30% across all stages

## 🚨 What About Currently Running Script?

Your current script for new contacts (`agents_immo.csv`) is still running in the background!
- It's independent from the nudge system
- New contacts will be added to that CSV with `sent=yes`
- You can consolidate them later into `master_contacts_tracking.csv` if needed

## ❓ Questions?

Read full documentation: `CAMPAIGN_README.md`

