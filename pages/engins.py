"""
Pages Engins - Saisie, Attribution, Interventions.
"""
import streamlit as st
from datetime import datetime, timedelta

from database import (
    get_engins, add_engin, delete_engin,
    get_attributions_engins, add_attribution_engin, retourner_engin,
    update_attribution_engin, delete_attribution_engin,
    get_categories_engins, get_services,
    get_interventions_engins, add_intervention_engin,
    _is_engin_active_today
)
from styles import THEMES


def render_saisir():
    """Page : Saisir un engin."""
    t = THEMES[st.session_state['theme']]
    engins = get_engins()
    categories_engins = get_categories_engins()

    st.markdown("# 🚜 Nouvel Engin")
    st.markdown("<p class='page-intro'>Ajouter un engin à votre parc</p>", unsafe_allow_html=True)

    with st.form("form_engin"):
        col1, col2 = st.columns(2)
        num_serie = col1.text_input("N° Série / Identifiant *", placeholder="ENG-001")
        marque = col2.text_input("Marque *", placeholder="Caterpillar")
        type_e = st.selectbox("Type *", categories_engins)
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if num_serie and marque:
                add_engin(num_serie, type_e, marque)
                st.success(f"✅ {num_serie} ajouté !")
                st.rerun()
            else:
                st.error("❌ Champs requis")

    st.markdown("---")
    st.markdown("### 📋 Liste des engins")
    if engins:
        for eng in engins:
            col1, col2 = st.columns([5, 1])
            col1.markdown(
                f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; "
                f"border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'>"
                f"<span style='color: {t['h1_color']}; font-weight: 600;'>{eng['numero_serie']}</span> "
                f"<span style='color: {t['label_color']};'>— {eng['type']} {eng['marque']}</span></div>",
                unsafe_allow_html=True
            )
            if col2.button("🗑️", key=f"del_eng_{eng['numero_serie']}"):
                delete_engin(eng['numero_serie'])
                st.rerun()
    else:
        st.info("Aucun engin enregistré")


def render_attribuer():
    """Page : Attribuer un engin avec planning semaine."""
    t = THEMES[st.session_state['theme']]
    engins = get_engins()
    attributions_engins = get_attributions_engins()
    services = get_services()

    st.markdown("# 🔧 Planning Engins")
    st.markdown("<p class='page-intro'>Planification et suivi des attributions sur période</p>", unsafe_allow_html=True)

    # ── PLANNING SEMAINE ──────────────────────────────────────────────
    st.markdown("### 📅 Planning Semaine")
    if 'eng_sem_offset' not in st.session_state:
        st.session_state['eng_sem_offset'] = 0

    today_date = datetime.now().date()
    lundi = today_date - timedelta(days=today_date.weekday())
    semaine_debut = lundi + timedelta(weeks=st.session_state['eng_sem_offset'])
    semaine_fin_nav = semaine_debut + timedelta(days=6)

    col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])
    if col_nav1.button("← Préc.", key="eng_prev"):
        st.session_state['eng_sem_offset'] -= 1
        st.rerun()
    nav_color = t['h23_color']
    col_nav2.markdown(
        f"<h4 style='text-align:center; color:{nav_color}'>Semaine du {semaine_debut.strftime('%d/%m/%Y')} au {semaine_fin_nav.strftime('%d/%m/%Y')}</h4>",
        unsafe_allow_html=True
    )
    if col_nav3.button("Suiv. →", key="eng_next"):
        st.session_state['eng_sem_offset'] += 1
        st.rerun()

    if engins:
        _render_planning(t, engins, attributions_engins, services, today_date, semaine_debut)
    else:
        st.info("Aucun engin enregistré — ajoutez-en depuis 🚜 Saisir un engin")

    # ── NOUVELLE ATTRIBUTION ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ➕ Nouvelle Attribution")
    if engins:
        with st.form("form_attr_engin"):
            col1, col2 = st.columns(2)
            engin_sel = col1.selectbox("Engin *", [f"{e['numero_serie']} - {e['type']} {e['marque']}" for e in engins])
            service_sel = col2.selectbox("Service *", services)
            col3, col4, col5 = st.columns(3)
            date_deb = col3.date_input("Date début *", value=datetime.now())
            date_fin_inp = col4.date_input("Date fin *", value=datetime.now())
            periode_sel = col5.selectbox("Période *", ["Journée", "Matin", "Après-midi"])
            if st.form_submit_button("✅ Confirmer", type="primary"):
                if date_fin_inp >= date_deb:
                    add_attribution_engin(
                        engin_sel.split(" - ")[0], service_sel,
                        date_deb.strftime("%d/%m/%Y"),
                        date_fin_inp.strftime("%d/%m/%Y"),
                        periode_sel
                    )
                    st.success("✅ Attribution enregistrée !")
                    st.rerun()
                else:
                    st.error("❌ La date de fin doit être ≥ à la date de début")

    # ── HISTORIQUE ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions_engins:
        for i, attr in enumerate(reversed(attributions_engins)):
            idx = len(attributions_engins) - 1 - i
            retourne_badge = "✅" if attr.get('retourne') else "🔑"
            date_fin_lbl = attr.get('date_fin', '')
            periode_lbl = attr.get('periode', '')
            periode_str = f" [{periode_lbl}]" if periode_lbl else ""
            date_str = attr.get('date', '')
            plage_str = f"{date_str} → {date_fin_lbl}" if date_fin_lbl and date_fin_lbl != date_str else date_str
            label_exp = f"{retourne_badge} {attr.get('numero_serie','')} — {attr.get('service','')} | {plage_str}{periode_str}"
            with st.expander(label_exp):
                with st.form(f"edit_attr_eng_{idx}"):
                    col1, col2 = st.columns(2)
                    srv_val = attr.get('service', '')
                    srv_idx = services.index(srv_val) if srv_val in services else 0
                    new_srv = col1.selectbox("Service", services, index=srv_idx, key=f"srv_eng_{idx}")
                    per_opts = ["Journée", "Matin", "Après-midi"]
                    per_val = attr.get('periode', 'Journée')
                    per_idx = per_opts.index(per_val) if per_val in per_opts else 0
                    new_per = col2.selectbox("Période", per_opts, index=per_idx, key=f"per_eng_{idx}")
                    col3, col4 = st.columns(2)
                    new_date = col3.text_input("Date début (JJ/MM/AAAA)", value=attr.get('date', ''), key=f"ds_eng_{idx}")
                    new_datefin = col4.text_input("Date fin (JJ/MM/AAAA)", value=attr.get('date_fin', ''), key=f"df_eng_{idx}")
                    col_s, col_d = st.columns(2)
                    saved = col_s.form_submit_button("💾 Enregistrer")
                    deleted = col_d.form_submit_button("🗑️ Supprimer")
                if saved:
                    update_attribution_engin(idx, {'service': new_srv, 'date': new_date, 'date_fin': new_datefin, 'periode': new_per})
                    st.success("✅ Modifié !")
                    st.rerun()
                if deleted:
                    delete_attribution_engin(idx)
                    st.success("✅ Supprimé !")
                    st.rerun()
    else:
        st.info("Aucune attribution enregistrée")


def _render_planning(t, engins, attributions_engins, services, today_date, semaine_debut):
    """Affiche le planning semaine."""
    JOURS_FR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    jours_sem = [semaine_debut + timedelta(days=i) for i in range(7)]
    _PALETTE = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316']
    svc_color = {s: _PALETTE[i % len(_PALETTE)] for i, s in enumerate(services)}

    def _get_slot(num_serie, day, periode):
        for a in attributions_engins:
            if a.get('numero_serie') != num_serie or a.get('retourne'):
                continue
            try:
                dd = datetime.strptime(a['date'], "%d/%m/%Y").date()
                df_d = datetime.strptime(a.get('date_fin', a['date']), "%d/%m/%Y").date()
                if dd <= day <= df_d:
                    p = a.get('periode', 'Journée')
                    if p == 'Journée' or p == periode:
                        return a['service']
            except Exception:
                pass
        return None

    cb = t['card_border']
    ib = t['input_bg']
    hc = t['h23_color']
    ic = t['intro_color']
    th_s = f"padding:0.45rem 0.4rem; border:1px solid {cb}; text-align:center; background:{ib}; color:{hc}; font-weight:600; font-size:0.8rem;"
    td_s = f"border:1px solid {cb}; text-align:center; padding:0.3rem 0.25rem; font-size:0.75rem;"
    td_eng_s = f"{td_s} background:{ib}; color:{hc}; text-align:left; padding:0.4rem 0.5rem; min-width:110px;"
    td_slot_s = f"{td_s} background:{ib}; color:{ic}; min-width:52px;"

    html = f"<div style='overflow-x:auto'><table style='width:100%; border-collapse:collapse;'><thead><tr>"
    html += f"<th style='{th_s} text-align:left; min-width:110px;'>Engin</th>"
    html += f"<th style='{th_s} min-width:52px;'>Slot</th>"
    for i, jour in enumerate(jours_sem):
        jour_color = '#f59e0b' if jour == today_date else hc
        html += f"<th style='{th_s} color:{jour_color}; min-width:88px;'>{JOURS_FR[i]}<br>{jour.strftime('%d/%m')}</th>"
    html += "</tr></thead><tbody>"

    for eng in engins:
        num = eng.get('numero_serie', '')
        eng_label = f"<b>{num}</b><br><small style='color:{ic}'>{eng.get('type','')} {eng.get('marque','')}</small>"
        for pi, (periode, icon) in enumerate([('Matin', '🌅'), ('Après-midi', '🌇')]):
            html += "<tr>"
            if pi == 0:
                html += f"<td rowspan='2' style='{td_eng_s}'>{eng_label}</td>"
            html += f"<td style='{td_slot_s}'>{icon} {periode}</td>"
            for jour in jours_sem:
                svc = _get_slot(num, jour, periode)
                if svc:
                    bg = svc_color.get(svc, '#6b7280')
                    html += f"<td style='{td_s} background:{bg}; color:white; font-weight:500;'>{svc}</td>"
                else:
                    html += f"<td style='{td_s} color:{ic};'>—</td>"
            html += "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

    legende = " ".join(
        f"<span style='background:{svc_color.get(s,'#6b7280')}; color:white; padding:0.2rem 0.6rem; border-radius:12px; font-size:0.75rem; margin-right:0.3rem;'>{s}</span>"
        for s in services
    )
    st.markdown(f"<div style='margin-top:0.6rem'>{legende}</div>", unsafe_allow_html=True)


def render_interventions():
    """Page : Interventions engins."""
    t = THEMES[st.session_state['theme']]
    engins = get_engins()
    interventions_engins = get_interventions_engins()

    st.markdown("# 🔨 Interventions Engins")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions sur engins</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")

    if engins:
        with st.form("form_interv_engin"):
            col1, col2 = st.columns(2)
            eng_sel = col1.selectbox("Engin *", [f"{e['numero_serie']} - {e['type']} {e['marque']}" for e in engins])
            type_i = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
            col3, col4 = st.columns(2)
            date_i = col3.date_input("Date *", value=datetime.now())
            heure_i = col4.time_input("Heure *", value=datetime.now().time())
            comm = st.text_area("Commentaire *", height=100)
            statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if comm:
                    add_intervention_engin(
                        eng_sel.split(" - ")[0], type_i,
                        date_i.strftime("%d/%m/%Y"), heure_i.strftime("%H:%M"),
                        comm, statut
                    )
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun engin enregistré")

    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions_engins:
        for interv in interventions_engins[:20]:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv.get('numero_serie', '')} - {interv.get('type', '')} - {interv.get('date', '')}"):
                st.write(f"**Type:** {interv.get('type', '')} | **Statut:** {statut}")
                st.info(interv.get('commentaire', ''))
    else:
        st.info("Aucune intervention enregistrée")
