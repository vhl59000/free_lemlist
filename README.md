# Free LemList - Email Campaign Management

Système de gestion de campagnes email pour prospection B2B avec relances automatiques.

## Structure du projet

- `AgentsImmo/` - Campagne pour agents immobiliers
- `Notaires/` - Campagne pour notaires
- Scripts Python pour envoi email, consolidation de contacts, et campagnes de relance

## Installation

```bash
# Cloner le repo
git clone <votre-repo-github>
cd free_lemlist

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer dépendances
pip install python-dotenv jinja2
```

## Configuration

Créer un fichier `.env` à la racine avec vos paramètres SMTP:

```bash
SMTP_HOST=smtp.exemple.com
SMTP_PORT=587
SMTP_USER=votre.email@domaine.com
SMTP_PASS=votre_mot_de_passe
SENDER_NAME="Votre Nom"
VIDEO_URL="https://youtube.com/watch?v=..."
```

## Utilisation

Voir les guides dans chaque dossier (`QUICK_START.md`, `CAMPAIGN_README.md`).
