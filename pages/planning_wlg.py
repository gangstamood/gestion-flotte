import html
import re
import streamlit as st
from datetime import datetime, timedelta
from database import (
    get_distribution_clefs, add_distribution_clef, retour_clef,
    add_attribution_engin, ecraser_attributions_engin_periode,
    marquer_retard_livraison_engin, marquer_engin_recu,
    marquer_livraison_anticipee_engin, annuler_livraison_anticipee_engin,
)

esc = html.escape

GROUPE_INFO = {
    'C': ('🚜', 'Chariots'),
    'T': ('🏗️', 'Télescopiques'),
    'N': ('🦺', 'Nacelles'),
}
GROUPE_ORDER = ['C', 'T', 'N']
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


def _is_wlg(num):
    return bool(re.match(r'^[CTN]\d+$', str(num)))


def _sort_key(engin):
    num = engin.get('numero_serie', '')
    g = num[0].upper() if num else '?'
    n = int(re.sub(r'\D', '', num) or '0')
    return (GROUPE_ORDER.index(g) if g in GROUPE_ORDER else 99, n)


def _get_zone_for_day(num_serie, day, attributions_engins):
    """Retourne la zone la plus spécifique (plage la plus courte) couvrant ce jour."""
    best = None
    best_dur = None
    for a in attributions_engins:
        if a.get('numero_serie') != num_serie or a.get('retourne'):
            continue
        try:
            dd = datetime.strptime(a['date'], "%d/%m/%Y").date()
            df = datetime.strptime(a.get('date_fin', a['date']), "%d/%m/%Y").date()
            if dd <= day <= df:
                dur = (df - dd).days
                # `<=` : à durée égale la dernière attribution rencontrée gagne,
                # ce qui permet à un ajustement manuel d'écraser un planning existant.
                if best_dur is None or dur <= best_dur:
                    best = a.get('service', '')
                    best_dur = dur
        except Exception:
            pass
    return best


def _get_zone_upcoming(num_serie, today, attributions_engins):
    """Retourne la zone de la prochaine attribution à venir (ou en cours)."""
    best = None
    best_date = None
    for a in attributions_engins:
        if a.get('numero_serie') != num_serie or a.get('retourne'):
            continue
        try:
            dd = datetime.strptime(a['date'], "%d/%m/%Y").date()
            df = datetime.strptime(a.get('date_fin', a['date']), "%d/%m/%Y").date()
            if df >= today:
                if best_date is None or dd < best_date:
                    best = a.get('service', '')
                    best_date = dd
        except Exception:
            pass
    return best


def _clef_status(num_serie, clefs):
    """Retourne (en_circulation, entry, idx) pour l'état courant de la clé."""
    for i, c in enumerate(clefs):
        if c.get('identifiant') == num_serie and c.get('categorie') == 'engin' and not c.get('retour_clef'):
            return True, c, i
    return False, None, None


def render_planning_wlg(t, engins, attributions_engins, interventions_engins=None):
    today = datetime.now().date()

    wlg_engins = [e for e in engins if _is_wlg(e.get('numero_serie', ''))]
    wlg_engins.sort(key=_sort_key)
    wlg_ids = {e['numero_serie'] for e in wlg_engins}

    clefs = get_distribution_clefs()

    # Engins WLG avec au moins une intervention "En cours"
    en_intervention_ids = set()
    for iv in (interventions_engins or []):
        if iv.get('statut') == 'En cours' and iv.get('numero_serie') in wlg_ids:
            en_intervention_ids.add(iv['numero_serie'])
    nb_intervention = len(en_intervention_ids)

    # Engins WLG avec une clé en circulation (inclut les mises en circulation anticipées)
    clef_out_ids = {
        c.get('identifiant') for c in clefs
        if c.get('categorie') == 'engin' and not c.get('retour_clef') and c.get('identifiant') in wlg_ids
    }

    # Engins WLG signalés comme non livrés (retard de livraison loueur)
    retard_ids = {e['numero_serie'] for e in wlg_engins if e.get('retard_livraison')}

    # Engins ayant déjà eu une clé distribuée (preuve qu'ils ont été sur parc)
    deja_recu_ids = {
        c.get('identifiant') for c in clefs
        if c.get('categorie') == 'engin'
    }

    # Engins WLG signalés comme livrés en avance (présents avant leur date de planning)
    avance_ids = {e['numero_serie'] for e in wlg_engins if e.get('livraison_anticipee')}

    actifs_today = [
        e for e in wlg_engins
        if _get_zone_for_day(e['numero_serie'], today, attributions_engins)
        or e['numero_serie'] in en_intervention_ids
        or e['numero_serie'] in clef_out_ids
        or e['numero_serie'] in retard_ids
        or e['numero_serie'] in avance_ids
    ]

    en_circulation = []
    for e in actifs_today:
        out, entry, idx = _clef_status(e['numero_serie'], clefs)
        if out:
            en_circulation.append((e, entry, idx))

    circ_ids = {e['numero_serie'] for e, _, _ in en_circulation}
    nb_non_livres = sum(1 for e in actifs_today if e['numero_serie'] in retard_ids)
    disponibles = [
        e for e in actifs_today
        if e['numero_serie'] not in circ_ids and e['numero_serie'] not in retard_ids
    ]

    # En-tête
    st.markdown("# 🎪 Planning WLG26")
    JOURS_LONG = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
               'août', 'septembre', 'octobre', 'novembre', 'décembre']
    today_str = f"{JOURS_LONG[today.weekday()]} {today.day} {MOIS_FR[today.month - 1]} {today.year}"
    st.markdown(f"<p class='page-intro'>{today_str}</p>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🚜 Engins WLG", len(wlg_engins))
    c2.metric("📅 Actifs aujourd'hui", len(actifs_today))
    c3.metric("🔴 Clés en circulation", len(en_circulation))
    c4.metric("🟢 Disponibles", len(disponibles))
    c5.metric("🔨 En intervention", nb_intervention)
    c6.metric("🚚 En attente livraison", nb_non_livres)

    st.markdown("---")

    # ── LIVRAISONS PRÉVUES POUR DEMAIN ─────────────────────────────────────
    tomorrow = today + timedelta(days=1)
    livraisons_demain = []
    for e in wlg_engins:
        num = e['numero_serie']
        if num in avance_ids:
            # déjà signalé livré en avance → présent dans le tableau actifs
            continue
        zone_tomorrow = _get_zone_for_day(num, tomorrow, attributions_engins)
        zone_today = _get_zone_for_day(num, today, attributions_engins)
        if zone_tomorrow and not zone_today:
            livraisons_demain.append((e, zone_tomorrow))

    if livraisons_demain:
        demain_str = f"{JOURS_LONG[tomorrow.weekday()]} {tomorrow.day} {MOIS_FR[tomorrow.month - 1]}"
        nb = len(livraisons_demain)
        st.markdown(
            f"### 🚚 À livrer cette nuit — pour {demain_str} "
            f"<span style='color:{t['intro_color']};font-size:0.85rem;font-weight:400;'>"
            f"({nb} engin{'s' if nb > 1 else ''})</span>",
            unsafe_allow_html=True,
        )
        for e, z in livraisons_demain:
            num = e['numero_serie']
            grp_icon = GROUPE_INFO.get(num[0].upper(), ('🚜', ''))[0]
            zc = _zone_color(z)
            col_info, col_btn = st.columns([7, 1.5])
            col_info.markdown(
                f"<div style='background:{t['card_bg']};border:1px solid {t['card_border']};"
                f"border-left:3px solid {zc};border-radius:8px;"
                f"padding:0.4rem 0.8rem;margin-bottom:0.3rem;'>"
                f"<b style='color:{t['h1_color']};font-size:1rem;'>{grp_icon} {esc(num)}</b>"
                f"<span style='background:{zc};color:white;padding:2px 10px;"
                f"border-radius:10px;font-size:0.78rem;font-weight:600;margin-left:0.6rem;'>"
                f"{esc(z)}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if col_btn.button("📦 Déjà livré", key=f"avance_{num}", use_container_width=True):
                marquer_livraison_anticipee_engin(num)
                st.success(f"📦 {num} signalé livré en avance")
                st.rerun()
        st.markdown("---")

    # ── SIGNALER UNE LIVRAISON ANTICIPÉE (autres jours) ────────────────────
    non_actifs = [
        e for e in wlg_engins
        if e['numero_serie'] not in {a['numero_serie'] for a in actifs_today}
        and e['numero_serie'] not in {e2['numero_serie'] for e2, _ in livraisons_demain}
    ]
    if non_actifs:
        with st.expander("📦 Signaler une livraison anticipée (autre jour)"):
            def _label_av(e):
                num = e['numero_serie']
                z_up = _get_zone_upcoming(num, today, attributions_engins)
                return f"{num} — prochaine zone : {z_up}" if z_up else f"{num} — pas de planning à venir"
            opts = [_label_av(e) for e in non_actifs]
            sel = st.selectbox("Engin *", opts, key="wlg_av_sel")
            sel_num = sel.split(" — ")[0]
            if st.button("📦 Signaler livré en avance", key="wlg_av_btn", type="primary"):
                marquer_livraison_anticipee_engin(sel_num)
                st.success(f"📦 {sel_num} signalé livré en avance")
                st.rerun()
        st.markdown("---")

    # ── CLÉs EN CIRCULATION (priorité matin) ───────────────────────────────
    if en_circulation:
        st.markdown("### 🔴 Clés en circulation")
        for eng, entry, idx in en_circulation:
            num = eng['numero_serie']
            zone = (
                _get_zone_for_day(num, today, attributions_engins)
                or _get_zone_upcoming(num, today, attributions_engins)
                or 'Anticipée'
            )
            nom = entry.get('nom', '')
            heure = entry.get('heure', '')
            zone_color = _zone_color(zone)
            grp_icon = GROUPE_INFO.get(num[0].upper(), ('🔑', ''))[0]

            col_info, col_btn = st.columns([5, 1])
            col_info.markdown(
                f"<div style='background:{t['card_bg']};border:1px solid {t['card_border']};"
                f"border-left:4px solid #ef4444;border-radius:10px;padding:0.75rem 1.2rem;'>"
                f"<span style='color:{t['h1_color']};font-weight:700;font-size:1.1rem;'>"
                f"{grp_icon} {esc(num)}</span>"
                f"<span style='background:{zone_color};color:white;padding:2px 10px;"
                f"border-radius:10px;margin-left:0.8rem;font-size:0.8rem;font-weight:600;'>"
                f"{esc(zone)}</span>"
                f"<span style='color:{t['label_color']};margin-left:1rem;font-size:0.95rem;'>"
                f"👤 <b>{esc(nom)}</b></span>"
                f"<span style='color:{t['intro_color']};margin-left:0.8rem;font-size:0.85rem;'>"
                f"⏰ {esc(heure)}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if col_btn.button("✅ Rendu", key=f"wlg_ret_{num}", type="primary"):
                retour_clef(idx)
                st.success(f"✅ Clé {num} rendue !")
                st.rerun()

        st.markdown("---")

    # ── DISTRIBUER UNE CLÉ ─────────────────────────────────────────────────
    st.markdown("### 🔑 Distribuer une clé")

    # Tous les engins sans clé en circulation (y compris pas encore actifs)
    all_dispo = [e for e in wlg_engins if e['numero_serie'] not in circ_ids]

    def _engin_label(e):
        num = e['numero_serie']
        zone = _get_zone_for_day(num, today, attributions_engins)
        return f"{num} — {zone}" if zone else num

    dispo_options = [_engin_label(e) for e in all_dispo]

    if dispo_options:
        engin_sel = st.selectbox("Engin *", dispo_options, key="wlg_sel_engin")
        sel_num = engin_sel.split(" — ")[0]
        is_inactive = not _get_zone_for_day(sel_num, today, attributions_engins)

        confirm = False
        if is_inactive:
            confirm = st.checkbox("⚠️ Confirmer la mise en circulation anticipée", key=f"wlg_early_{sel_num}")

        with st.form(f"form_wlg_distrib_{st.session_state.get('_fk', 0)}"):
            col_b, col_c = st.columns([3, 2])
            nom_input = col_b.text_input("Preneur *", placeholder="Prénom NOM")
            commentaire = col_c.text_input("Commentaire", placeholder="Optionnel")
            if st.form_submit_button("🔑 Distribuer", type="primary"):
                if not nom_input.strip():
                    st.error("❌ Le nom du preneur est requis")
                elif is_inactive and not confirm:
                    st.error("⚠️ Cochez la case pour confirmer la mise en circulation anticipée")
                else:
                    add_distribution_clef('engin', sel_num, nom_input.strip(), commentaire)
                    st.success(f"✅ Clé {sel_num} → {nom_input.strip()}")
                    st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                    st.rerun()
    else:
        st.info("Toutes les clés sont en circulation")

    st.markdown("---")

    # ── STATUT DE TOUS LES ENGINS AUJOURD'HUI ─────────────────────────────
    st.markdown("### 📋 Engins actifs aujourd'hui")

    cb = t['card_border']
    ib = t['input_bg']
    hc = t['h23_color']
    ic = t['intro_color']

    engin_map = {e['numero_serie']: e for e in wlg_engins}

    if not actifs_today:
        st.info("Aucun engin actif aujourd'hui")
    else:
        for groupe in GROUPE_ORDER:
            g_engins = [e for e in actifs_today if e.get('numero_serie', '')[0].upper() == groupe]
            if not g_engins:
                continue
            grp_icon, grp_label = GROUPE_INFO[groupe]
            st.markdown(f"**{grp_icon} {grp_label}**")

            for eng in g_engins:
                num = eng['numero_serie']
                marque = eng.get('marque', '')
                num_pre = engin_map.get(num, {}).get('numero_prestataire', '') or ''
                zone_today = _get_zone_for_day(num, today, attributions_engins)
                out, entry, _ = _clef_status(num, clefs)
                non_livre = num in retard_ids
                # "livré en avance" effectif : flag set ET pas encore dans son planning
                en_avance = (num in avance_ids) and not zone_today
                if zone_today:
                    zone = zone_today
                elif out:
                    zone = _get_zone_upcoming(num, today, attributions_engins) or 'Anticipée'
                elif en_avance:
                    zone = _get_zone_upcoming(num, today, attributions_engins) or ''
                elif non_livre:
                    zone = _get_zone_upcoming(num, today, attributions_engins) or ''
                else:
                    zone = ''
                zone_color = _zone_color(zone)
                in_interv = num in en_intervention_ids

                # Style de bordure selon le statut
                # (priorité non livré > intervention > clé sortie > livré en avance > dispo)
                if non_livre:
                    border_color = '#a16207'  # ambre foncé
                    bg_tint = 'rgba(161,98,7,0.08)'
                elif in_interv:
                    border_color = '#f97316'
                    bg_tint = 'rgba(249,115,22,0.10)'
                elif out and entry:
                    border_color = '#ef4444'
                    bg_tint = 'rgba(239,68,68,0.07)'
                elif en_avance:
                    border_color = '#0ea5e9'  # bleu cyan
                    bg_tint = 'rgba(14,165,233,0.08)'
                else:
                    border_color = '#10b981'
                    bg_tint = 'rgba(16,185,129,0.05)'

                # Statut clé
                if out and entry:
                    nom_p = entry.get('nom', '')
                    heure_p = entry.get('heure', '')
                    clef_html = (
                        f"<span style='color:#ef4444;font-weight:600;'>🔴 {esc(nom_p)}</span>"
                        f"<span style='color:{ic};font-size:0.8rem;margin-left:0.4rem;'>• {esc(heure_p)}</span>"
                    )
                else:
                    clef_html = "<span style='color:#10b981;font-weight:600;'>🟢 Disponible</span>"

                badges = ""
                if non_livre:
                    retard_dt = eng.get('retard_livraison', '')
                    badges += (
                        f"<span style='background:#a16207;color:white;padding:2px 8px;"
                        f"border-radius:8px;margin-left:0.4rem;font-size:0.72rem;font-weight:600;'"
                        f" title='Signalé le {esc(retard_dt)}'>🚚 Non livré</span>"
                    )
                if en_avance:
                    avance_dt = eng.get('livraison_anticipee', '')
                    badges += (
                        f"<span style='background:#0ea5e9;color:white;padding:2px 8px;"
                        f"border-radius:8px;margin-left:0.4rem;font-size:0.72rem;font-weight:600;'"
                        f" title='Signalé le {esc(avance_dt)}'>📦 Livré en avance</span>"
                    )
                if in_interv:
                    badges += (
                        "<span style='background:#f97316;color:white;padding:2px 8px;"
                        "border-radius:8px;margin-left:0.4rem;font-size:0.72rem;font-weight:600;'>"
                        "🔨 Intervention</span>"
                    )

                zone_badge = (
                    f"<span style='background:{zone_color};color:white;padding:3px 10px;"
                    f"border-radius:10px;font-weight:600;font-size:0.78rem;'>{esc(zone)}</span>"
                ) if zone else f"<span style='color:{ic}'>—</span>"

                pre_html = (
                    f"<span style='color:{ic};font-size:0.78rem;'>N° {esc(num_pre)}</span>"
                ) if num_pre else ""
                marque_html = (
                    f"<span style='color:{ic};font-size:0.78rem;'>{esc(marque)}</span>"
                ) if marque else ""

                col_info, col_btn = st.columns([7, 1.5])
                col_info.markdown(
                    f"<div style='background:{bg_tint};border:1px solid {cb};"
                    f"border-left:3px solid {border_color};border-radius:8px;"
                    f"padding:0.5rem 0.8rem;margin-bottom:0.35rem;"
                    f"display:flex;flex-wrap:wrap;align-items:center;gap:0.6rem;'>"
                    f"<span style='font-weight:700;font-size:1.05rem;color:{hc};min-width:48px;'>{esc(num)}</span>"
                    f"<span style='min-width:90px;'>{pre_html}</span>"
                    f"<span style='min-width:120px;'>{marque_html}</span>"
                    f"<span>{zone_badge}</span>"
                    f"<span style='flex:1;'>{clef_html}{badges}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                # L'engin est considéré sur parc si clé en circulation, intervention,
                # ou clé déjà distribuée par le passé → masque le bouton "Non livré"
                sur_parc = out or in_interv or num in deja_recu_ids

                with col_btn:
                    if non_livre:
                        if st.button("✅ Reçu", key=f"recu_{num}", type="primary", use_container_width=True):
                            marquer_engin_recu(num)
                            st.success(f"✅ {num} marqué reçu sur parc")
                            st.rerun()
                    elif en_avance:
                        if st.button("↩️ Annuler avance", key=f"unav_{num}", use_container_width=True):
                            annuler_livraison_anticipee_engin(num)
                            st.info(f"↩️ {num} : livraison anticipée annulée")
                            st.rerun()
                    elif not sur_parc:
                        if st.button("🚚 Non livré", key=f"nonlivre_{num}", use_container_width=True):
                            marquer_retard_livraison_engin(num)
                            st.warning(f"🚚 {num} signalé non livré")
                            st.rerun()

    # ── PLANNING SEMAINE ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📅 Planning semaine")

    if 'wlg_jour_offset' not in st.session_state:
        st.session_state['wlg_jour_offset'] = 0

    lundi = today - timedelta(days=today.weekday())
    sem_debut = lundi + timedelta(days=st.session_state['wlg_jour_offset'])
    sem_fin = sem_debut + timedelta(days=6)

    col_n1, col_n2, col_n3, col_n4, col_n5 = st.columns([1, 1, 4, 1, 1])
    if col_n1.button("⏮ Sem.", key="wlg_prev_sem"):
        st.session_state['wlg_jour_offset'] -= 7
        st.rerun()
    if col_n2.button("← Jour", key="wlg_prev_jour"):
        st.session_state['wlg_jour_offset'] -= 1
        st.rerun()
    aligne_lundi = sem_debut.weekday() == 0
    titre = (
        f"Semaine du {sem_debut.strftime('%d/%m')} au {sem_fin.strftime('%d/%m/%Y')}"
        if aligne_lundi
        else f"Du {JOURS_FR[sem_debut.weekday()]} {sem_debut.strftime('%d/%m')} "
             f"au {JOURS_FR[sem_fin.weekday()]} {sem_fin.strftime('%d/%m/%Y')}"
    )
    col_n3.markdown(
        f"<h4 style='text-align:center;color:{hc}'>{titre}</h4>",
        unsafe_allow_html=True,
    )
    if col_n4.button("Jour →", key="wlg_next_jour"):
        st.session_state['wlg_jour_offset'] += 1
        st.rerun()
    if col_n5.button("Sem. ⏭", key="wlg_next_sem"):
        st.session_state['wlg_jour_offset'] += 7
        st.rerun()

    if wlg_engins:
        jours_sem = [sem_debut + timedelta(days=i) for i in range(7)]

        th_s = (f"padding:0.4rem 0.35rem;border:1px solid {cb};text-align:center;"
                f"background:{ib};color:{hc};font-weight:600;font-size:0.76rem;")
        td_s = f"border:1px solid {cb};text-align:center;padding:0.3rem 0.25rem;font-size:0.74rem;"
        td_eng = (f"{td_s}background:{ib};color:{hc};text-align:left;"
                  f"padding:0.35rem 0.55rem;font-weight:700;font-size:0.9rem;")
        td_grp = (f"padding:0.3rem 0.55rem;background:{ib};color:{ic};"
                  f"font-size:0.72rem;font-weight:600;border:1px solid {cb};")

        grid = (
            f"<div style='overflow-x:auto'>"
            f"<table style='width:100%;border-collapse:collapse;'><thead><tr>"
            f"<th style='{th_s} text-align:left;min-width:58px;'>Engin</th>"
        )
        for jour in jours_sem:
            is_today = jour == today
            j_color = '#f59e0b' if is_today else hc
            j_bg = "background:rgba(245,158,11,0.12);" if is_today else ""
            j_bold = "font-weight:800;" if is_today else ""
            grid += (f"<th style='{th_s}color:{j_color};{j_bg}{j_bold}min-width:78px;'>"
                     f"{JOURS_FR[jour.weekday()]}<br>{jour.strftime('%d/%m')}</th>")
        grid += "</tr></thead><tbody>"

        prev_g = None
        for eng in wlg_engins:
            num = eng['numero_serie']
            g = num[0].upper()
            if g != prev_g and g in GROUPE_INFO:
                grp_icon, grp_label = GROUPE_INFO[g]
                grid += (f"<tr><td colspan='8' style='{td_grp}'>"
                         f"{grp_icon} {grp_label}</td></tr>")
                prev_g = g

            out_today, _, _ = _clef_status(num, clefs)
            marque = eng.get('marque', '')
            engin_cell = (
                f"<span style='font-weight:700;font-size:0.9rem;color:{hc};'>{esc(num)}</span>"
                + (f"<br><span style='font-weight:400;font-size:0.72rem;color:{ic};'>{esc(marque)}</span>" if marque else "")
            )
            grid += f"<tr><td style='{td_eng}'>{engin_cell}</td>"
            for jour in jours_sem:
                is_today_col = jour == today
                zone = _get_zone_for_day(num, jour, attributions_engins)
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

        # Légende zones
        all_zones = set()
        for e in wlg_engins:
            for j in jours_sem:
                z = _get_zone_for_day(e['numero_serie'], j, attributions_engins)
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

    # ── AJUSTER LE PLANNING ────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("✏️ Ajuster le planning — modifier la zone d'un engin"):
        if wlg_engins:
            with st.form(f"form_wlg_adj_{st.session_state.get('_fk', 0)}"):
                col1, col2 = st.columns(2)
                engin_opts = [
                    f"{e['numero_serie']} — {e.get('marque', '')} "
                    f"({_get_zone_for_day(e['numero_serie'], today, attributions_engins) or 'non actif'})"
                    for e in wlg_engins
                ]
                engin_adj = col1.selectbox("Engin *", engin_opts)
                zone_adj = col2.text_input("Nouvelle zone *", placeholder="SITE 1, LENI, PRAIRIE…")
                col3, col4 = st.columns(2)
                date_deb = col3.date_input("Du *", value=today)
                date_fin_v = col4.date_input("Au *", value=today)
                if st.form_submit_button("✅ Confirmer", type="primary"):
                    if zone_adj.strip() and date_fin_v >= date_deb:
                        num = engin_adj.split(" — ")[0]
                        date_deb_s = date_deb.strftime("%d/%m/%Y")
                        date_fin_s = date_fin_v.strftime("%d/%m/%Y")
                        ecraser_attributions_engin_periode(num, date_deb_s, date_fin_s)
                        add_attribution_engin(num, zone_adj.strip(), date_deb_s, date_fin_s, "Journée")
                        st.success(f"✅ {num} → {zone_adj.strip()} du {date_deb.strftime('%d/%m')} au {date_fin_v.strftime('%d/%m')}")
                        st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                        st.rerun()
                    else:
                        st.error("❌ Zone requise et date fin ≥ date début")
