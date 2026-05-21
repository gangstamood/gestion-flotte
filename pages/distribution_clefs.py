import html
import streamlit as st
from datetime import datetime
from database import (
    get_distribution_clefs, add_distribution_clef,
    retour_clef, delete_distribution_clef
)

esc = html.escape


def render_distribution_clefs(t, engins, vehicules, scooters):
    st.markdown("# 🔑 Distribution des Clés")
    st.markdown("<p class='page-intro'>Traçabilité des remises et retours de clés</p>", unsafe_allow_html=True)

    clefs = get_distribution_clefs()
    en_circulation = [c for c in clefs if not c.get('retour_clef')]
    rendues = [c for c in clefs if c.get('retour_clef')]

    col1, col2, col3 = st.columns(3)
    col1.metric("🔑 En circulation", len(en_circulation))
    col2.metric("✅ Rendues aujourd'hui", sum(
        1 for c in rendues if c.get('retour_clef', '').startswith(datetime.now().strftime("%d/%m/%Y"))
    ))
    col3.metric("📋 Total distribué", len(clefs))

    st.markdown("---")
    st.markdown("### ➕ Distribuer une clé")

    tab_engin, tab_vehicule = st.tabs(["🚜 Engins", "🚗 Véhicules"])

    with tab_engin:
        if engins:
            with st.form("form_distrib_engin"):
                options = [f"{e['numero_serie']} — {e['type']} {e['marque']}" for e in engins]
                engin_sel = st.selectbox("Engin *", options)
                col_a, col_b = st.columns(2)
                nom = col_a.text_input("Nom du preneur *", placeholder="Prénom NOM")
                commentaire = col_b.text_input("Commentaire", placeholder="Optionnel")
                if st.form_submit_button("🔑 Distribuer", type="primary"):
                    if nom.strip():
                        identifiant = engin_sel.split(" — ")[0]
                        add_distribution_clef('engin', identifiant, nom.strip(), commentaire)
                        st.success(f"✅ Clé {identifiant} distribuée à {nom}")
                        st.rerun()
                    else:
                        st.error("❌ Le nom du preneur est requis")
        else:
            st.info("Aucun engin enregistré — ajoutez-en depuis 🚜 Saisir un engin")

    with tab_vehicule:
        if vehicules:
            with st.form("form_distrib_vehicule"):
                options_v = [f"{v['immatriculation']} — {v['type']} {v['marque']}" for v in vehicules]
                vh_sel = st.selectbox("Véhicule *", options_v)
                col_a, col_b = st.columns(2)
                nom_v = col_a.text_input("Nom du preneur *", placeholder="Prénom NOM")
                commentaire_v = col_b.text_input("Commentaire", placeholder="Optionnel")
                if st.form_submit_button("🔑 Distribuer", type="primary"):
                    if nom_v.strip():
                        identifiant_v = vh_sel.split(" — ")[0]
                        add_distribution_clef('vehicule', identifiant_v, nom_v.strip(), commentaire_v)
                        st.success(f"✅ Clé {identifiant_v} distribuée à {nom_v}")
                        st.rerun()
                    else:
                        st.error("❌ Le nom du preneur est requis")
        else:
            st.info("Aucun véhicule enregistré — ajoutez-en depuis ➕ Saisir un véhicule")

    if en_circulation:
        st.markdown("---")
        st.markdown("### 🔑 Clés en circulation")
        for i, c in enumerate(clefs):
            if c.get('retour_clef'):
                continue
            idx = clefs.index(c)
            cat_icon = "🚜" if c.get('categorie') == 'engin' else "🚗" if c.get('categorie') == 'vehicule' else "🛺"
            col_info, col_btn = st.columns([5, 1])
            col_info.markdown(
                f"<div style='background:{t['card_bg']};border:1px solid {t['card_border']};"
                f"border-left:4px solid #ef4444;border-radius:10px;padding:0.8rem 1.2rem;'>"
                f"<span style='color:{t['h1_color']};font-weight:600;'>{cat_icon} {esc(c.get('identifiant',''))}</span>"
                f"<span style='color:{t['label_color']};margin-left:1rem;'>👤 {esc(c.get('nom',''))}</span>"
                f"<span style='color:{t['text_color']};margin-left:1rem;font-size:0.85rem;'>"
                f"📅 {esc(c.get('date',''))} {esc(c.get('heure',''))}</span>"
                + (f"<span style='color:{t['intro_color']};margin-left:1rem;font-size:0.85rem;'>💬 {esc(c.get('commentaire',''))}</span>" if c.get('commentaire') else "")
                + "</div>",
                unsafe_allow_html=True
            )
            if col_btn.button("✅ Rendu", key=f"ret_clef_{idx}", type="primary"):
                retour_clef(idx)
                st.success("✅ Clé rendue !")
                st.rerun()

    if rendues:
        st.markdown("---")
        with st.expander(f"📋 Historique — {len(rendues)} clé(s) rendue(s)"):
            for i, c in enumerate(reversed(rendues)):
                idx = len(clefs) - 1 - clefs[::-1].index(c)
                cat_icon = "🚜" if c.get('categorie') == 'engin' else "🚗" if c.get('categorie') == 'vehicule' else "🛺"
                col_h, col_d = st.columns([5, 1])
                col_h.markdown(
                    f"<div style='background:{t['input_bg']};border:1px solid {t['card_border']};"
                    f"border-radius:8px;padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.8;'>"
                    f"<span style='color:{t['h1_color']};font-weight:600;'>{cat_icon} {esc(c.get('identifiant',''))}</span>"
                    f"<span style='color:{t['label_color']};margin-left:1rem;'>👤 {esc(c.get('nom',''))}</span>"
                    f"<span style='color:{t['text_color']};margin-left:1rem;font-size:0.8rem;'>"
                    f"📤 {esc(c.get('date',''))} {esc(c.get('heure',''))} — "
                    f"📥 {esc(c.get('retour_clef',''))}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                if col_d.button("🗑️", key=f"del_clef_{idx}"):
                    delete_distribution_clef(idx)
                    st.rerun()
