import html
import re
import streamlit as st
from datetime import datetime
from database import (
    add_intervention_engin, add_intervention_golfette,
    update_intervention_engin_statut, update_intervention_golfette_statut,
)

esc = html.escape

TYPES_INTERV = ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"]
STATUTS = ["En cours", "Terminée", "En attente"]


def _is_wlg(num):
    return bool(re.match(r'^[CTN]\d+$', str(num)))


def _render_fiche_contact(t, contacts, categorie):
    """Affiche la fiche contacts pour une catégorie (engins ou golfettes)."""
    fiches = [c for c in contacts if c.get('categorie') == categorie]
    if not fiches:
        return
    ic = t['intro_color']
    hc = t['h23_color']
    cb = t['card_border']
    bg = t['card_bg']
    label = "🚜 Contacts Engins" if categorie == 'engins' else "⛳ Contacts Golfettes"
    cards = "".join(
        f"<div style='flex:1;min-width:160px;'>"
        f"<span style='color:{hc};font-weight:700;font-size:0.95rem;'>{esc(c.get('nom',''))}</span><br>"
        f"<span style='color:{ic};font-size:0.85rem;'>📞 <b>{esc(c.get('telephone',''))}</b></span><br>"
        f"<span style='color:{ic};font-size:0.82rem;'>🕐 {esc(c.get('horaires',''))}</span>"
        f"</div>"
        for c in fiches
    )
    st.markdown(
        f"<div style='background:{bg};border:1px solid {cb};border-left:4px solid #3b82f6;"
        f"border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:1rem;'>"
        f"<div style='color:#3b82f6;font-weight:700;font-size:0.82rem;margin-bottom:0.5rem;'>"
        f"📋 {label}</div>"
        f"<div style='display:flex;gap:2rem;flex-wrap:wrap;'>{cards}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_interventions_wlg(t, engins, golfettes, interventions_engins, interventions_golfettes, contacts_wlg=None):
    st.markdown("# 🔨 Interventions WLG26")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions sur engins et golfettes</p>",
                unsafe_allow_html=True)

    contacts = contacts_wlg or []
    # Pré-remplissage formulaire depuis le premier contact de chaque catégorie
    first_eng = next((c for c in contacts if c.get('categorie') == 'engins'), {})
    first_golf = next((c for c in contacts if c.get('categorie') == 'golfettes'), {})
    default_tel_eng = first_eng.get('telephone', '')
    default_hor_eng = first_eng.get('horaires', '')
    default_tel_golf = first_golf.get('telephone', '')
    default_hor_golf = first_golf.get('horaires', '')

    wlg_engins = [e for e in engins if _is_wlg(e.get('numero_serie', ''))]
    # On garde l'index d'origine pour pouvoir update le statut (idx = ligne dans la feuille)
    wlg_interv_engins = [(idx, i) for idx, i in enumerate(interventions_engins) if _is_wlg(i.get('numero_serie', ''))]
    wlg_interv_golf = list(enumerate(interventions_golfettes))

    # Métriques
    en_cours_e = sum(1 for _, i in wlg_interv_engins if i.get('statut') == 'En cours')
    en_cours_g = sum(1 for _, i in wlg_interv_golf if i.get('statut') == 'En cours')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚜 Interventions engins", len(wlg_interv_engins))
    c2.metric("⛳ Interventions golfettes", len(wlg_interv_golf))
    c3.metric("🔴 En cours (engins)", en_cours_e)
    c4.metric("🔴 En cours (golfettes)", en_cours_g)

    st.markdown("---")

    tab_engins, tab_golf = st.tabs(["🚜 Engins", "⛳ Golfettes"])

    # ── ONGLET ENGINS ─────────────────────────────────────────────────────
    with tab_engins:
        _render_fiche_contact(t, contacts, 'engins')
        st.markdown("### ➕ Déclarer une intervention")
        if wlg_engins:
            with st.form(f"form_interv_engin_wlg_{st.session_state.get('_fk', 0)}"):
                col1, col2 = st.columns(2)
                eng_opts = [f"{e['numero_serie']} — {e.get('marque', '')}" for e in wlg_engins]
                eng_sel = col1.selectbox("Engin *", eng_opts)
                type_i = col2.selectbox("Type *", TYPES_INTERV)
                col3, col4 = st.columns(2)
                date_i = col3.date_input("Date *", value=datetime.now())
                heure_i = col4.time_input("Heure *", value=datetime.now().time())
                comm = st.text_area("Description *", height=90, placeholder="Décrivez le problème ou l'intervention…")
                col5, col6, col7 = st.columns(3)
                statut = col5.selectbox("Statut", STATUTS)
                telephone = col6.text_input("📞 N° à appeler", value=default_tel_eng, placeholder="06 XX XX XX XX")
                horaires = col7.text_input("🕐 Horaires", value=default_hor_eng, placeholder="8h-12h / 14h-17h")
                if st.form_submit_button("✅ Enregistrer", type="primary"):
                    if comm.strip():
                        num = eng_sel.split(" — ")[0]
                        add_intervention_engin(
                            num, type_i,
                            date_i.strftime("%d/%m/%Y"),
                            heure_i.strftime("%H:%M"),
                            comm.strip(), statut,
                            telephone.strip(), horaires.strip()
                        )
                        st.success(f"✅ Intervention enregistrée pour {num}")
                        st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                        st.rerun()
                    else:
                        st.error("❌ La description est requise")
        else:
            st.info("Aucun engin WLG enregistré")

        st.markdown("---")
        st.markdown("### 📋 Historique")
        _render_liste_interventions(t, wlg_interv_engins, id_key='numero_serie', kind='engin')

    # ── ONGLET GOLFETTES ──────────────────────────────────────────────────
    with tab_golf:
        _render_fiche_contact(t, contacts, 'golfettes')
        st.markdown("### ➕ Déclarer une intervention")
        if golfettes:
            with st.form(f"form_interv_golf_wlg_{st.session_state.get('_fk', 0)}"):
                col1, col2 = st.columns(2)
                golf_opts = [f"{g['numero_serie']} — {g.get('type', '')}" for g in golfettes]
                golf_sel = col1.selectbox("Golfette *", golf_opts)
                type_i = col2.selectbox("Type *", TYPES_INTERV)
                col3, col4 = st.columns(2)
                date_i = col3.date_input("Date *", value=datetime.now(), key="golf_date")
                heure_i = col4.time_input("Heure *", value=datetime.now().time(), key="golf_heure")
                comm = st.text_area("Description *", height=90,
                                    placeholder="Décrivez le problème ou l'intervention…",
                                    key="golf_comm")
                col5g, col6g, col7g = st.columns(3)
                statut = col5g.selectbox("Statut", STATUTS, key="golf_statut")
                telephone = col6g.text_input("📞 N° à appeler", value=default_tel_golf, placeholder="06 XX XX XX XX", key="golf_tel")
                horaires = col7g.text_input("🕐 Horaires", value=default_hor_golf, placeholder="8h-12h / 14h-17h", key="golf_hor")
                if st.form_submit_button("✅ Enregistrer", type="primary"):
                    if comm.strip():
                        num = golf_sel.split(" — ")[0]
                        add_intervention_golfette(
                            num, type_i,
                            date_i.strftime("%d/%m/%Y"),
                            heure_i.strftime("%H:%M"),
                            comm.strip(), statut,
                            telephone.strip(), horaires.strip()
                        )
                        st.success(f"✅ Intervention enregistrée pour {num}")
                        st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                        st.rerun()
                    else:
                        st.error("❌ La description est requise")
        else:
            st.info("Aucune golfette enregistrée")

        st.markdown("---")
        st.markdown("### 📋 Historique")
        _render_liste_interventions(t, wlg_interv_golf, id_key='numero_serie', kind='golfette')


def _render_liste_interventions(t, items, id_key, kind):
    """items: list of (idx, intervention_dict). kind: 'engin' | 'golfette'."""
    if not items:
        st.info("Aucune intervention enregistrée")
        return

    en_cours = [(idx, i) for idx, i in items if i.get('statut') == 'En cours']
    autres = [(idx, i) for idx, i in items if i.get('statut') != 'En cours']

    if en_cours:
        st.markdown("**🔴 En cours**")
        for idx, i in en_cours:
            _render_card(t, idx, i, id_key, kind)
        if autres:
            st.markdown("---")

    if autres:
        with st.expander(f"📋 Terminées / En attente ({len(autres)})"):
            for idx, i in reversed(autres):
                _render_card(t, idx, i, id_key, kind)


def _render_card(t, idx, i, id_key, kind):
    statut = i.get('statut', '')
    color = '#ef4444' if statut == 'En cours' else '#10b981' if statut == 'Terminée' else '#f59e0b'
    emoji = '🔴' if statut == 'En cours' else '✅' if statut == 'Terminée' else '⏸️'
    telephone = i.get('telephone', '') or ''
    horaires = i.get('horaires', '') or ''
    contact_line = ''
    if telephone or horaires:
        parts = []
        if telephone:
            parts.append(f"📞 <b>{esc(telephone)}</b>")
        if horaires:
            parts.append(f"🕐 {esc(horaires)}")
        contact_line = (
            f"<br><span style='color:{t['intro_color']};font-size:0.82rem;'>"
            + " &nbsp;·&nbsp; ".join(parts)
            + "</span>"
        )
    st.markdown(
        f"<div style='background:{t['card_bg']};border:1px solid {t['card_border']};"
        f"border-left:4px solid {color};border-radius:10px;"
        f"padding:0.75rem 1.2rem;margin-bottom:0.25rem;'>"
        f"<span style='color:{t['h1_color']};font-weight:700;'>{esc(i.get(id_key,''))}</span>"
        f"<span style='color:{t['label_color']};margin-left:0.8rem;'>{esc(i.get('type',''))}</span>"
        f"<span style='color:{t['intro_color']};margin-left:0.8rem;font-size:0.82rem;'>"
        f"📅 {esc(i.get('date',''))} {esc(i.get('heure',''))}</span>"
        f"<span style='color:{color};margin-left:0.8rem;font-size:0.82rem;'>{emoji} {esc(statut)}</span><br>"
        f"<span style='color:{t['text_color']};font-size:0.85rem;'>💬 {esc(i.get('commentaire',''))}</span>"
        f"{contact_line}"
        f"</div>",
        unsafe_allow_html=True,
    )
    cur_idx = STATUTS.index(statut) if statut in STATUTS else 0
    col_sel, _ = st.columns([1, 3])
    new_statut = col_sel.selectbox(
        "Statut",
        STATUTS,
        index=cur_idx,
        key=f"statut_{kind}_{idx}",
        label_visibility="collapsed",
    )
    if new_statut != statut:
        if kind == 'engin':
            update_intervention_engin_statut(idx, new_statut)
        else:
            update_intervention_golfette_statut(idx, new_statut)
        st.rerun()
