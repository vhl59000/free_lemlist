import smtplib, ssl, csv, time, os, sys, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from jinja2 import Template

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def load_env():
    # Load env from campaign folder and fallback to parent .env
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
        "EMAIL_SUBJECT": os.getenv("EMAIL_SUBJECT", "École Polytechnique - Projet de logiciel pour études notariales"),
        "VIDEO_URL": os.getenv("VIDEO_URL", "https://www.youtube.com/watch?v=4JHtwtUv_lk"),
        "BCC_EMAIL": os.getenv("BCC_EMAIL", "valentin.henry-leo@polytechnique.edu"),
        "SEND_DELAY_SECONDS": int(os.getenv("SEND_DELAY_SECONDS", 300)),
    }

def load_recipients(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t"])
        except Exception:
            class _D: delimiter = ';'
            dialect = _D()
        reader = csv.DictReader(f, delimiter=getattr(dialect, 'delimiter', ';'))
        for row in reader:
            if row.get("email"):
                first_name = (row.get("first_name") or row.get("firstName") or "").strip()
                last_name = (row.get("last_name") or row.get("lastName") or "").strip()
                company_name = (row.get("company_name") or row.get("companyName") or "").strip()
                yield {
                    "email": row["email"].strip(),
                    "first_name": first_name,
                    "last_name": last_name,
                    "company_name": company_name,
                }

def load_recipients_list(csv_path):
    return list(load_recipients(csv_path))

def format_progress(current: int, total: int, width: int = 30) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "] 0/0 (0%)"
    filled = int(width * current / total)
    if filled > width:
        filled = width
    bar = "#" * filled + "-" * (width - filled)
    percent = int((current / total) * 100)
    return f"[{bar}] {current}/{total} ({percent}%)"

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
    # Ensure stable header order
    delimiter = getattr(dialect, 'delimiter', ';')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def load_exclusion_set(path):
    excluded = set()
    if not path or not os.path.exists(path):
        return excluded
    def add_from_csv(csv_file):
        try:
            rows, _, _ = read_csv_rows_with_dialect(csv_file)
        except Exception:
            return
        for row in rows:
            email = (row.get('email') or '').strip().lower()
            if email:
                excluded.add(email)
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for name in files:
                if name.lower().endswith('.csv'):
                    add_from_csv(os.path.join(root, name))
    else:
        add_from_csv(path)
    return excluded

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

    context = ssl.create_default_context()
    if smtp_cfg.get("SMTP_ALLOW_INSECURE_TLS"):
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

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

def read_template_html():
    template_path = os.path.join(os.path.dirname(__file__), 'template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def mask_secret(secret, visible=2):
    if not secret:
        return ""
    if len(secret) <= visible * 2:
        return "*" * len(secret)
    return f"{secret[:visible]}{'*' * (len(secret) - (visible * 2))}{secret[-visible:]}"

def send_test_email(to_email):
    cfg = load_env()
    subject = "SMTP .env parameters check"
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5;">
        <h3>Loaded SMTP configuration</h3>
        <ul>
          <li><b>SMTP_HOST</b>: {cfg.get('SMTP_HOST') or ''}</li>
          <li><b>SMTP_PORT</b>: {cfg.get('SMTP_PORT') or ''}</li>
          <li><b>SMTP_USER</b>: {cfg.get('SMTP_USER') or ''}</li>
          <li><b>SMTP_PASS</b>: {mask_secret(cfg.get('SMTP_PASS'))}</li>
          <li><b>SENDER_NAME</b>: {cfg.get('SENDER_NAME') or ''}</li>
          <li><b>REPLY_TO</b>: {cfg.get('REPLY_TO') or ''}</li>
        </ul>
        <p>If you received this email, SMTP connectivity and credentials worked.</p>
      </body>
    </html>
    """
    recipient = {"email": to_email, "first_name": "", "last_name": "", "company_name": ""}
    send_email(cfg, subject, html_body, recipient)

def main(csv_path, exclude_csv=None):
    cfg = load_env()
    subject = cfg["EMAIL_SUBJECT"]
    tpl = Template(read_template_html())

    # Load full CSV to allow in-place marking of sent rows
    rows, dialect, fieldnames = read_csv_rows_with_dialect(csv_path)
    if 'sent' not in fieldnames:
        fieldnames.append('sent')

    # Build exclusion set of already-contacted emails
    excluded = load_exclusion_set(exclude_csv)

    total = len(rows)
    for i, row in enumerate(rows, 1):
        email_value = (row.get('email') or '').strip()
        if not email_value:
            logging.warning(f"{format_progress(i, total)} Ligne sans email: saut de l'envoi")
            continue
        if email_value.lower() in excluded:
            logging.info(f"{format_progress(i, total)} Email dans la liste exclue: {email_value}, saut")
            continue
        # Skip already sent rows
        if (row.get('sent') or '').strip().lower() == 'yes':
            logging.info(f"{format_progress(i, total)} Déjà marqué envoyé: {email_value}, saut")
            continue

        r = {
            'email': email_value,
            'first_name': (row.get('first_name') or row.get('firstName') or '').strip(),
            'last_name': (row.get('last_name') or row.get('lastName') or '').strip(),
            'company_name': (row.get('company_name') or row.get('companyName') or '').strip(),
        }
        html_body = tpl.render(**r, video_url=cfg["VIDEO_URL"])
        try:
            send_email(cfg, subject, html_body, r)
            row['sent'] = 'yes'
            write_csv_rows(csv_path, rows, dialect, fieldnames)
            logging.info(f"{format_progress(i, total)} Envoyé à {r['email']} ({r.get('first_name','')} {r.get('last_name','')})")
        except Exception as e:
            logging.error(f"[{i}] Erreur pour {email_value}: {e}")

        delay = cfg.get("SEND_DELAY_SECONDS", 300)
        logging.info(f"Pause {int(delay/60)} minutes avant le prochain…")
        time.sleep(delay)

def send_template_to_single(email, first_name="", last_name="", company_name=""):
    cfg = load_env()
    subject = cfg["EMAIL_SUBJECT"]
    tpl = Template(read_template_html())
    if not (email or "").strip():
        logging.warning("Skip send: empty email provided to send_template_to_single")
        return
    html_body = tpl.render(first_name=first_name, last_name=last_name, company_name=company_name, video_url=cfg["VIDEO_URL"])
    recipient = {"email": email, "first_name": first_name, "last_name": last_name, "company_name": company_name}
    send_email(cfg, subject, html_body, recipient)

def send_first_from_csv(csv_path):
    for r in load_recipients(csv_path):
        email = r.get('email', '').strip()
        if not email:
            continue
        send_template_to_single(
            email,
            first_name=r.get('first_name', ''),
            last_name=r.get('last_name', ''),
            company_name=r.get('company_name', ''),
        )
        return email, r.get('first_name', '')
    raise RuntimeError('No valid recipient row found in CSV')

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--send-test":
        to_email = ""
        if len(sys.argv) >= 3:
            to_email = sys.argv[2]
        if not to_email:
            print("Usage: python script.py --send-test <email>")
            sys.exit(1)
        try:
            logging.info(f"Sending test email to {to_email} using .env SMTP settings…")
            send_test_email(to_email)
            logging.info("Test email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send test email: {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) >= 2 and sys.argv[1] == "--send-template":
        to_email = ""
        first_name = ""
        if len(sys.argv) >= 3:
            to_email = sys.argv[2]
        if len(sys.argv) >= 4:
            first_name = sys.argv[3]
        if not to_email:
            print("Usage: python script.py --send-template <email> [first_name]")
            sys.exit(1)
        try:
            logging.info(f"Sending template email to {to_email}…")
            send_template_to_single(to_email, first_name=first_name)
            logging.info("Template email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send template email: {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) >= 2 and sys.argv[1] == "--send-first-from-csv":
        if len(sys.argv) < 3:
            print("Usage: python script.py --send-first-from-csv <file.csv>")
            sys.exit(1)
        csv_path = sys.argv[2]
        try:
            logging.info(f"Sending template to first row in {csv_path}…")
            email, first_name = send_first_from_csv(csv_path)
            logging.info(f"Template email sent successfully to {email} (first_name={first_name}).")
        except Exception as e:
            logging.error(f"Failed to send from CSV: {e}")
            sys.exit(1)
        sys.exit(0)

    # Support optional exclusion list: --exclude-csv <path>
    exclude_csv = None
    args = [a for a in sys.argv[1:] if a]
    if len(args) >= 1 and args[0] not in ("--send-test", "--send-template", "--send-first-from-csv"):
        # positional run: script.py <csv> [--exclude-csv <file>]
        csv_pos = args[0]
        i = 1
        while i < len(args):
            if args[i] == "--exclude-csv" and i + 1 < len(args):
                exclude_csv = args[i+1]
                i += 2
            else:
                i += 1
        main(csv_pos, exclude_csv=exclude_csv)
        sys.exit(0)

    print("Usage: python script.py Notaires.csv [--exclude-csv already_sent.csv]\n"
          "       python script.py --send-test <email>\n"
          "       python script.py --send-template <email> [first_name]\n"
          "       python script.py --send-first-from-csv <file.csv>")
    sys.exit(1)


