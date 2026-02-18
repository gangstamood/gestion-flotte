# Architecture complète - Gestion de Flotte

## Stack technique
- **Framework** : Streamlit (Python)
- **Backend** : Google Sheets API v4 via `googleapiclient`
- **Auth** : `google.oauth2.service_account` + `st.secrets`
- **PDF** : ReportLab (bons de carburant)
- **Data** : Pandas pour import/export CSV/Excel

## Fichiers
- `app.py` — Application principale (~1510 lignes)
- `styles.py` — `THEMES` dict (4 thèmes) + `get_css(t)` : tout le CSS injecté via `st.markdown()`
- `alertes.py` — `verifier_alertes()`, `verifier_alertes_scooters()` (via `_verifier_alertes_date_retour()`), `verifier_alertes_engins()`
- `.streamlit/config.toml` — Config Streamlit
- `requirements.txt` — Dépendances Python

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

## Structure du code (ordre dans app.py)

| Section | Lignes approx. | Description |
|---------|----------------|-------------|
| Imports | 1-11 | streamlit, pandas, google, reportlab, io + `styles` (THEMES, get_css) + `alertes` |
| Config page | 13 | `st.set_page_config()` |
| Thème actif | 15-18 | Init `session_state.theme` + `t = THEMES[...]` (THEMES défini dans `styles.py`) |
| CSS | 20 | `st.markdown(get_css(t))` — défini dans `styles.py` |
| Hamburger JS | 22-104 | Menu mobile via `components.html()` |
| Auth | 107-131 | `check_password()` avec `show_login()` interne |
| Google Sheets | 134-214 | Connexion, read/write, `@st.cache_resource init_database()`, batch loader |
| CRUD Véhicules | 216-274 | get/add/delete vehicules, attributions, categories |
| CRUD Services | 276-290 | get/add/delete services |
| CRUD Interventions | 292-298 | Véhicules |
| CRUD Carburant | 300-316 | Bons carburant |
| CRUD Engins | 318-382 | get/add/delete engins + attributions + catégories |
| CRUD Scooters | 384-448 | get/add/delete scooters + attributions + catégories |
| PDF | 450-492 | generer_pdf_bon() |
| Chargement données | 494-512 | Batch load via _load_all_sheets() |
| Sidebar | 514-608 | Navigation catégorisée + alertes (fonctions dans alertes.py) |
| Pages | 611-1464 | 13 pages de contenu |

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
| date | Date sortie |
| heure | Heure sortie |
| retourne | Vide ou datetime retour |

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
- `get_attributions_engins()` / `add_attribution_engin(num_serie, service, date, heure)`
- `retourner_engin(num_serie)`
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
- `get_carburant()` / `add_bon_carburant(bon)` / `update_bon_carburant(numero_bon, type_carb, volume, montant)`

### Liens
- `get_liens()` / `add_lien(nom, url)` — anti-doublon sur `nom` / `delete_lien(nom)`

### Alertes
- `verifier_alertes(attributions)` — véhicules, retour <= 2 jours
- `verifier_alertes_scooters(attributions)` — scooters, retour <= 2 jours
- `verifier_alertes_engins(attributions)` — engins, > 8h de location

### PDF
- `generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None)` → BytesIO

---

## Pages de l'application

| Page | Clé nav | Contenu |
|------|---------|---------|
| Dashboard | 📊 Dashboard | Boutons liens Excel (si configurés), métriques, détails par type, sorties/retours du jour, retourner véhicule/scooter/engin |
| Saisir véhicule | ➕ Saisir un véhicule | Formulaire ajout + liste avec suppression |
| Importer | 📥 Importer des véhicules | Upload CSV/Excel |
| Attribuer véhicule | 🔧 Attribuer un véhicule | Formulaire + historique éditable |
| Bons carburant | ⛽ Bons de Carburant | Générer bon PDF + saisie retour |
| Interventions VH | 🔨 Pannes & Interventions | Déclarer + historique |
| Saisir scooter | 🛵 Saisir un scooter | Formulaire ajout + liste |
| Attribuer scooter | 🔧 Attribuer un scooter | Formulaire (avec casque) + historique éditable |
| Interventions SCO | 🔨 Interventions Scooters | Déclarer + historique |
| Saisir engin | 🚜 Saisir un engin | Formulaire ajout + liste |
| Attribuer engin | 🔧 Attribuer un engin | Formulaire + retourner + historique éditable |
| Interventions ENG | 🔨 Interventions Engins | Déclarer + historique |
| Paramètres | ⚙️ Paramètres | Thème + gestion catégories/services + gestion liens Excel (📎) |

---

## Sidebar (menu catégorisé)

```
🚗 Flotte (titre)
├── 📊 Dashboard (bouton principal)
├── 🚗 Véhicules (expander)
│   ├── Saisir un véhicule
│   ├── Importer des véhicules
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

## Patterns de clés formulaires
- `f"edit_attr_vh_{idx}"` / `f"edit_attr_sco_{idx}"` / `f"edit_attr_eng_{idx}"` — forms édition
- `f"srv_vh_{idx}"` / `f"dr_vh_{idx}"` / `f"ds_vh_{idx}"` / `f"hs_vh_{idx}"` — champs véhicules
- `f"srv_sco_{idx}"` / `f"dr_sco_{idx}"` / `f"cq_sco_{idx}"` — champs scooters
- `f"srv_eng_{idx}"` / `f"ds_eng_{idx}"` / `f"hs_eng_{idx}"` — champs engins
- `f"del_{immat}"` / `f"del_sco_{immat}"` / `f"del_eng_{num}"` — boutons suppression entités
