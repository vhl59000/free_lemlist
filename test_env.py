from dotenv import load_dotenv
import os

load_dotenv()  # charge le fichier .env depuis la racine du projet

print("✅ SMTP_HOST :", os.getenv("SMTP_HOST"))
