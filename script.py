# send_every_5min_zimbra_notaires.py
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
    load_dotenv()
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
    }

def load_recipients(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        # Try to detect delimiter; many exports use ';'
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

def send_email(smtp_cfg, subject, html_body, recipient):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{smtp_cfg['SENDER_NAME']} <{smtp_cfg['SMTP_USER']}>"
    msg["To"] = recipient["email"]
    msg["Reply-To"] = smtp_cfg["REPLY_TO"]
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Build TLS/SSL context
    context = ssl.create_default_context()
    if smtp_cfg.get("SMTP_ALLOW_INSECURE_TLS"):
        # WARNING: Disables certificate verification. Use only when you trust the server.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    if smtp_cfg.get("SMTP_USE_SSL") or smtp_cfg.get("SMTP_PORT") == 465:
        with smtplib.SMTP_SSL(smtp_cfg["SMTP_HOST"], smtp_cfg["SMTP_PORT"], context=context) as server:
            if smtp_cfg.get("SMTP_DEBUG"):
                server.set_debuglevel(1)
            server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASS"])
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_cfg["SMTP_HOST"], smtp_cfg["SMTP_PORT"]) as server:
            if smtp_cfg.get("SMTP_DEBUG"):
                server.set_debuglevel(1)
            server.starttls(context=context)
            server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASS"])
            server.send_message(msg)

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
    recipient = {"email": to_email, "firstName": "", "lastName": "", "companyName": ""}
    send_email(cfg, subject, html_body, recipient)

def main(csv_path):
    cfg = load_env()
    subject = "École Polytechnique - Projet de logiciel pour études notariales"
    
    message_template = """
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5;">
        <p>Bonjour {{ first_name }},</p>
        <p>Je m’appelle Valentin, étudiant en dernière année à l’École Polytechnique. 
        Avec deux amis, nous développons actuellement une solution d’assistance intelligente pour les études notariales, 
        et nous serions ravis d’avoir votre retour d’expert.</p>
        <p>Notre outil permet de ne plus perdre une opportunité à cause d’un appel manqué : 
        chaque appel est automatiquement redirigé vers une conversation WhatsApp gérée par l’IA, qui :</p>
        <ul>
          <li>recueille toutes les informations nécessaires à une réservation,</li>
          <li>répond aux questions usuelles des clients, grâce à un accès aux connaissances propres à votre étude,</li>
          <li>tout en vous laissant le contrôle total sur les échanges et les réservations.</li>
        </ul>
        <p>Je vous partage une courte <a href="https://www.youtube.com/watch?v=4JHtwtUv_lk" target="_blank" rel="noopener noreferrer">vidéo démo</a> pour que ce soit plus concret.<br>
        On est très preneurs de retours experts pour avancer et on serait ravis d’en discuter avec vous si vous êtes curieux.</p>
        <p>Merci beaucoup pour votre temps et excellente journée !</p>
        <p>Bien à vous,<br><b>Valentin</b></p>
      </body>
    </html>
    """

    tpl = Template(message_template)
    for i, r in enumerate(load_recipients(csv_path), 1):
        html_body = tpl.render(**r)
        try:
            send_email(cfg, subject, html_body, r)
            logging.info(f"[{i}] Envoyé à {r['email']} ({r.get('first_name','')} {r.get('last_name','')})")
        except Exception as e:
            logging.error(f"[{i}] Erreur pour {r['email']}: {e}")

        logging.info("Pause 5 minutes avant le prochain…")
        time.sleep(300)

def send_template_to_single(email, first_name="", last_name="", company_name=""):
    cfg = load_env()
    subject = "École Polytechnique - Projet de logiciel pour études notariales"
    message_template = """
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5;">
        <p>Bonjour {{ first_name }},</p>
        <p>Je m’appelle Valentin, étudiant en dernière année à l’École Polytechnique. 
        Avec deux amis, nous développons actuellement une solution d’assistance intelligente pour les études notariales, 
        et nous serions ravis d’avoir votre retour d’expert.</p>
        <p>Notre outil permet de ne plus perdre une opportunité à cause d’un appel manqué : 
        chaque appel est automatiquement redirigé vers une conversation WhatsApp gérée par l’IA, qui :</p>
        <ul>
          <li>recueille toutes les informations nécessaires à une réservation,</li>
          <li>répond aux questions usuelles des clients, grâce à un accès aux connaissances propres à votre étude,</li>
          <li>tout en vous laissant le contrôle total sur les échanges et les réservations.</li>
        </ul>
        <p>Je vous partage une courte <a href="https://www.youtube.com/watch?v=4JHtwtUv_lk" target="_blank" rel="noopener noreferrer">vidéo démo</a> pour que ce soit plus concret.<br>
        On est très preneurs de retours experts pour avancer et on serait ravis d’en discuter avec vous si vous êtes curieux.</p>
        <p>Merci beaucoup pour votre temps et excellente journée !</p>
        <p>Bien à vous,<br><b>Valentin</b></p>
      </body>
    </html>
    """
    tpl = Template(message_template)
    html_body = tpl.render(first_name=first_name, last_name=last_name, company_name=company_name)
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
    # Test mode: send a single email with the .env parameters
    if len(sys.argv) >= 2 and sys.argv[1] == "--send-test":
        to_email = "valentin.henryleo@gmail.com"
        if len(sys.argv) >= 3:
            to_email = sys.argv[2]
        try:
            logging.info(f"Sending test email to {to_email} using .env SMTP settings…")
            send_test_email(to_email)
            logging.info("Test email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send test email: {e}")
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) >= 2 and sys.argv[1] == "--send-template":
        to_email = "valentin.henryleo@gmail.com"
        first_name = ""
        if len(sys.argv) >= 3:
            to_email = sys.argv[2]
        if len(sys.argv) >= 4:
            first_name = sys.argv[3]
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
            print("Usage: python send_every_5min_zimbra_notaires.py --send-first-from-csv <file.csv>")
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

    if len(sys.argv) != 2:
        print("Usage: python send_every_5min_zimbra_notaires.py Notaires.csv\n"
              "       python send_every_5min_zimbra_notaires.py --send-test [email]\n"
              "       python send_every_5min_zimbra_notaires.py --send-template [email] [first_name]\n"
              "       python send_every_5min_zimbra_notaires.py --send-first-from-csv <file.csv>")
        sys.exit(1)
    main(sys.argv[1])