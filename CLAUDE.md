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
├── app.py              # Point d'entrée + configuration
├── auth.py             # Authentification (check_password)
├── hamburger.py        # Bouton hamburger JS (inject_hamburger)
├── sidebar.py          # Navigation + alertes (render_sidebar)
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
| `app.py` | ~75 | Point d'entrée, config, chargement données, routeur |
| `auth.py` | ~25 | Authentification — `check_password(t)` |
| `hamburger.py` | ~75 | Bouton hamburger JS — `inject_hamburger(t)` |
| `sidebar.py` | ~80 | Navigation + alertes — `render_sidebar(t, ...)` |
| `database.py` | ~230 | Connexion GSheets + CRUD complet |
| `pdf.py` | ~45 | Génération PDF bons carburant — `generer_pdf_bon(...)` |
| `styles.py` | ~240 | 4 thèmes + CSS injecté — `THEMES`, `get_css(t)` |
| `alertes.py` | ~72 | Fonctions d'alertes |
| `pages/__init__.py` | 0 | Package Python |
| `pages/dashboard.py` | ~230 | `render_dashboard(t, ...)` |
| `pages/vehicules.py` | ~190 | `render_vehicules(page, t, ...)` — 4 sous-pages |
| `pages/scooters.py` | ~130 | `render_scooters(page, t, ...)` — 3 sous-pages |
| `pages/engins.py` | ~185 | `render_engins(page, t, ...)` — 3 sous-pages |
| `pages/parametres.py` | ~90 | `render_parametres(t, ...)` |

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
- Configuration de la page (`st.set_page_config`)
- Initialisation du thème + injection CSS
- Appel `inject_hamburger(t)`
- Appel `check_password(t)`
- Appel `init_database()` + `_load_all_sheets()`
- Chargement et dérivation des données en variables locales
- Initialisation `st.session_state` (page, dashboard_detail, eng_sem_offset)
- Appel `render_sidebar(...)`
- Routeur : dispatche vers `render_dashboard / render_vehicules / render_scooters / render_engins / render_parametres`

### auth.py
- `check_password(t)` — Authentification par mot de passe, affiche login si besoin

### hamburger.py
- `inject_hamburger(t)` — Injecte le bouton hamburger JS via `components.html`

### sidebar.py
- `render_sidebar(t, attributions, attributions_scooters, attributions_engins, services)` — Sidebar complète avec navigation et alertes

### database.py (CRUD)
- `get_sheets_service()` — Connexion Google Sheets (cached)
- `read_sheet()` / `write_sheet()` — Opérations de base
- `_load_all_sheets()` — Chargement batch avec cache 60s
- `init_database()` — Création des feuilles manquantes
- CRUD Véhicules, Scooters, Engins
- CRUD Attributions (3 types)
- CRUD Catégories, Services, Interventions
- CRUD Carburant, Liens

### pdf.py
- `generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None)` → BytesIO

### pages/dashboard.py
- `render_dashboard(t, vehicules, attributions, scooters, attributions_scooters, engins, attributions_engins, interventions, interventions_scooters, interventions_engins, services, liens)`

### pages/vehicules.py
- `render_vehicules(page, t, vehicules, attributions, categories, services, bons_carburant, interventions)` — dispatche vers 4 sous-pages

### pages/scooters.py
- `render_scooters(page, t, scooters, attributions_scooters, categories_scooters, services, interventions_scooters)` — dispatche vers 3 sous-pages

### pages/engins.py
- `render_engins(page, t, engins, attributions_engins, categories_engins, services, interventions_engins)` — dispatche vers 3 sous-pages

### pages/parametres.py
- `render_parametres(t, categories, services, categories_engins, categories_scooters, liens)`

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
| retourne | Vide ou datetime retour effectif (override date_fin) |

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
| volume | Litres (string, converti en numeric) |
| montant | Euros (string, converti en numeric) |
| notes | Optionnel |
| statut | Non saisi / Saisi |

### liens
| Colonne | Description |
|---------|-------------|
| nom | Libellé affiché sur le bouton du Dashboard |
| url | URL complète vers le tableau Excel / Google Sheets |

---

## Fonctions CRUD complètes

### Véhicules
- `get_vehicules()` → `read_sheet('vehicules')`
- `add_vehicule(immat, type_v, marque)` — anti-doublon
- `delete_vehicule(immat)`
- `get_attributions()` → `read_sheet('attributions')`
- `add_attribution(immat, service, date, heure, date_retour_prevue)`
- `retourner_vehicule(immat)` — marque la dernière attribution non retournée
- `update_attribution(idx, data)` — modification par index
- `delete_attribution(idx)` — suppression par index

### Scooters
- `get_scooters()` / `add_scooter()` / `delete_scooter()`
- `get_attributions_scooters()` / `add_attribution_scooter(immat, service, date, heure, date_retour_prevue, casque="")`
- `retourner_scooter(immat)`
- `update_attribution_scooter(idx, data)` / `delete_attribution_scooter(idx)`

### Engins
- `get_engins()` / `add_engin()` / `delete_engin()`
- `_is_engin_active_today(attr)` — True si date_debut ≤ today ≤ date_fin et non retourné
- `get_attributions_engins()` / `add_attribution_engin(num_serie, service, date_debut, date_fin, periode)`
- `retourner_engin(num_serie)` — marque retourne avec datetime actuel
- `update_attribution_engin(idx, data)` / `delete_attribution_engin(idx)`

### Catégories & Services
- `get_categories()` / `add_category(nom)` / `delete_category(nom)` — avec défauts
- `get_categories_engins()` / `add_category_engin()` / `delete_category_engin()`
- `get_categories_scooters()` / `add_category_scooter()` / `delete_category_scooter()`
- `get_services()` / `add_service(nom)` / `delete_service(nom)` — avec défauts

### Interventions
- `get_interventions()` / `add_intervention(immat, type_i, date, heure, comm, statut)`
- `get_interventions_engins()` / `add_intervention_engin(num_serie, ...)`
- `get_interventions_scooters()` / `add_intervention_scooter(immat, ...)`

### Carburant
- `get_carburant()` / `add_bon_carburant(bon)` / `update_bon_carburant(numero_bon, type_carb, volume, montant)` / `delete_bon_carburant(numero_bon)`

### Liens
- `get_liens()` / `add_lien(nom, url)` — anti-doublon sur `nom` / `delete_lien(nom)`

### Alertes
- `verifier_alertes(attributions)` — véhicules, retour <= 2 jours
- `verifier_alertes_scooters(attributions)` — scooters, retour <= 2 jours
- `verifier_alertes_engins(attributions)` — engins dont date_fin < today et non retournés

### PDF
- `generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None)` → BytesIO

---

## Pages de l'application

| Page | Clé nav | Contenu |
|------|---------|---------|
| Dashboard | 📊 Dashboard | Boutons liens Excel (si configurés), métriques, détails par type, sorties/retours du jour, retourner véhicule/scooter/engin |
| Saisir véhicule | ➕ Saisir un véhicule | Formulaire ajout + liste avec suppression |
| Attribuer véhicule | 🔧 Attribuer un véhicule | Formulaire + historique éditable |
| Bons carburant | ⛽ Bons de Carburant | Générer bon PDF + saisie retour |
| Interventions VH | 🔨 Pannes & Interventions | Déclarer + historique |
| Saisir scooter | 🛵 Saisir un scooter | Formulaire ajout + liste |
| Attribuer scooter | 🔧 Attribuer un scooter | Formulaire (avec casque) + historique éditable |
| Interventions SCO | 🔨 Interventions Scooters | Déclarer + historique |
| Saisir engin | 🚜 Saisir un engin | Formulaire ajout + liste |
| Attribuer engin | 🔧 Attribuer un engin | Planning semaine (grille HTML colorée par service, navigation ±semaine) + formulaire période (date_debut/date_fin/periode) + historique éditable |
| Interventions ENG | 🔨 Interventions Engins | Déclarer + historique |
| Paramètres | ⚙️ Paramètres | Thème + gestion catégories/services + gestion liens Excel (📎) |

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

Navigation via `st.session_state.page` + `nav_to()` callback.
Expanders ouverts auto quand page active dans la catégorie.

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
- Les fonctions CRUD utilisent `read_sheet()` non-caché pour garantir la fraîcheur lors des écritures

---

## Clés session_state
- `theme` — nom du thème actif
- `password_correct` — booléen auth
- `page` — page de navigation courante
- `dashboard_detail` — vue détail du dashboard (vehicules/scooters/engins/None)
- `dernier_bon` — dernier bon carburant généré (pour PDF)
- `eng_sem_offset` — décalage semaine planning engins

---

## Patterns de clés formulaires
- `f"edit_attr_vh_{idx}"` / `f"edit_attr_sco_{idx}"` / `f"edit_attr_eng_{idx}"` — forms édition
- `f"srv_vh_{idx}"` / `f"dr_vh_{idx}"` / `f"ds_vh_{idx}"` / `f"hs_vh_{idx}"` — champs véhicules
- `f"srv_sco_{idx}"` / `f"dr_sco_{idx}"` / `f"cq_sco_{idx}"` — champs scooters
- `f"srv_eng_{idx}"` / `f"ds_eng_{idx}"` / `f"hs_eng_{idx}"` — champs engins
- `f"del_{immat}"` / `f"del_sco_{immat}"` / `f"del_eng_{num}"` — boutons suppression entités