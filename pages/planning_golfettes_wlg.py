import html
import re
import streamlit as st
from datetime import datetime, timedelta
from database import (
    get_distribution_clefs, add_distribution_clef, retour_clef,
    add_attribution_golfette,
)

esc = html.escape

JOURS_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

_PALETTE = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#a855f7',
    '#14b8a6', '#f43f5e', '#0ea5e9', '#d97706', '#7c3aed',
    '#16a34a', '#b91c1c', '#0284c7', '#c2410c', '#6d28d9',
]


def _zone_color(zone):
    if not zone:
        return '#6b7280'
    return _PALETTE[abs(hash(zone)) % len(_PALETTE)]


def _sort_key(g):
    num = g.get('numero_serie', '')
    n = int(re.sub(r'\D', '', num) or '0')
    return n


def _get_zone_for_day(num_serie, day, attributions):
    best, best_dur = None, None
    for a in attributions:
        if a.get('numero_serie') != num_serie or a.get('retourne'):
            continue
        try:
            dd = datetime.strptime(a['date'], "%d/%m/%Y").date()
            df = datetime.strptime(a.get('date_fin', a['date']), "%d/%m/%Y").date()
            if dd <= day <= df:
                dur = (df - dd).days
                if best_dur is None or dur < best_dur:
                    best = a.get('service', '')
                    best_dur = dur
        except Exception:
            pass
    return best


def _clef_status(num_serie, clefs):
    for i, c in enumerate(clefs):
        if c.get('identifiant') == num_serie and c.get('categorie') == 'golfette' and not c.get('retour_clef'):
            return True, c, i
    return False, None, None


def render_planning_golfettes_wlg(t, golfettes, attributions_golfettes):
    today = datetime.now().date()

    golfettes_sorted = sorted(golfettes, key=_sort_key)
    clefs = get_distribution_clefs()

    actifs_today = [g for g in golfettes_sorted if _get_zone_for_day(g['numero_serie'], today, attributions_golfettes)]

    en_circulation = []
    for g in actifs_today:
        out, entry, idx = _clef_status(g['numero_serie'], clefs)
        if out:
            en_circulation.append((g, entry, idx))

    circ_ids = {g['numero_serie'] for g, _, _ in en_circulation}
    disponibles = [g for g in actifs_today if g['numero_serie'] not in circ_ids]

    # En-tête
    st.markdown("# ⛳ Planning Golfettes WLG26")
    JOURS_LONG = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
               'août', 'septembre', 'octobre', 'novembre', 'décembre']
    today_str = f"{JOURS_LONG[today.weekday()]} {today.day} {MOIS_FR[today.month - 1]} {today.year}"
    st.markdown(f"<p class='page-intro'>{today_str}</p>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⛳ Golfettes", len(golfettes_sorted))
    c2.metric("📅 Actives aujourd'hui", len(actifs_today))
    c3.metric("🔴 Clés en circulation", len(en_circulation))
    c4.metric("🟢 Disponibles", len(disponibles))

    st.markdown("---")

    # ── CLÉS EN CIRCULATION ────────────────────────────────────────────────
    if en_circulation:
        st.markdown("### 🔴 Clés en circulation")
        for golf, entry, idx in en_circulation:
            num = golf['numero_serie']
            zone = _get_zone_for_day(num, today, attributions_golfettes) or '?'
            nom = entry.get('nom', '')
            heure = entry.get('heure', '')
            zone_color = _zone_color(zone)

            col_info, col_btn = st.columns([5, 1])
            col_info.markdown(
                f"<div style='background:{t['card_bg']};border:1px solid {t['card_border']};"
                f"border-left:4px solid #ef4444;border-radius:10px;padding:0.75rem 1.2rem;'>"
                f"<span style='color:{t['h1_color']};font-weight:700;font-size:1.1rem;'>⛳ {esc(num)}</span>"
                f"<span style='background:{zone_color};color:white;padding:2px 10px;"
                f"border-radius:10px;margin-left:0.8rem;font-size:0.8rem;font-weight:600;'>{esc(zone)}</span>"
                f"<span style='color:{t['label_color']};margin-left:1rem;font-size:0.95rem;'>"
                f"👤 <b>{esc(nom)}</b></span>"
                f"<span style='color:{t['intro_color']};margin-left:0.8rem;font-size:0.85rem;'>⏰ {esc(heure)}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if col_btn.button("✅ Rendu", key=f"wlg_golf_ret_{num}", type="primary"):
                retour_clef(idx)
                st.success(f"✅ Clé {num} rendue !")
                st.rerun()
        st.markdown("---")

    # ── DISTRIBUER UNE CLÉ ────────────────────────────────────────────────
    st.markdown("### 🔑 Distribuer une clé")

    all_dispo = [g for g in golfettes_sorted if g['numero_serie'] not in circ_ids]

    def _golf_label(g):
        num = g['numero_serie']
        zone = _get_zone_for_day(num, today, attributions_golfettes)
        if zone:
            return f"{num} — {zone}"
        next_start = None
        for a in attributions_golfettes:
            if a.get('numero_serie') != num or a.get('retourne'):
                continue
            try:
                dd = datetime.strptime(a['date'], "%d/%m/%Y").date()
                if dd > today and (next_start is None or dd < next_start):
                    next_start = dd
            except Exception:
                pass
        if next_start:
            return f"{num} — (livraison anticipée, démarre le {next_start.strftime('%d/%m')})"
        return f"{num} — (hors période)"

    dispo_options = [_golf_label(g) for g in all_dispo]

    if dispo_options:
        with st.form(f"form_wlg_golf_distrib_{st.session_state.get('_fk', 0)}"):
            col_a, col_b, col_c = st.columns([2, 3, 2])
            golf_sel = col_a.selectbox("Golfette *", dispo_options)
            nom_input = col_b.text_input("Preneur *", placeholder="Prénom NOM")
            commentaire = col_c.text_input("Commentaire", placeholder="Optionnel")
            if st.form_submit_button("🔑 Distribuer", type="primary"):
                if nom_input.strip():
                    num = golf_sel.split(" — ")[0]
                    add_distribution_clef('golfette', num, nom_input.strip(), commentaire)
                    st.success(f"✅ Clé {num} → {nom_input.strip()}")
                    st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                    st.rerun()
                else:
                    st.error("❌ Le nom du preneur est requis")
    else:
        st.info("Toutes les clés sont en circulation")

    st.markdown("---")

    # ── STATUT AUJOURD'HUI ────────────────────────────────────────────────
    st.markdown("### 📋 Golfettes actives aujourd'hui")

    cb = t['card_border']
    ib = t['input_bg']
    hc = t['h23_color']
    ic = t['intro_color']

    th = (f"padding:0.5rem 0.7rem;border:1px solid {cb};background:{ib};"
          f"color:{hc};font-weight:600;font-size:0.8rem;text-align:left;")
    td = f"padding:0.55rem 0.7rem;border:1px solid {cb};font-size:0.85rem;vertical-align:middle;"

    if not actifs_today:
        st.info("Aucune golfette active aujourd'hui")
    else:
        table = (
            f"<div style='overflow-x:auto;margin-bottom:1.4rem;'>"
            f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
            f"<th style='{th} width:65px;'>ID</th>"
            f"<th style='{th} width:130px;'>Type</th>"
            f"<th style='{th}'>Zone assignée</th>"
            f"<th style='{th}'>Statut clé</th>"
            f"</tr></thead><tbody>"
        )
        for g in actifs_today:
            num = g['numero_serie']
            type_g = g.get('type', '')
            zone = _get_zone_for_day(num, today, attributions_golfettes) or ''
            out, entry, _ = _clef_status(num, clefs)
            zone_color = _zone_color(zone)

            if out and entry:
                row_style = "background:rgba(239,68,68,0.07);border-left:3px solid #ef4444;"
                nom_p = entry.get('nom', '')
                heure_p = entry.get('heure', '')
                clef_cell = (
                    f"<span style='color:#ef4444;font-weight:600;'>🔴 {esc(nom_p)}</span>"
                    f"<span style='color:{ic};font-size:0.8rem;margin-left:0.5rem;'>• {esc(heure_p)}</span>"
                )
            else:
                row_style = "background:rgba(16,185,129,0.05);border-left:3px solid #10b981;"
                clef_cell = "<span style='color:#10b981;font-weight:600;'>🟢 Disponible</span>"

            zone_badge = (
                f"<span style='background:{zone_color};color:white;padding:3px 12px;"
                f"border-radius:12px;font-weight:600;font-size:0.82rem;'>{esc(zone)}</span>"
            ) if zone else f"<span style='color:{ic}'>—</span>"

            table += (
                f"<tr style='{row_style}'>"
                f"<td style='{td} font-weight:700;font-size:1.05rem;color:{hc};'>⛳ {esc(num)}</td>"
                f"<td style='{td} color:{ic};font-size:0.8rem;'>{esc(type_g)}</td>"
                f"<td style='{td}'>{zone_badge}</td>"
                f"<td style='{td}'>{clef_cell}</td>"
                f"</tr>"
            )
        table += "</tbody></table></div>"
        st.markdown(table, unsafe_allow_html=True)

    # ── PLANNING SEMAINE ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Planning semaine")

    if 'wlg_golf_sem_offset' not in st.session_state:
        st.session_state['wlg_golf_sem_offset'] = 0

    lundi = today - timedelta(days=today.weekday())
    sem_debut = lundi + timedelta(weeks=st.session_state['wlg_golf_sem_offset'])
    sem_fin = sem_debut + timedelta(days=6)

    col_n1, col_n2, col_n3 = st.columns([1, 3, 1])
    if col_n1.button("← Préc.", key="wlg_golf_prev"):
        st.session_state['wlg_golf_sem_offset'] -= 1
        st.rerun()
    col_n2.markdown(
        f"<h4 style='text-align:center;color:{hc}'>"
        f"Semaine du {sem_debut.strftime('%d/%m')} au {sem_fin.strftime('%d/%m/%Y')}</h4>",
        unsafe_allow_html=True,
    )
    if col_n3.button("Suiv. →", key="wlg_golf_next"):
        st.session_state['wlg_golf_sem_offset'] += 1
        st.rerun()

    if golfettes_sorted:
        jours_sem = [sem_debut + timedelta(days=i) for i in range(7)]

        th_s = (f"padding:0.4rem 0.35rem;border:1px solid {cb};text-align:center;"
                f"background:{ib};color:{hc};font-weight:600;font-size:0.76rem;")
        td_s = f"border:1px solid {cb};text-align:center;padding:0.3rem 0.25rem;font-size:0.74rem;"
        td_eng = (f"{td_s}background:{ib};color:{hc};text-align:left;"
                  f"padding:0.35rem 0.55rem;font-weight:700;font-size:0.9rem;")

        grid = (
            f"<div style='overflow-x:auto'>"
            f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
            f"<th style='{th_s} text-align:left;min-width:60px;'>Golfette</th>"
        )
        for i, jour in enumerate(jours_sem):
            is_today = jour == today
            j_color = '#f59e0b' if is_today else hc
            j_bg = "background:rgba(245,158,11,0.12);" if is_today else ""
            j_bold = "font-weight:800;" if is_today else ""
            grid += (f"<th style='{th_s}color:{j_color};{j_bg}{j_bold}min-width:78px;'>"
                     f"{JOURS_FR[i]}<br>{jour.strftime('%d/%m')}</th>")
        grid += "</tr></thead><tbody>"

        for g in golfettes_sorted:
            num = g['numero_serie']
            out_today, _, _ = _clef_status(num, clefs)
            grid += f"<tr><td style='{td_eng}'>⛳ {esc(num)}</td>"
            for jour in jours_sem:
                is_today_col = jour == today
                zone = _get_zone_for_day(num, jour, attributions_golfettes)
                today_bg = "background:rgba(245,158,11,0.08);" if is_today_col else ""
                if zone:
                    bg = _zone_color(zone)
                    clef_mk = " 🔑" if (is_today_col and out_today) else ""
                    grid += (f"<td style='{td_s}{today_bg}background:{bg};"
                             f"color:white;font-weight:600;'>{esc(zone)}{clef_mk}</td>")
                else:
                    grid += f"<td style='{td_s}{today_bg}color:{ic};'>—</td>"
            grid += "</tr>"

        grid += "</tbody></table></div>"
        st.markdown(grid, unsafe_allow_html=True)

        all_zones = set()
        for g in golfettes_sorted:
            for j in jours_sem:
                z = _get_zone_for_day(g['numero_serie'], j, attributions_golfettes)
                if z:
                    all_zones.add(z)
        if all_zones:
            legend = " ".join(
                f"<span style='background:{_zone_color(z)};color:white;padding:0.15rem 0.55rem;"
                f"border-radius:10px;font-size:0.72rem;margin:0.15rem;display:inline-block;'>"
                f"{esc(z)}</span>"
                for z in sorted(all_zones)
            )
            st.markdown(f"<div style='margin-top:0.5rem;line-height:2.2;'>{legend}</div>",
                        unsafe_allow_html=True)

    # ── AJUSTER LE PLANNING ───────────────────────────────────────────────
    st.markdown("---")
    with st.expander("✏️ Ajuster le planning — modifier la zone d'une golfette"):
        if golfettes_sorted:
            with st.form(f"form_wlg_golf_adj_{st.session_state.get('_fk', 0)}"):
                col1, col2 = st.columns(2)
                golf_opts = [
                    f"{g['numero_serie']} — {g.get('type', '')} "
                    f"({_get_zone_for_day(g['numero_serie'], today, attributions_golfettes) or 'non actif'})"
                    for g in golfettes_sorted
                ]
                golf_adj = col1.selectbox("Golfette *", golf_opts)
                zone_adj = col2.text_input("Nouvelle zone *", placeholder="SCENE 1, LENI, PRAIRIE…")
                col3, col4 = st.columns(2)
                date_deb = col3.date_input("Du *", value=today)
                date_fin_v = col4.date_input("Au *", value=today)
                if st.form_submit_button("✅ Confirmer", type="primary"):
                    if zone_adj.strip() and date_fin_v >= date_deb:
                        num = golf_adj.split(" — ")[0]
                        add_attribution_golfette(
                            num, zone_adj.strip(),
                            date_deb.strftime("%d/%m/%Y"),
                            date_fin_v.strftime("%d/%m/%Y"),
                            "Journée",
                        )
                        st.success(f"✅ {num} → {zone_adj.strip()} du {date_deb.strftime('%d/%m')} au {date_fin_v.strftime('%d/%m')}")
                        st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                        st.rerun()
                    else:
                        st.error("❌ Zone requise et date fin ≥ date début")
