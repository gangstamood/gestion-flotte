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
├── app.py                        # Point d'entrée + configuration
├── auth.py                       # Authentification (check_password)
├── hamburger.py                  # Bouton hamburger JS (inject_hamburger)
├── sidebar.py                    # Navigation + alertes (render_sidebar)
├── database.py                   # Connexion Google Sheets + fonctions CRUD
├── pdf.py                        # Génération PDF (bons carburant)
├── styles.py                     # Thèmes CSS (THEMES dict + get_css)
├── alertes.py                    # Fonctions d'alertes
├── import_wlg.py                 # Script import Excel → GSheets (engins WLG26)
├── pages/
│   ├── __init__.py
│   ├── dashboard.py              # Vue d'ensemble
│   ├── vehicules.py              # Saisie, attribution, carburant, interventions
│   ├── scooters.py               # Saisie, attribution, interventions
│   ├── engins.py                 # Saisie, attribution (planning), interventions
│   ├── golfettes.py              # Saisie, attribution (planning), interventions
│   ├── distribution_clefs.py     # Distribution clés toutes catégories
│   ├── planning_wlg.py           # Planning engins WLG26 (rush + semaine)
│   ├── planning_golfettes_wlg.py # Planning golfettes WLG26
│   ├── interventions_wlg.py      # Interventions WLG26 (engins + golfettes)
│   └── parametres.py             # Thèmes, catégories, services, liens
├── .streamlit/
│   └── config.toml               # Config Streamlit
└── requirements.txt              # Dépendances Python
```

---

## Fichiers

| Fichier | Description |
|---------|-------------|
| `app.py` | Point d'entrée, config, chargement données, routeur |
| `auth.py` | Authentification — `check_password(t)` |
| `hamburger.py` | Bouton hamburger JS — `inject_hamburger(t)` |
| `sidebar.py` | Navigation + alertes — `render_sidebar(t, ...)` |
| `database.py` | Connexion GSheets + CRUD complet (toutes entités) |
| `pdf.py` | Génération PDF bons carburant — `generer_pdf_bon(...)` |
| `styles.py` | 4 thèmes + CSS injecté — `THEMES`, `get_css(t)` |
| `alertes.py` | Fonctions d'alertes (véhicules, scooters, engins, golfettes) |
| `import_wlg.py` | Import Excel WLG26 → GSheets (standalone, utilise .venv) |
| `pages/dashboard.py` | `render_dashboard(t, ...)` |
| `pages/vehicules.py` | `render_vehicules(page, t, ...)` — 4 sous-pages |
| `pages/scooters.py` | `render_scooters(page, t, ...)` — 3 sous-pages |
| `pages/engins.py` | `render_engins(page, t, ...)` — 4 sous-pages |
| `pages/golfettes.py` | `render_golfettes(page, t, ...)` — 4 sous-pages |
| `pages/distribution_clefs.py` | `render_distribution_clefs(t, engins, vehicules, scooters, golfettes)` |
| `pages/planning_wlg.py` | `render_planning_wlg(t, engins, attributions_engins)` |
| `pages/planning_golfettes_wlg.py` | `render_planning_golfettes_wlg(t, golfettes, attributions_golfettes)` |
| `pages/interventions_wlg.py` | `render_interventions_wlg(t, engins, golfettes, interventions_engins, interventions_golfettes)` |
| `pages/parametres.py` | `render_parametres(t, categories, services, categories_engins, categories_scooters, categories_golfettes, liens)` |

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
- Appel `inject_hamburger(t)` + `check_password(t)`
- Appel `init_database()` + `_load_all_sheets()`
- Chargement et dérivation des données en variables locales (toutes entités + golfettes + distribution_clefs)
- Initialisation `st.session_state` (page, dashboard_detail, eng_sem_offset, wlg_sem_offset, wlg_golf_sem_offset, golf_sem_offset, _fk)
- Appel `render_sidebar(...)`
- Routeur : dispatche vers toutes les pages selon `st.session_state.page`

### database.py (CRUD)
- `get_sheets_service()` — Connexion Google Sheets (cached)
- `read_sheet()` / `write_sheet()` — Opérations de base
- `_load_all_sheets()` — Chargement batch avec cache 60s (toutes les feuilles)
- `init_database()` — Création des feuilles manquantes
- CRUD Véhicules, Scooters, Engins, **Golfettes**
- CRUD Attributions (4 types : vehicules, scooters, engins, golfettes)
- CRUD Catégories (4 types), Services, Interventions (4 types)
- CRUD Carburant, Liens
- **CRUD Distribution Clefs** : `get_distribution_clefs()`, `add_distribution_clef(categorie, identifiant, nom, commentaire)`, `retour_clef(idx)`

### alertes.py
- `verifier_alertes(attributions)` — véhicules, retour <= 2 jours
- `verifier_alertes_scooters(attributions)` — scooters, retour <= 2 jours
- `verifier_alertes_engins(attributions)` — engins dont date_fin < today et non retournés
- `verifier_alertes_golfettes(attributions)` — golfettes dont date_fin < today et non retournées

### import_wlg.py (script standalone)
- Lit `PLANNING ENGINS WLG26 EN COURS.xlsx` depuis `/Users/alan/Downloads/`
- Filtre regex `^[CTN]\d+$` (C=chariots, T=télescopiques, N=nacelles ; exclut cuves et tire-palles)
- Marque construction :
  - Chariots : `f"{taille} · {fourches}"` (longues/courtes) ou juste taille
  - Nacelles : `f"{taille} · {subtype}"` (4RM/BOOM) ou juste taille
  - Télescopiques : taille uniquement
- Met à jour les engins existants (marque) + ajoute les nouveaux
- Usage : `.venv/bin/python3 import_wlg.py`

### pages/planning_wlg.py
- `_is_wlg(num)` — regex `^[CTN]\d+$`
- `_get_zone_for_day(num_serie, day, attributions)` — "most specific attribution wins" (plus courte durée de date range)
- `_clef_status(num_serie, clefs)` — (en_circulation, entry, idx) pour categorie='engin'
- Distribution : selectbox hors form → checkbox "⚠️ Confirmer la mise en circulation anticipée" si engin inactif → form nom + commentaire
- Sections : clés en circulation → distribuer → tableau statut groupé (C/T/N) → planning semaine → ajuster (expander)

### pages/planning_golfettes_wlg.py
- Même structure que planning_wlg.py mais pour golfettes (pas de filtre regex, toutes sont WLG)
- categorie='golfette' pour `add_distribution_clef`

### pages/interventions_wlg.py
- Deux onglets : 🚜 Engins / ⛳ Golfettes
- Filtre WLG engins : `_is_wlg(num)` regex `^[CTN]\d+$`
- `_render_liste_interventions` : "En cours" inline, autres dans expander
- `_render_card` : carte colorée avec border-left selon statut

---

## Data Model (Google Sheets)

### vehicules
| immatriculation | Clé primaire (ex: AB-123-CD) |
| type | FK categories |
| marque | Marque du véhicule |

### attributions
| immatriculation | FK vehicules |
| service | FK services |
| date | Date sortie (JJ/MM/AAAA) |
| heure | Heure sortie (HH:MM) |
| date_retour_prevue | Date retour prévue (JJ/MM/AAAA) |
| retourne | Vide ou JJ/MM/AAAA HH:MM |

### scooters / attributions_scooters
- Même modèle que vehicules, avec champ `casque` dans attributions_scooters

### engins
| numero_serie | Clé primaire (ex: C6, T3, N2) |
| type | FK categories_engins |
| marque | Taille · fourches/subtype (ex: "3T · Courtes", "18m · 4RM") |

### attributions_engins
| numero_serie | FK engins |
| service | Zone WLG (SITE 1, LENI, PRAIRIE…) ou service municipal |
| date | Date de début (JJ/MM/AAAA) |
| date_fin | Date de fin (JJ/MM/AAAA) |
| periode | Journée / Matin / Après-midi |
| retourne | Vide ou datetime retour effectif |

### golfettes
| numero_serie | Clé primaire (ex: G1, G12) |
| type | FK categories_golfettes |
| marque | Marque |

### attributions_golfettes
- Même modèle que attributions_engins

### categories / categories_engins / categories_scooters / categories_golfettes
| nom | Défauts golfettes : Électrique, Thermique, Autre |

### services
| nom | Voirie, Bâtiment, Espaces verts (services municipaux) |
**Note** : les zones WLG (SITE 1, LENI, PRAIRIE…) sont stockées directement dans `attributions_engins.service` sans passer par la table services.

### interventions / interventions_engins / interventions_scooters / interventions_golfettes
| immatriculation/numero_serie | FK entité |
| type | Panne, Entretien, Réparation, Contrôle, Autre |
| date | JJ/MM/AAAA |
| heure | HH:MM |
| commentaire | Description libre |
| statut | En cours, Terminée, En attente |

### distribution_clefs
| date | JJ/MM/AAAA |
| heure | HH:MM |
| categorie | vehicule / scooter / engin / golfette |
| identifiant | immatriculation ou numero_serie |
| nom | Prénom NOM du preneur |
| commentaire | Optionnel |
| retour_clef | Vide ou datetime retour |
| ext_sheet | (sync Google Sheet externe WLG) |
| ext_row | (sync Google Sheet externe WLG) |

### carburant
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
| nom | Libellé affiché sur le bouton du Dashboard |
| url | URL complète vers le tableau Excel / Google Sheets |

---

## Fonctions CRUD complètes

### Véhicules
- `add_vehicule(immat, type_v, marque)` — anti-doublon
- `retourner_vehicule(immat)`, `update_attribution(idx, data)`, `delete_attribution(idx)`

### Scooters
- `add_scooter()`, `retourner_scooter(immat)`, `add_attribution_scooter(..., casque="")`

### Engins
- `add_engin()`, `retourner_engin(num_serie)`, `add_attribution_engin(num_serie, service, date_debut, date_fin, periode)`
- `update_attribution_engin(idx, data)`, `delete_attribution_engin(idx)`

### Golfettes
- `get_golfettes()` / `add_golfette()` / `delete_golfette()`
- `get_attributions_golfettes()` / `add_attribution_golfette(num_serie, service, date_debut, date_fin, periode)`
- `retourner_golfette(num_serie)`
- `update_attribution_golfette(idx, data)` / `delete_attribution_golfette(idx)`
- `get_interventions_golfettes()` / `add_intervention_golfette(num_serie, type_i, date, heure, comm, statut)`

### Distribution Clefs
- `get_distribution_clefs()` → liste triée par date/heure desc
- `add_distribution_clef(categorie, identifiant, nom, commentaire="")` — ajoute avec date/heure courante
- `retour_clef(idx)` — marque retour_clef avec datetime actuel

### Catégories & Services
- `get_categories()` / `add_category(nom)` / `delete_category(nom)` (idem pour engins, scooters, golfettes)
- `get_services()` / `add_service(nom)` / `delete_service(nom)`

### Alertes
- `verifier_alertes(attributions)` — véhicules, retour <= 2 jours
- `verifier_alertes_scooters(attributions)` — scooters, retour <= 2 jours
- `verifier_alertes_engins(attributions)` — engins dont date_fin < today et non retournés
- `verifier_alertes_golfettes(attributions)` — golfettes dont date_fin < today et non retournées

### PDF
- `generer_pdf_bon(bon, conducteur_nom, conducteur_prenom, logo_url=None)` → BytesIO

---

## Pages de l'application

| Page | Clé nav | Contenu |
|------|---------|---------|
| Dashboard | 📊 Dashboard | Métriques, détails par type, sorties/retours du jour, retourner entité, boutons liens |
| Distribution Clés | 🔑 Distribution Clés | Vue clés en circulation par catégorie + distribution toutes catégories |
| Planning Engins WLG | 🎪 Planning Engins WLG | Rush mode (clés en circulation + distribuer avec confirmation anticipée) + statut groupé C/T/N + planning semaine coloré par zone + ajuster attribution |
| Planning Golfettes WLG | ⛳ Planning Golfettes WLG | Même structure pour golfettes |
| Interventions WLG | 🔨 Interventions WLG | Déclarer + suivre interventions engins et golfettes WLG (2 onglets) |
| Saisir véhicule | ➕ Saisir un véhicule | Formulaire ajout + liste avec suppression |
| Attribuer véhicule | 🔧 Attribuer un véhicule | Formulaire + historique éditable |
| Bons carburant | ⛽ Bons de Carburant | Générer bon PDF + saisie retour |
| Interventions VH | 🔨 Pannes & Interventions | Déclarer + historique |
| Saisir scooter | 🛵 Saisir un scooter | Formulaire ajout + liste |
| Attribuer scooter | 🔧 Attribuer un scooter | Formulaire (avec casque) + historique éditable |
| Interventions SCO | 🔨 Interventions Scooters | Déclarer + historique |
| Vue Engins | 📊 Vue Engins | Tableau de bord opérationnel engins |
| Saisir engin | 🚜 Saisir un engin | Formulaire ajout + liste |
| Attribuer engin | 🔧 Attribuer un engin | Planning semaine + formulaire période + historique éditable |
| Interventions ENG | 🔨 Interventions Engins | Déclarer + historique |
| Vue Golfettes | 📊 Vue Golfettes | Tableau de bord golfettes |
| Saisir golfette | ⛳ Saisir une golfette | Formulaire ajout + liste |
| Attribuer golfette | 🔧 Attribuer une golfette | Planning semaine + formulaire période + historique éditable |
| Interventions GOLF | 🔨 Interventions Golfettes | Déclarer + historique |
| Paramètres | ⚙️ Paramètres | Thème + gestion catégories/services + gestion liens Excel |

---

## Sidebar (menu catégorisé)

```
🚗 Flotte (titre)
├── 📊 Dashboard (bouton principal)
├── 🔑 Distribution Clés (bouton principal)
├── 🎪 WLG26 (expander)
│   ├── Planning Engins WLG
│   ├── Planning Golfettes WLG
│   └── Interventions WLG
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
│   ├── Vue Engins
│   ├── Saisir un engin
│   ├── Attribuer un engin
│   └── Interventions Engins
├── ⛳ Golfettes (expander)
│   ├── Vue Golfettes
│   ├── Saisir une golfette
│   ├── Attribuer une golfette
│   └── Interventions Golfettes
├── ⚙️ Paramètres (bouton principal)
├── ── Alertes ──
│   ├── 🚨 Véhicules à retourner
│   ├── 🚜 Engins à retourner
│   ├── ⛳ Golfettes à retourner
│   └── 🛵 Scooters à retourner
└── 🗄️ Base connectée
```

Navigation via `st.session_state.page` + `nav_to()` callback.
Expanders ouverts auto quand page active dans la catégorie.

---

## Système de cache

```
Premier chargement : 1 appel batchGet (toutes feuilles)
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
- `dashboard_detail` — vue détail du dashboard (vehicules/scooters/engins/golfettes/None)
- `dernier_bon` — dernier bon carburant généré (pour PDF)
- `eng_sem_offset` — décalage semaine planning engins (page engins)
- `wlg_sem_offset` — décalage semaine planning engins WLG
- `wlg_golf_sem_offset` — décalage semaine planning golfettes WLG
- `golf_sem_offset` — décalage semaine planning golfettes (page golfettes)
- `_fk` — compteur form key (incrémenté après soumission réussie pour reset les forms)

---

## Patterns de clés formulaires
- `f"edit_attr_vh_{idx}"` / `f"edit_attr_sco_{idx}"` / `f"edit_attr_eng_{idx}"` / `f"edit_attr_golf_{idx}"` — forms édition
- `f"wlg_sel_engin"` / `f"wlg_sel_golf"` — selectbox distribution WLG (hors form)
- `f"wlg_early_{sel_num}"` / `f"wlg_golf_early_{sel_num}"` — checkbox confirmation anticipée
- `f"del_{immat}"` / `f"del_sco_{immat}"` / `f"del_eng_{num}"` / `f"del_golf_{num}"` — boutons suppression

---

## WLG26 — Conventions spécifiques

- **Engins WLG** : filtré par regex `^[CTN]\d+$` — C=chariots (C1-C24), T=télescopiques (T1-T8), N=nacelles (N1-N9)
- **Golfettes WLG** : toutes les golfettes en DB sont WLG (G1-G21+)
- **Zones** : noms libres dans `attributions.service` (SITE 1, LENI, PRAIRIE, etc.) — ne pas confondre avec la table `services` (services municipaux)
- **Couleurs zones** : `abs(hash(zone)) % len(palette)` — couleur stable par nom de zone
- **Attribution "most specific"** : quand plusieurs attributions couvrent un même jour, la plus courte durée (date range) l'emporte — permet les overrides journaliers
- **Livraison anticipée** : engin présent mais pas encore dans sa période active → dropdown affiche juste l'ID, checkbox de confirmation requise avant distribution
