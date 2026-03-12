import html
import streamlit as st
from datetime import datetime, timedelta
from database import (
    add_vehicule, delete_vehicule,
    add_attribution, update_attribution, delete_attribution,
    add_bon_carburant, update_bon_carburant, delete_bon_carburant,
    add_intervention, AGENCES, save_fiche_vehicule
)
from pdf import generer_pdf_bon

esc = html.escape


def render_vehicules(page, t, vehicules, attributions, categories, services, bons_carburant, interventions, fiches_vehicules):
    if page == "➕ Saisir un véhicule":
        _page_saisir(t, vehicules, categories)
    elif page == "🔧 Attribuer un véhicule":
        _page_attribuer(t, vehicules, attributions, services)
    elif page == "⛽ Bons de Carburant":
        _page_carburant(t, vehicules, attributions, services, bons_carburant)
    elif page == "🔨 Pannes & Interventions":
        _page_interventions(t, vehicules, interventions)
    elif page == "📋 Fiche véhicule":
        _page_fiche(t, vehicules, fiches_vehicules, interventions, bons_carburant, attributions)


def _page_saisir(t, vehicules, categories):
    st.markdown("# ➕ Nouveau Véhicule")
    st.markdown("<p class='page-intro'>Ajouter un véhicule à votre flotte</p>", unsafe_allow_html=True)
    with st.form("form_vh"):
        col1, col2 = st.columns(2)
        immat = col1.text_input("Immatriculation *", placeholder="AB-123-CD")
        marque = col2.text_input("Marque *", placeholder="Renault")
        col3, col4 = st.columns(2)
        type_v = col3.selectbox("Type *", categories)
        agence = col4.selectbox("Agence *", AGENCES)
        if st.form_submit_button("✅ Enregistrer", type="primary"):
            if immat and marque:
                add_vehicule(immat, type_v, marque, agence)
                st.success(f"✅ {immat} ajouté !")
                st.rerun()
            else:
                st.error("❌ Champs requis")
    st.markdown("---")
    st.markdown("### 📋 Liste des véhicules")
    if vehicules:
        for vh in vehicules:
            col1, col2 = st.columns([5, 1])
            agence_vh = vh.get('agence', '')
            agence_str = f" · 📍 {esc(agence_vh)}" if agence_vh else ""
            col1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 10px; padding: 1rem; margin-bottom: 0.5rem;'><span style='color: {t['h1_color']}; font-weight: 600;'>{esc(vh['immatriculation'])}</span> <span style='color: {t['label_color']};'>— {esc(vh['type'])} {esc(vh['marque'])}{agence_str}</span></div>", unsafe_allow_html=True)
            if col2.button("🗑️", key=f"del_{vh['immatriculation']}"):
                delete_vehicule(vh['immatriculation'])
                st.rerun()


def _page_attribuer(t, vehicules, attributions, services):
    st.markdown("# 🔧 Attribution")
    st.markdown("<p class='page-intro'>Attribuer un véhicule à un service</p>", unsafe_allow_html=True)
    if vehicules:
        with st.form("form_attr"):
            col1, col2 = st.columns(2)
            immat_sel = col1.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules])
            service = col2.selectbox("Service *", services)
            col3, col4 = st.columns(2)
            date_s = col3.date_input("Date sortie", value=datetime.now())
            heure_s = col4.time_input("Heure sortie", value=datetime.now().time())
            date_retour = st.date_input("Date de retour prévue *", value=datetime.now() + timedelta(days=1))
            if st.form_submit_button("✅ Confirmer", type="primary"):
                if date_retour < date_s:
                    st.error("❌ La date de retour doit être après la date de sortie")
                else:
                    add_attribution(immat_sel.split(" - ")[0], service, date_s.strftime("%d/%m/%Y"), heure_s.strftime("%H:%M"), date_retour.strftime("%d/%m/%Y"))
                    st.success("✅ Attribué !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule")
    st.markdown("---")
    st.markdown("### 📜 Historique")
    if attributions:
        vh_map = {v['immatriculation']: v for v in vehicules}
        for i, attr in enumerate(reversed(attributions)):
            idx = len(attributions) - 1 - i
            retourne_badge = "✅" if attr.get('retourne') else "🔑"
            immat_attr = attr.get('immatriculation', '')
            agence_attr = vh_map.get(immat_attr, {}).get('agence', '')
            agence_label = f" · 📍 {agence_attr}" if agence_attr else ""
            with st.expander(f"{retourne_badge} {immat_attr}{agence_label} → {attr.get('service', '')} ({attr.get('date', '')})"):
                with st.form(f"edit_attr_vh_{idx}"):
                    col1, col2 = st.columns(2)
                    srv_val = attr.get('service', '')
                    srv_idx = services.index(srv_val) if srv_val in services else 0
                    new_srv = col1.selectbox("Service", services, index=srv_idx, key=f"srv_vh_{idx}")
                    new_dr = col2.text_input("Date retour prévue", value=attr.get('date_retour_prevue', ''), key=f"dr_vh_{idx}")
                    col3, col4 = st.columns(2)
                    new_date = col3.text_input("Date sortie", value=attr.get('date', ''), key=f"ds_vh_{idx}")
                    new_heure = col4.text_input("Heure", value=attr.get('heure', ''), key=f"hs_vh_{idx}")
                    col_s, col_d = st.columns(2)
                    saved = col_s.form_submit_button("💾 Enregistrer")
                    deleted = col_d.form_submit_button("🗑️ Supprimer")
                if saved:
                    update_attribution(idx, {'service': new_srv, 'date_retour_prevue': new_dr, 'date': new_date, 'heure': new_heure})
                    st.success("✅ Modifié !")
                    st.rerun()
                if deleted:
                    delete_attribution(idx)
                    st.success("✅ Supprimé !")
                    st.rerun()
    else:
        st.info("Aucune attribution")


def _page_carburant(t, vehicules, attributions, services, bons_carburant):
    st.markdown("# ⛽ Bons de Carburant")
    st.markdown("<p class='page-intro'>Générer et suivre les bons</p>", unsafe_allow_html=True)
    st.markdown("### 📝 Générer un Bon")
    service_bon = st.selectbox("Service *", services, key="service_bon")
    vh_srv = [f"{v['immatriculation']} - {v['type']} {v['marque']}" for attr in attributions if attr.get('service') == service_bon and not attr.get('retourne') for v in vehicules if v['immatriculation'] == attr['immatriculation']]
    if vh_srv:
        with st.form("form_bon"):
            vh_sel = st.selectbox("Véhicule *", vh_srv)
            col1, col2 = st.columns(2)
            date_bon = col1.date_input("Date *", value=datetime.now())
            num_carte = col2.text_input("N° Carte *")
            col3, col4 = st.columns(2)
            conducteur_prenom = col3.text_input("Prénom *")
            conducteur_nom = col4.text_input("Nom *")
            logo_url = st.text_input("URL logo (optionnel)")
            notes = st.text_area("Notes", height=80)
            if st.form_submit_button("✅ Générer", type="primary"):
                if conducteur_nom and conducteur_prenom and num_carte:
                    num_bon = f"BC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    bon = {"numero_bon": num_bon, "immatriculation": vh_sel.split(" - ")[0], "service": service_bon, "date": date_bon.strftime("%d/%m/%Y"), "numero_carte": num_carte, "conducteur_nom": conducteur_nom, "conducteur_prenom": conducteur_prenom, "type_carburant": "", "volume": "", "montant": "", "notes": notes, "statut": "Non saisi"}
                    add_bon_carburant(bon)
                    st.session_state.dernier_bon = {'bon': bon, 'conducteur_nom': conducteur_nom, 'conducteur_prenom': conducteur_prenom, 'logo_url': logo_url}
                    st.success(f"✅ Bon {num_bon} généré !")
                    st.rerun()
                else:
                    st.error("❌ Champs requis")
        if 'dernier_bon' in st.session_state:
            bon = st.session_state.dernier_bon['bon']
            st.markdown(f"<div style='background: {t['input_bg']}; border-radius: 16px; padding: 2rem; margin: 1rem 0; border: 1px solid {t['card_border']};'><h3 style='color: {t['h1_color']}; text-align: center;'>📄 BON DE CARBURANT</h3><p style='color: {t['label_color']};'><strong style='color: {t['strong_color']};'>N°:</strong> {esc(bon['numero_bon'])} | <strong style='color: {t['strong_color']};'>Véhicule:</strong> {esc(bon['immatriculation'])} | <strong style='color: #ef4444;'>Carte N°{esc(bon['numero_carte'])}</strong></p></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                pdf = generer_pdf_bon(bon, st.session_state.dernier_bon['conducteur_nom'], st.session_state.dernier_bon['conducteur_prenom'], st.session_state.dernier_bon.get('logo_url'))
                st.download_button("📥 Télécharger PDF", pdf, f"bon_{bon['numero_bon']}.pdf", "application/pdf", type="primary")
            with col2:
                if st.button("🔄 Nouveau bon"):
                    del st.session_state.dernier_bon
                    st.rerun()
    else:
        st.warning(f"⚠️ Aucun véhicule attribué au service {service_bon}")

    st.markdown("---")
    st.markdown("### 📥 Saisir données retour")
    non_saisis = [b for b in bons_carburant if b.get('statut') == "Non saisi"]
    if non_saisis:
        with st.form("form_saisie"):
            bon_sel = st.selectbox("Bon *", [f"{b['numero_bon']} - {b['immatriculation']}" for b in non_saisis])
            col1, col2, col3 = st.columns(3)
            type_carb = col1.selectbox("Carburant *", ["Diesel", "SP95", "SP98", "GPL", "Électrique"])
            volume = col2.number_input("Volume (L) *", min_value=0.0, step=0.1)
            montant = col3.number_input("Montant (€) *", min_value=0.0, step=0.01)
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if volume > 0:
                    update_bon_carburant(bon_sel.split(" - ")[0], type_carb, volume, montant)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.info("✅ Tous les bons sont saisis")

    st.markdown("---")
    st.markdown("### 📋 Historique")
    if bons_carburant:
        h = st.columns([2, 1.5, 1, 1.2, 0.8, 0.9, 1, 0.5])
        for col, label in zip(h, ["N° Bon", "Véhicule", "Date", "Carburant", "Vol. (L)", "Montant (€)", "Statut", ""]):
            col.markdown(f"<small><b>{label}</b></small>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.25rem 0 0.5rem 0'>", unsafe_allow_html=True)
        for bon in reversed(bons_carburant):
            num = bon.get('numero_bon', '')
            statut = bon.get('statut', '')
            statut_color = '#ef4444' if statut == 'Non saisi' else '#10b981'
            c = st.columns([2, 1.5, 1, 1.2, 0.8, 0.9, 1, 0.5])
            c[0].markdown(f"<small>{esc(num)}</small>", unsafe_allow_html=True)
            c[1].markdown(f"<small>{esc(bon.get('immatriculation', ''))}</small>", unsafe_allow_html=True)
            c[2].markdown(f"<small>{esc(bon.get('date', ''))}</small>", unsafe_allow_html=True)
            c[3].markdown(f"<small>{esc(bon.get('type_carburant', '-'))}</small>", unsafe_allow_html=True)
            c[4].markdown(f"<small>{esc(bon.get('volume', '-'))}</small>", unsafe_allow_html=True)
            c[5].markdown(f"<small>{esc(bon.get('montant', '-'))}</small>", unsafe_allow_html=True)
            c[6].markdown(f"<small style='color:{statut_color}'>{esc(statut)}</small>", unsafe_allow_html=True)
            if c[7].button("🗑️", key=f"del_bon_{num}"):
                delete_bon_carburant(num)
                st.rerun()
    else:
        st.info("Aucun bon enregistré")


def _page_interventions(t, vehicules, interventions):
    st.markdown("# 🔨 Interventions Véhicules")
    st.markdown("<p class='page-intro'>Déclarer et suivre les interventions</p>", unsafe_allow_html=True)
    st.markdown("### ➕ Déclarer")
    if vehicules:
        with st.form("form_interv"):
            col1, col2 = st.columns(2)
            vh_sel = col1.selectbox("Véhicule *", [f"{v['immatriculation']} - {v['type']} {v['marque']}" for v in vehicules])
            type_i = col2.selectbox("Type *", ["Panne", "Entretien", "Réparation", "Contrôle", "Autre"])
            col3, col4 = st.columns(2)
            date_i = col3.date_input("Date *", value=datetime.now())
            heure_i = col4.time_input("Heure *", value=datetime.now().time())
            comm = st.text_area("Commentaire *", height=100)
            statut = st.selectbox("Statut", ["En cours", "Terminée", "En attente"])
            if st.form_submit_button("✅ Enregistrer", type="primary"):
                if comm:
                    add_intervention(vh_sel.split(" - ")[0], type_i, date_i.strftime("%d/%m/%Y"), heure_i.strftime("%H:%M"), comm, statut)
                    st.success("✅ Enregistré !")
                    st.rerun()
    else:
        st.warning("⚠️ Aucun véhicule enregistré")
    st.markdown("---")
    st.markdown("### 📋 Historique")
    if interventions:
        for interv in interventions[:20]:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            with st.expander(f"{emoji} {interv.get('immatriculation', '')} - {interv.get('type', '')} - {interv.get('date', '')}"):
                st.write(f"**Type:** {interv.get('type', '')} | **Statut:** {statut}")
                st.info(interv.get('commentaire', ''))


def _page_fiche(t, vehicules, fiches_vehicules, interventions, bons_carburant, attributions=None):
    st.markdown("# 📋 Fiche Véhicule")
    st.markdown("<p class='page-intro'>Contrat, état des lieux et historique par véhicule</p>", unsafe_allow_html=True)

    if not vehicules:
        st.warning("⚠️ Aucun véhicule enregistré")
        return

    vh_options = [f"{v['immatriculation']} — {v.get('type', '')} {v.get('marque', '')} · 📍 {v.get('agence', '')}" for v in vehicules]
    sel = st.selectbox("Sélectionner un véhicule", vh_options)
    immat = sel.split(" — ")[0]
    vh = next((v for v in vehicules if v['immatriculation'] == immat), {})
    fiche = next((f for f in fiches_vehicules if f.get('immatriculation') == immat), {})

    st.markdown(f"""
    <div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 12px; padding: 1.2rem; margin: 1rem 0;'>
        <span style='color: {t['h1_color']}; font-size: 1.3rem; font-weight: 700;'>{esc(immat)}</span>
        <span style='color: {t['label_color']};'> — {esc(vh.get('type',''))} {esc(vh.get('marque',''))} · 📍 {esc(vh.get('agence',''))}</span>
    </div>
    """, unsafe_allow_html=True)

    attr_active = next((a for a in (attributions or []) if a.get('immatriculation') == immat and not a.get('retourne')), None)
    if attr_active:
        st.markdown(f"""
        <div style='background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.4); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;'>
            <span style='color: #10b981; font-weight: 600;'>🔑 Actuellement attribué</span><br>
            <span style='color: {t['label_color']};'>Service : <strong>{esc(attr_active.get('service','?'))}</strong> · Sorti le {esc(attr_active.get('date','?'))} · Retour prévu le {esc(attr_active.get('date_retour_prevue','?'))}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background: rgba(100,100,100,0.08); border: 1px solid {t['card_border']}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;'>
            <span style='color: {t['label_color']};'>🟢 Véhicule disponible — aucune attribution en cours</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📄 Contrat & État des lieux")
    with st.form("form_fiche"):
        contrat_url = st.text_input("🔗 Lien contrat (OneDrive)", value=fiche.get('contrat_url', ''), placeholder="https://...")
        photos_entree = st.text_area("📷 Photos état des lieux d'entrée (un lien par ligne)", value=fiche.get('photos_entree', '').replace(',', '\n'), height=100, placeholder="https://...")
        photos_sortie = st.text_area("📷 Photos état des lieux de sortie (un lien par ligne)", value=fiche.get('photos_sortie', '').replace(',', '\n'), height=100, placeholder="https://...")
        notes = st.text_area("📝 Notes", value=fiche.get('notes', ''), height=80)
        if st.form_submit_button("💾 Enregistrer la fiche", type="primary"):
            save_fiche_vehicule(
                immat,
                contrat_url,
                ','.join([l.strip() for l in photos_entree.splitlines() if l.strip()]),
                ','.join([l.strip() for l in photos_sortie.splitlines() if l.strip()]),
                notes
            )
            st.success("✅ Fiche enregistrée !")
            st.rerun()

    if fiche.get('contrat_url'):
        st.markdown(f"[📄 Voir le contrat]({fiche['contrat_url']})", unsafe_allow_html=False)

    if fiche.get('photos_entree'):
        st.markdown("**Photos entrée :**")
        for url in fiche['photos_entree'].split(','):
            if url.strip():
                st.markdown(f"- [🔗 Photo]({url.strip()})")

    if fiche.get('photos_sortie'):
        st.markdown("**Photos sortie :**")
        for url in fiche['photos_sortie'].split(','):
            if url.strip():
                st.markdown(f"- [🔗 Photo]({url.strip()})")

    st.markdown("---")
    st.markdown("### 🔨 Interventions")
    vh_interventions = [i for i in interventions if i.get('immatriculation') == immat]
    if vh_interventions:
        for interv in vh_interventions:
            statut = interv.get('statut', '')
            emoji = "🔴" if statut == "En cours" else "✅" if statut == "Terminée" else "⏸️"
            st.markdown(f"{emoji} **{interv.get('type', '')}** — {interv.get('date', '')} | {statut}")
            if interv.get('commentaire'):
                st.caption(interv['commentaire'])
    else:
        st.info("Aucune intervention pour ce véhicule")

    st.markdown("---")
    st.markdown("### ⛽ Bons de Carburant")
    vh_bons = [b for b in bons_carburant if b.get('immatriculation') == immat]
    if vh_bons:
        cols = st.columns([2, 1, 1, 1, 1])
        for col, label in zip(cols, ["N° Bon", "Date", "Carburant", "Volume (L)", "Montant (€)"]):
            col.markdown(f"<small><b>{label}</b></small>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.25rem 0 0.5rem 0'>", unsafe_allow_html=True)
        for bon in reversed(vh_bons):
            c = st.columns([2, 1, 1, 1, 1])
            c[0].markdown(f"<small>{esc(bon.get('numero_bon',''))}</small>", unsafe_allow_html=True)
            c[1].markdown(f"<small>{esc(bon.get('date',''))}</small>", unsafe_allow_html=True)
            c[2].markdown(f"<small>{esc(bon.get('type_carburant','-'))}</small>", unsafe_allow_html=True)
            c[3].markdown(f"<small>{esc(bon.get('volume','-'))}</small>", unsafe_allow_html=True)
            c[4].markdown(f"<small>{esc(bon.get('montant','-'))}</small>", unsafe_allow_html=True)
    else:
        st.info("Aucun bon de carburant pour ce véhicule")
