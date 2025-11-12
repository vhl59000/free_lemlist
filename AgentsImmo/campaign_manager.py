#!/usr/bin/env python3
"""
Multi-stage email campaign manager
Handles: Initial contact → Nudge 1 → Nudge 2
With intelligent timing and status tracking
"""
import smtplib, ssl, csv, time, os, sys, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from jinja2 import Template
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def load_env():
    load_dotenv()
    parent_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(parent_env):
        load_dotenv(parent_env)
    return {
        "SMTP_HOST": os.getenv("SMTP_HOST"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
        "SMTP_USER": os.getenv("SMTP_USER"),
        "SMTP_PASS": os.getenv("SMTP_PASS"),
        "SENDER_NAME": os.getenv("SENDER_NAME", os.getenv("SMTP_USER")),
        "REPLY_TO": os.getenv("REPLY_TO", os.getenv("SMTP_USER")),
        "SMTP_USE_SSL": os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes"),
        "SMTP_ALLOW_INSECURE_TLS": os.getenv("SMTP_ALLOW_INSECURE_TLS", "false").lower() in ("1", "true", "yes"),
        "SMTP_DEBUG": os.getenv("SMTP_DEBUG", "false").lower() in ("1", "true", "yes"),
        "VIDEO_URL": os.getenv("VIDEO_URL", "https://www.youtube.com/watch?v=eS6VZm7rzeM"),
        "BCC_EMAIL": os.getenv("BCC_EMAIL", "valentin.henry-leo@polytechnique.edu"),
        "DAYS_BEFORE_NUDGE1": int(os.getenv("DAYS_BEFORE_NUDGE1", "3")),
        "DAYS_BEFORE_NUDGE2": int(os.getenv("DAYS_BEFORE_NUDGE2", "5")),
        "EMAIL_SUBJECT": os.getenv("EMAIL_SUBJECT", "École Polytechnique - Projet de logiciel pour agences immobilières"),
        "EMAIL_SUBJECT_NUDGE1": os.getenv("EMAIL_SUBJECT_NUDGE1", "Re: Projet IA pour agences immobilières"),
        "EMAIL_SUBJECT_NUDGE2": os.getenv("EMAIL_SUBJECT_NUDGE2", "Re: Dernier message - Projet IA immobilier"),
    }

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

def format_progress(current: int, total: int, width: int = 30) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "] 0/0 (0%)"
    filled = int(width * current / total)
    if filled > width:
        filled = width
    bar = "#" * filled + "-" * (width - filled)
    percent = int((current / total) * 100)
    return f"[{bar}] {current}/{total} ({percent}%)"

def send_email(smtp_cfg, subject, html_body, recipient):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{smtp_cfg['SENDER_NAME']} <{smtp_cfg['SMTP_USER']}>"
    msg["To"] = recipient["email"]
    msg["Reply-To"] = smtp_cfg["REPLY_TO"]
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    to_addrs = [recipient["email"]]
    bcc = (smtp_cfg.get("BCC_EMAIL") or "").strip()
    if bcc:
        to_addrs.append(bcc)

    try:
        cert_path = os.getenv("SMTP_CA_CERT", "zimbra_cert.pem")
        if os.path.exists(cert_path):
            context = ssl.create_default_context(cafile=cert_path)
            logging.info(f"Utilisation du certificat local : {cert_path}")
        else:
            context = ssl.create_default_context()
    except Exception as e:
        logging.warning(f"Impossible de charger le certificat local : {e}")
        context = ssl.create_default_context()

    if smtp_cfg.get("SMTP_ALLOW_INSECURE_TLS"):
        logging.warning("⚠️ TLS non vérifié activé : certificat auto-signé accepté")
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    try:
        if smtp_cfg.get("SMTP_USE_SSL") or smtp_cfg.get("SMTP_PORT") == 465:
            with smtplib.SMTP_SSL(smtp_cfg["SMTP_HOST"], smtp_cfg["SMTP_PORT"], context=context) as server:
                if smtp_cfg.get("SMTP_DEBUG"):
                    server.set_debuglevel(1)
                server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASS"])
                server.sendmail(smtp_cfg["SMTP_USER"], to_addrs, msg.as_string())
        else:
            with smtplib.SMTP(smtp_cfg["SMTP_HOST"], smtp_cfg["SMTP_PORT"]) as server:
                if smtp_cfg.get("SMTP_DEBUG"):
                    server.set_debuglevel(1)
                server.starttls(context=context)
                server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASS"])
                server.sendmail(smtp_cfg["SMTP_USER"], to_addrs, msg.as_string())
    except ssl.SSLError as ssl_err:
        logging.error(f"❌ Erreur SSL : {ssl_err}")
        logging.warning("Tentative de reconnexion avec contexte non vérifié...")
        insecure_context = ssl._create_unverified_context()
        with smtplib.SMTP_SSL(smtp_cfg["SMTP_HOST"], smtp_cfg["SMTP_PORT"], context=insecure_context) as server:
            server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASS"])
            server.sendmail(smtp_cfg["SMTP_USER"], to_addrs, msg.as_string())

def read_template(template_name):
    template_path = os.path.join(os.path.dirname(__file__), template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def parse_date(date_str):
    """Parse date string, return None if empty or invalid"""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
    except:
        return None

def send_nudge_campaign(csv_path, campaign_stage, delay_seconds=150, dry_run=False):
    """
    campaign_stage: 'nudge1' or 'nudge2'
    """
    cfg = load_env()
    
    # Select template and subject based on stage
    if campaign_stage == 'nudge1':
        template_file = 'template_nudge1.html'
        subject = cfg["EMAIL_SUBJECT_NUDGE1"]
        date_field = 'nudge1_date'
        required_prior_field = 'premier_envoi_date'
        days_delay = cfg["DAYS_BEFORE_NUDGE1"]
        new_status = 'nudge1_sent'
    elif campaign_stage == 'nudge2':
        template_file = 'template_nudge2.html'
        subject = cfg["EMAIL_SUBJECT_NUDGE2"]
        date_field = 'nudge2_date'
        required_prior_field = 'nudge1_date'
        days_delay = cfg["DAYS_BEFORE_NUDGE2"]
        new_status = 'nudge2_sent'
    else:
        logging.error(f"Unknown campaign stage: {campaign_stage}")
        return
    
    tpl = Template(read_template(template_file))
    rows, dialect, fieldnames = read_csv_rows_with_dialect(csv_path)
    
    # Ensure required fields exist
    for field in ['premier_envoi_date', 'nudge1_date', 'nudge2_date', 'answered', 'status']:
        if field not in fieldnames:
            fieldnames.append(field)
    
    total = len(rows)
    sent_count = 0
    
    for i, row in enumerate(rows, 1):
        email = (row.get('email') or '').strip()
        if not email:
            continue
        
        # Check if already answered
        answered = (row.get('answered') or '').strip().lower()
        if answered == 'yes':
            logging.info(f"{format_progress(i, total)} {email} a déjà répondu, saut")
            continue
        
        # Check if this stage was already sent
        if (row.get(date_field) or '').strip():
            logging.info(f"{format_progress(i, total)} {email} - {campaign_stage} déjà envoyé, saut")
            continue
        
        # Check if prior stage exists and enough time has passed
        prior_date = parse_date(row.get(required_prior_field) or '')
        if not prior_date:
            logging.info(f"{format_progress(i, total)} {email} - pas de {required_prior_field}, saut")
            continue
        
        days_since_prior = (datetime.now() - prior_date).days
        if days_since_prior < days_delay:
            logging.info(f"{format_progress(i, total)} {email} - seulement {days_since_prior} jours depuis le dernier contact (minimum {days_delay}), saut")
            continue
        
        # Ready to send!
        r = {
            'email': email,
            'first_name': (row.get('first_name') or '').strip(),
            'last_name': (row.get('last_name') or '').strip(),
            'company_name': (row.get('company_name') or '').strip(),
        }
        
        html_body = tpl.render(**r, video_url=cfg["VIDEO_URL"])
        
        if dry_run:
            logging.info(f"{format_progress(i, total)} [DRY RUN] Envoi {campaign_stage} à {email}")
            sent_count += 1
            continue
        
        try:
            send_email(cfg, subject, html_body, r)
            row[date_field] = datetime.now().strftime('%Y-%m-%d')
            row['status'] = new_status
            write_csv_rows(csv_path, rows, dialect, fieldnames)
            sent_count += 1
            logging.info(f"{format_progress(i, total)} ✅ {campaign_stage} envoyé à {email} ({r.get('first_name','')} {r.get('last_name','')})")
        except Exception as e:
            logging.error(f"[{i}] Erreur pour {email}: {e}")
        
        logging.info(f"Pause {delay_seconds}s avant le prochain…")
        time.sleep(delay_seconds)
    
    logging.info(f"\n🎯 Campaign terminée : {sent_count} emails {campaign_stage} envoyés sur {total} contacts")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-stage email campaign manager')
    parser.add_argument('csv_file', help='Path to the master contacts CSV file')
    parser.add_argument('stage', choices=['nudge1', 'nudge2'], help='Campaign stage to run')
    parser.add_argument('--delay', type=int, default=150, help='Delay in seconds between emails (default: 150 = 2m30s)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate sending without actually sending emails')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    logging.info(f"🚀 Démarrage campaign {args.stage} avec délai de {args.delay}s entre chaque email")
    if args.dry_run:
        logging.info("⚠️ MODE DRY RUN - Aucun email ne sera envoyé")
    
    send_nudge_campaign(args.csv_file, args.stage, delay_seconds=args.delay, dry_run=args.dry_run)

