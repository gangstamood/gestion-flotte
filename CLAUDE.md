# Architecture complète - Gestion de Flotte

## Stack technique
- **Framework** : Streamlit (Python)
- **Backend** : Google Sheets API v4 via `googleapiclient`
- **Auth** : `google.oauth2.service_account` + `st.secrets`
- **PDF** : ReportLab (bons de carburant)
- **Data** : Pandas pour import/export CSV/Excel

---

## Architecture modulaire

```
gestion-flotte/
├── app.py              # Point d'entrée + config + routeur de pages
├── database.py         # Connexion Google Sheets + fonctions CRUD
├── pdf.py              # Génération PDF (bons carburant)
├── styles.py           # Thèmes CSS (THEMES dict + get_css)
├── alertes.py          # Fonctions d'alertes
├── pages/              # Modules de pages
│   ├── __init__.py
│   ├── dashboard.py    # Vue d'ensemble
│   ├── vehicules.py    # Saisie, attribution, carburant, interventions
│   ├── scooters.py     # Saisie, attribution, interventions
│   ├── engins.py       # Saisie, attribution (planning), interventions
│   └── parametres.py   # Thèmes, catégories, services, liens
├── .streamlit/
│   └── config.toml     # Config Streamlit
└── requirements.txt    # Dépendances Python
```

---

## Fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `app.py` | ~220 | Point d'entrée, auth, sidebar, routeur |
| `database.py` | ~380 | Connexion GSheets + CRUD complet |
| `pdf.py` | ~60 | Génération PDF bons carburant |
| `styles.py` | ~320 | 4 thèmes + CSS injecté |
| `alertes.py` | ~80 | Fonctions d'alertes |
| `pages/dashboard.py` | ~320 | Page dashboard |
| `pages/vehicules.py` | ~280 | Pages véhicules |
| `pages/scooters.py` | ~180 | Pages scooters |
| `pages/engins.py` | ~280 | Pages engins |
| `pages/parametres.py` | ~150 | Page paramètres |

---

## Secrets requis (`.streamlit/secrets.toml`)
```
app_password = "..."
[gcp_service_account]
type = "service_account"
project_id = "..."
...
[google_sheets]
spreadsheet_id = "..."
```

---

## Structure du code

### app.py (Point d'entrée)
- Configuration de la page
- Initialisation du thème
- Bouton hamburger JS
- Authentification
- Chargement des données
- Sidebar avec navigation
- Routeur de pages

### database.py (CRUD)
- `get_sheets_service()` — Connexion Google Sheets
- `read_sheet()` / `write_sheet()` — Opérations de base
- `_load_all_sheets()` — Chargement batch avec cache 60s
- CRUD Véhicules, Scooters, Engins
- CRUD Attributions (3 types)
- CRUD Catégories, Services, Interventions
- CRUD Carburant, Liens

### pdf.py
- `generer_pdf_bon()` — Génération PDF pour bons carburant

### styles.py
- `THEMES` — Dictionnaire de 4 thèmes
- `get_css(t)` — CSS injecté via `st.markdown()`

### alertes.py
- `verifier_alertes()` — Véhicules à retourner
- `verifier_alertes_scooters()` — Scooters à retourner
- `verifier_alertes_engins()` — Engins à retourner

---

## Data Model (15 feuilles Google Sheets)

### vehicules
| Colonne | Description |
|---------|-------------|
| immatriculation | Clé primaire (ex: AB-123-CD) |
| type | Catégorie (FK categories) |
| marque | Marque du véhicule |

### attributions
| Colonne | Description |
|---------|-------------|
| immatriculation | FK vehicules |
| service | FK services |
| date | Date sortie (JJ/MM/AAAA) |
| heure | Heure sortie (HH:MM) |
| date_retour_prevue | Date retour prévue (JJ/MM/AAAA) |
| retourne | Vide ou JJ/MM/AAAA HH:MM |

### scooters
| Colonne | Description |
|---------|-------------|
| immatriculation | Clé primaire |
| type | Catégorie (FK categories_scooters) |
| marque | Marque |

### attributions_scooters
| Colonne | Description |
|---------|-------------|
| immatriculation | FK scooters |
| service | FK services |
| date | Date sortie |
| heure | Heure sortie |
| date_retour_prevue | Date retour prévue |
| casque | Référence casque attribué |
| retourne | Vide ou datetime retour |

### engins
| Colonne | Description |
|---------|-------------|
| numero_serie | Clé primaire |
| type | Catégorie (FK categories_engins) |
| marque | Marque |

### attributions_engins
| Colonne | Description |
|---------|-------------|
| numero_serie | FK engins |
| service | FK services |
| date | Date de début (JJ/MM/AAAA) |
| date_fin | Date de fin de la période (JJ/MM/AAAA) |
| periode | Journée / Matin / Après-midi |
| retourne | Vide ou datetime retour effectif |

### categories / categories_engins / categories_scooters
| Colonne | Défauts |
|---------|---------|
| nom | Véhicules: Camion, Fourgon, Tractopelle, Tondeuse, Utilitaire, Autre |
| nom | Engins: Tractopelle, Tondeuse, Compacteur, Nacelle, Mini-pelle, Autre |
| nom | Scooters: 50cc, 125cc, Électrique, Autre |

### services
| Colonne | Défauts |
|---------|---------|
| nom | Voirie, Bâtiment, Espaces verts |

### interventions / interventions_engins / interventions_scooters
| Colonne | Description |
|---------|-------------|
| immatriculation/numero_serie | FK entité |
| type | Panne, Entretien, Réparation, Contrôle, Autre |
| date | JJ/MM/AAAA |
| heure | HH:MM |
| commentaire | Description libre |
| statut | En cours, Terminée, En attente |

### carburant
| Colonne | Description |
|---------|-------------|
| numero_bon | BC-YYYYMMDDHHmmss |
| immatriculation | FK vehicules |
| service | FK services |
| date | JJ/MM/AAAA |
| numero_carte | N° carte carburant |
| conducteur_nom / conducteur_prenom | Identité conducteur |
| type_carburant | Diesel, SP95, SP98, GPL, Électrique |
| volume | Litres |
| montant | Euros |
| notes | Optionnel |
| statut | Non saisi / Saisi |

### liens
| Colonne | Description |
|---------|-------------|
| nom | Libellé affiché sur le bouton du Dashboard |
| url | URL complète vers le tableau |

---

## Pages de l'application

| Page | Module | Fonction |
|------|--------|----------|
| Dashboard | `pages/dashboard.py` | `render()` |
| Saisir véhicule | `pages/vehicules.py` | `render_saisir()` |
| Attribuer véhicule | `pages/vehicules.py` | `render_attribuer()` |
| Bons carburant | `pages/vehicules.py` | `render_carburant()` |
| Interventions VH | `pages/vehicules.py` | `render_interventions()` |
| Saisir scooter | `pages/scooters.py` | `render_saisir()` |
| Attribuer scooter | `pages/scooters.py` | `render_attribuer()` |
| Interventions SCO | `pages/scooters.py` | `render_interventions()` |
| Saisir engin | `pages/engins.py` | `render_saisir()` |
| Attribuer engin | `pages/engins.py` | `render_attribuer()` |
| Interventions ENG | `pages/engins.py` | `render_interventions()` |
| Paramètres | `pages/parametres.py` | `render()` |

---

## Sidebar (menu catégorisé)

```
🚗 Flotte (titre)
├── 📊 Dashboard (bouton principal)
├── 🚗 Véhicules (expander)
│   ├── Saisir un véhicule
│   ├── Attribuer un véhicule
│   ├── Bons de Carburant
│   └── Pannes & Interventions
├── 🛵 Scooters (expander)
│   ├── Saisir un scooter
│   ├── Attribuer un scooter
│   └── Interventions Scooters
├── 🚜 Engins (expander)
│   ├── Saisir un engin
│   ├── Attribuer un engin
│   └── Interventions Engins
├── ⚙️ Paramètres (bouton principal)
├── ── Alertes ──
│   ├── 🚨 Véhicules à retourner
│   ├── 🚜 Engins à retourner
│   └── 🛵 Scooters à retourner
└── 🗄️ Base connectée
```

---

## Système de cache

```
Premier chargement : 1 appel batchGet (14 feuilles)
    ↓ cache 60s
Navigations suivantes : 0 appel API (instantané)
    ↓ si écriture
write_sheet() → _load_all_sheets.clear()
    ↓
Prochain rerun : 1 appel batchGet (données fraîches)
```

- `@st.cache_resource` : connexion Google Sheets (permanent)
- `@st.cache_data(ttl=60)` : données des feuilles (60s)

---

## Clés session_state
- `theme` — nom du thème actif
- `password_correct` — booléen auth
- `page` — page de navigation courante
- `dashboard_detail` — vue détail du dashboard
- `dernier_bon` — dernier bon carburant généré
- `eng_sem_offset` — décalage semaine planning engins
