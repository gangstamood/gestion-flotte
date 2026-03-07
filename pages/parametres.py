import streamlit as st
from styles import THEMES
from database import (
    add_category, delete_category,
    add_service, delete_service,
    add_category_engin, delete_category_engin,
    add_category_scooter, delete_category_scooter,
    add_lien, delete_lien
)


def render_parametres(t, categories, services, categories_engins, categories_scooters, liens):
    st.markdown("# ⚙️ Paramètres")
    st.markdown("<p class='page-intro'>Configurer l'application</p>", unsafe_allow_html=True)

    st.markdown("### 🎨 Apparence")
    theme_names = list(THEMES.keys())
    current_idx = theme_names.index(st.session_state['theme']) if st.session_state['theme'] in theme_names else 0
    selected_theme = st.selectbox("Thème", theme_names, index=current_idx)
    if selected_theme != st.session_state['theme']:
        st.session_state['theme'] = selected_theme
        st.rerun()

    st.markdown("---")
    st.markdown("### 🚗 Véhicules")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🏷️ Catégories Véhicules")
        for cat in categories:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{cat}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dc_{cat}"):
                delete_category(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat = c1.text_input("Nouvelle catégorie", label_visibility="collapsed", placeholder="Nouvelle catégorie...")
        if c2.button("➕", key="ac", type="primary"):
            if nv_cat:
                add_category(nv_cat)
                st.rerun()
    with col2:
        st.markdown("#### 🏢 Services")
        for srv in services:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{srv}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"ds_{srv}"):
                delete_service(srv)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_srv = c1.text_input("Nouveau service", label_visibility="collapsed", placeholder="Nouveau service...")
        if c2.button("➕", key="as", type="primary"):
            if nv_srv:
                add_service(nv_srv)
                st.rerun()

    st.markdown("---")
    st.markdown("### 🚜 Engins")
    st.markdown("#### 🏷️ Catégories Engins")
    col_eng = st.columns(2)[0]
    with col_eng:
        for cat in categories_engins:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{cat}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dce_{cat}"):
                delete_category_engin(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_eng = c1.text_input("Nouvelle catégorie engin", label_visibility="collapsed", placeholder="Nouvelle catégorie engin...")
        if c2.button("➕", key="ace", type="primary"):
            if nv_cat_eng:
                add_category_engin(nv_cat_eng)
                st.rerun()

    st.markdown("---")
    st.markdown("### 🛵 Scooters")
    st.markdown("#### 🏷️ Catégories Scooters")
    col_sco = st.columns(2)[0]
    with col_sco:
        for cat in categories_scooters:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{cat}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dcs_{cat}"):
                delete_category_scooter(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_sco = c1.text_input("Nouvelle catégorie scooter", label_visibility="collapsed", placeholder="Nouvelle catégorie scooter...")
        if c2.button("➕", key="acs", type="primary"):
            if nv_cat_sco:
                add_category_scooter(nv_cat_sco)
                st.rerun()

    st.markdown("---")
    st.markdown("### 📎 Liens Tableaux Excel")
    st.markdown("<p class='page-intro'>Ces liens apparaissent comme boutons cliquables sur le Dashboard.</p>", unsafe_allow_html=True)
    col_liens = st.columns(2)[0]
    with col_liens:
        for lien in liens:
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{lien.get('nom', '')}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['intro_color']}; font-size: 0.8rem; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;'>{lien.get('url', '')}</div>", unsafe_allow_html=True)
            if c3.button("🗑️", key=f"dl_{lien.get('nom', '')}"):
                delete_lien(lien.get('nom', ''))
                st.rerun()
        with st.form("form_add_lien"):
            c1, c2, c3 = st.columns([2, 3, 1])
            nv_nom = c1.text_input("Nom *", label_visibility="collapsed", placeholder="Ex : Véhicules 2024")
            nv_url = c2.text_input("URL *", label_visibility="collapsed", placeholder="https://...")
            if c3.form_submit_button("➕", type="primary"):
                if nv_nom and nv_url:
                    add_lien(nv_nom, nv_url)
                    st.rerun()
                else:
                    st.error("❌ Nom et URL requis")
