import html
import streamlit as st
from datetime import datetime, timedelta
from database import (
    add_scooter, delete_scooter,
    add_attribution_scooter, update_attribution_scooter, delete_attribution_scooter,
    add_intervention_scooter
)


esc = html.escape


def render_scooters(page, t, scooters, attributions_scooters, categories_scooters, services, interventions_scooters):
    if page == "🛵 Saisir un scooter":
        _page_saisir(t, scooters, categories_scooters, services)
    elif page == "🔧 Attribuer un scooter":
        _page_attribuer(t, scooters, attributions_scooters, services)
    elif page == "🔨 Interventions Scooters":
        _page_interventions(t, scooters, interventions_scooters)


def _page_saisir(t, scooters, categories_scooters, services):
    st.markdown("# 🛵 Nouveau Scooter")
    st.markdown("<p class='page-intro'>Ajouter un scooter à votre flotte</p>", unsafe_allow_html=True)
    with st.form("form_sco"):
        st.markdown("**🛵 Informations scooter**")
        col1, col2 = st.columns(2)
        immat_sco = col1.text_input("Immatriculation *", placeholder="AB-123-CD")
        marque_sco = col2.text_input("Marque *", placeholder="Piaggio")
        type_sco = st.selectbox("Type *", categories_scooters)
        st.markdown("**🔧 Attribution initiale**")
        col3, col4 = st.columns(2)
        service_sco = col3.selectbox("Service *", services)
        date_retour_sco = col4.date_input("Date de retour prévue *", value=datetime.now() + timedelta(days=1))
        col5, col6, col7 = st.columns(3)
        date_s_sco = col5.date_input("Date de sortie", value=datetime.now())
        heure_s_sco = col6.time_input("Heure de sortie", value=datetime.now().time())
        casque_sco = col7.text_input("🪖 Casque attribué", placeholder="N° ou réf.")
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if immat_sco and marque_sco:
                if date_retour_sco < date_s_sco:
                    st.error("❌ La date de retour doit être après la date de sortie")
                else:
                    add_scooter(immat_sco, type_sco, marque_sco)
                    add_attribution_scooter(immat_sco, service_sco, date_s_sco.strftime("%d/%m/%Y"), heure_s_sco.strftime("%H:%M"), date_retour_sco.strftime("%d/%m/%Y"), casque_sco)
                    st.success(f"✅ {immat_sco} ajouté et attribué au service {service_sco} !")
                    st.rerun()
            else:
                st.error("❌ Champs requis")
    st.markdown("---")
    st.markdown("### 📋 Liste des scooters")
    if scooters:
        for sco in scooters:
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'><span style='color: {t['h1_color']}; font-weight: 600;'>{esc(sco['immatriculation'])}</span> <span style='color: {t['label_color']};'>— {esc(sco['type'])} {esc(sco['marque'])}</span></div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_sco_{sco['immatriculation']}"):
                delete_scooter(sco['immatriculation'])
                st.rerun()


def _page_attribuer(t, scooters, attributions_scooters, services):
    st.markdown("# 🔧 Attribution Scooter")
    st.markdown("<p class='page-intro'>Attribuer un scooter à un service</p>", unsafe_allow_html=True)
    if scooters:
        with st.form("form_attr_sco"):
            col1, col2 = st.columns(2)
            sco_sel = col1.selectbox("Scooter *", [f"{s['immatriculation']} - {s['type']} {s['marque']}" for s in scooters])
            service_sco = col2.selectbox("Service *", services)
            col3, col4 = st.columns(2)
            date_s_sco = col3.date_input("Date sortie", value=datetime.now())
            heure_s_sco = col4.time_input("Heure sortie", value=datetime.now().time())
            col5, col6 = st.columns(2)
            date_retour_sco = col5.date_input("Date de retour prévue *", value=datetime.now() + timedelta(days=1))
            casque_sco = col6.text_input("🪖 Casque attribué", placeholder="N° ou réf. du casque")
            if st.form_submit_button("✅ Confirmer", type="primary"):
                if date_retour_sco < date_s_sco:
                    st.error("❌ La date de retour doit être après la date de sortie")
                else:
                    add_attribution_scooter(sco_sel.split(" - ")[0], service_sco, date_s_sco.strftime("%d/%m/%Y"), heure_s_sco.strftime("%H:%M"), date_retour_sco.strftime("%d/%m/%Y"), casque_sco)
                    st.success("✅ Attribué !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun scooter")
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions_scooters:
        for i, attr in enumerate(reversed(attributions_scooters)):
            idx = len(attributions_scooters) - 1 - i
            retourne_badge = "✅" if attr.get('retourne') else "🔑"
            casque_txt = f" | 🪖 {attr.get('casque')}" if attr.get('casque') else ""
            with st.expander(f"{retourne_badge} {attr.get('immatriculation', '')} → {attr.get('service', '')} ({attr.get('date', '')}){casque_txt}"):
                with st.form(f"edit_attr_sco_{idx}"):
                    col1, col2 = st.columns(2)
                    srv_val = attr.get('service', '')
                    srv_idx = services.index(srv_val) if srv_val in services else 0
                    new_srv = col1.selectbox("Service", services, index=srv_idx, key=f"srv_sco_{idx}")
                    new_dr = col2.text_input("Date retour prévue", value=attr.get('date_retour_prevue', ''), key=f"dr_sco_{idx}")
                    col3, col4 = st.columns(2)
                    new_date = col3.text_input("Date sortie", value=attr.get('date', ''), key=f"ds_sco_{idx}")
                    new_heure = col4.text_input("Heure", value=attr.get('heure', ''), key=f"hs_sco_{idx}")
                    new_casque = st.text_input("🪖 Casque", value=attr.get('casque', ''), key=f"cq_sco_{idx}")
                    col_s, col_d = st.columns(2)
                    saved = col_s.form_submit_button("💾 Enregistrer")
                    deleted = col_d.form_submit_button("🗑️ Supprimer")
                if saved:
                    update_attribution_scooter(idx, {'service': new_srv, 'date_retour_prevue': new_dr, 'date': new_date, 'heure': new_heure, 'casque': new_casque})
                    st.success("✅ Modifié !")
                    st.rerun()
                if deleted:
                    delete_attribution_scooter(idx)
                    st.success("✅ Supprimé !")
                    st.rerun()
    else:
        st.info("Aucune attribution")


def _page_interventions(t, scooters, interventions_scooters):
    st.markdown("# 🔨 Interventions Scooters")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")
    if scooters:
        with st.form("form_interv_sco"):
            col1, col2 = st.columns(2)
            sco_sel_i = col1.selectbox("Scooter *", [f"{s['immatriculation']} - {s['type']} {s['marque']}" for s in scooters])
            type_i_sco = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
            col3, col4 = st.columns(2)
            date_i_sco = col3.date_input("Date *", value=datetime.now())
            heure_i_sco = col4.time_input("Heure *", value=datetime.now().time())
            comm_sco = st.text_area("Commentaire *", height=100)
            statut_sco = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if comm_sco:
                    add_intervention_scooter(sco_sel_i.split(" - ")[0], type_i_sco, date_i_sco.strftime("%d/%m/%Y"), heure_i_sco.strftime("%H:%M"), comm_sco, statut_sco)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun scooter enregistré")
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions_scooters:
        for interv in interventions_scooters[:20]:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv.get('immatriculation', '')} - {interv.get('type', '')} - {interv.get('date', '')}"):
                st.write(f"**Type:** {interv.get('type', '')} | **Statut:** {statut}")
                st.info(interv.get('commentaire', ''))
    else:
        st.info("Aucune intervention enregistrée")
