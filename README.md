# 🚀 Free LemList - Email Campaign Management System

Système complet de gestion de campagnes email pour prospection B2B avec **relances automatiques intelligentes**. Envoi massifs + suivi des réponses + campagnes de nurturing sur plusieurs semaines.

## 📁 Structure du projet

```
free_lemlist/
├── AgentsImmo/                    # 🏠 Campagne agents immobiliers
│   ├── script.py                  # Script principal d'envoi
│   ├── campaign_manager.py        # Gestionnaire de relances
│   ├── consolidate_contacts.py    # Consolidation contacts existants
│   ├── mark_answered.py           # Marquage réponses manuelles
│   ├── master_contacts_tracking.csv # Suivi centralisé des contacts
│   ├── template.html              # Template email initial
│   ├── template_nudge1.html       # Template relance 1 (3j après)
│   ├── template_nudge2.html       # Template relance 2 (5j après nudge1)
│   ├── agents_immo.csv            # Liste principale des prospects
│   ├── already_contacted_immo/    # Archives contacts déjà contactés
│   ├── QUICK_START.md             # Guide démarrage rapide
│   └── CAMPAIGN_README.md         # Documentation complète campagnes
├── Notaires/                      # ⚖️ Campagne notaires
│   ├── script.py                  # Script d'envoi notaires
│   ├── template.html              # Template email notaires
│   └── already_contacted_notaires/ # Archives contacts notaires
├── test_env.py                    # Test configuration SMTP
└── README.md                      # Ce fichier
```

## 🛠️ Installation & Setup

### 1. Cloner et installer

```bash
# Cloner le repo
git clone <votre-repo-github>
cd free_lemlist

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate sur Windows

# Installer dépendances
pip install python-dotenv jinja2
```

### 2. Configuration SMTP

Créer un fichier `.env` à la racine :

```bash
# Configuration SMTP (exemple Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASS=votre_mot_de_passe_app
SENDER_NAME="Valentin Henry-Léo"
REPLY_TO=votre.email@gmail.com

# Templates et contenu
VIDEO_URL="https://youtube.com/watch?v=VOTRE_VIDEO_ID"
EMAIL_SUBJECT="École Polytechnique - Projet IA immobilier"
EMAIL_SUBJECT_NUDGE1="Re: Projet IA pour agences immobilières"
EMAIL_SUBJECT_NUDGE2="Re: Dernier message - Projet IA immobilier"

# Délais campagnes (en jours)
DAYS_BEFORE_NUDGE1=3
DAYS_BEFORE_NUDGE2=5

# Email copie (optionnel)
BCC_EMAIL=backup@domaine.com
```

### 3. Test de configuration

```bash
# Tester la config SMTP
python test_env.py
python script.py --send-test votre.email@gmail.com
```

## 🎯 Utilisation - Workflow complet

### Phase 0: Récupérer la data

Allez sur lemlist (free plan) et télécharger les databases qui vous intéressent en (.csv). Ensuite foutez la dans le folder approprié (ici AgentsImmo).

### Phase 1: Envoi initial

```bash
cd AgentsImmo

# Activer venv
source ../venv/bin/activate

# Envoi avec exclusion des déjà contactés
python script.py agents_immo.csv --exclude-csv already_contacted_immo
```

### Phase 2: Consolidation & Suivi

```bash
# Créer fichier de suivi centralisé
python consolidate_contacts.py

# Le fichier master_contacts_tracking.csv est créé avec:
# - email, first_name, last_name, company_name
# - premier_envoi_date, nudge1_date, nudge2_date
# - answered, status, notes
```

### Phase 3: Campagnes de relance automatiques

```bash
# ATTENDRE 3+ jours après envoi initial

# Aperçu qui recevra la relance 1
python campaign_manager.py master_contacts_tracking.csv nudge1 --dry-run

# Envoyer relance 1 (150s = 2m30s entre chaque email)
python campaign_manager.py master_contacts_tracking.csv nudge1 --delay 150
```

```bash
# ATTENDRE 5+ jours après relance 1

# Envoyer relance 2
python campaign_manager.py master_contacts_tracking.csv nudge2 --delay 150
```

### Phase 4: Gestion des réponses

```bash
# Marquer une réponse positive
python mark_answered.py master_contacts_tracking.csv single contact@email.com \
  --answered yes \
  --status responded \
  --notes "Intéressé par démo lundi"

# Marquer comme pas intéressé
python mark_answered.py master_contacts_tracking.py single contact@email.com \
  --answered yes \
  --status not_interested
```

## 📧 Templates & Personnalisation

### Variables disponibles dans tous les templates :

- `{{ first_name }}` - Prénom du contact
- `{{ last_name }}` - Nom du contact
- `{{ company_name }}` - Nom de l'entreprise
- `{{ video_url }}` - URL de la vidéo de démo

### Templates par défaut :

| Template | Usage | Délai | Localisation |
|----------|--------|-------|--------------|
| `template.html` | Email initial | Immédiat | `AgentsImmo/template.html` |
| `template_nudge1.html` | Relance 1 | 3j après | `AgentsImmo/template_nudge1.html` |
| `template_nudge2.html` | Relance 2 | 5j après nudge1 | `AgentsImmo/template_nudge2.html` |

### Exemple de personnalisation :

```html
<!-- template_nudge1.html -->
<p>Bonjour {{ first_name }},</p>
<p>J'espère que vous allez bien. Je reviens vers vous concernant notre solution IA pour {{ company_name }}.</p>
<p>Avez-vous eu le temps de regarder la vidéo ? {{ video_url }}</p>
<p>Bien cordialement,<br>Valentin</p>
```

## 📊 Métriques & Suivi

Ouvrir `master_contacts_tracking.csv` dans Excel pour suivre :

- **Taux de réponse** : `COUNTIF(status, "responded") / COUNT(status)`
- **Progression campagnes** : Distribution des statuts
- **Timing optimal** : Analyser délais de réponse

### Commandes monitoring :

```bash
# Compter par statut
grep -o 'contacted\|nudge1_sent\|nudge2_sent\|responded\|not_interested' master_contacts_tracking.csv | sort | uniq -c

# Voir les plus récents
head -5 master_contacts_tracking.csv
```

## 🔧 Scripts disponibles

| Script | Usage | Options principales |
|--------|-------|-------------------|
| `script.py` | Envoi massifs | `--exclude-csv`, `--send-test` |
| `campaign_manager.py` | Relances automatiques | `--dry-run`, `--delay` |
| `consolidate_contacts.py` | Consolidation archives | Auto |
| `mark_answered.py` | Marquage manuel réponses | `single`, `bulk` |
| `test_env.py` | Test config SMTP | - |

## ⚠️ Sécurité & Bonnes pratiques

- **🔐 Jamais commiter `.env`** (déjà dans `.gitignore`)
- **📧 Toujours `--dry-run` avant envoi réel**
- **⏱️ Respecter les délais** entre envois (éviter spam)
- **💾 Backup** `master_contacts_tracking.csv` régulièrement
- **📊 Suivre les réponses** et mettre à jour immédiatement

## 🚀 Prochains développements

- [ ] Interface web pour gestion campagnes
- [ ] Intégration tracking ouvertures/clics
- [ ] Templates dynamiques par secteur
- [ ] API REST pour automation
- [ ] Dashboard métriques temps réel

## 📞 Support

- **Issues GitHub** pour bugs/features
- **QUICK_START.md** pour démarrage rapide
- **CAMPAIGN_README.md** pour docs complètes
