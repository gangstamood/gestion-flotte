import html
import streamlit as st
from styles import THEMES
from database import (
    add_category, delete_category,
    add_service, delete_service,
    add_category_engin, delete_category_engin,
    add_category_scooter, delete_category_scooter,
    add_category_golfette, delete_category_golfette,
    add_lien, delete_lien,
    set_parametre
)


esc = html.escape


def render_parametres(t, categories, services, categories_engins, categories_scooters, categories_golfettes, liens, parametres=None):
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
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{esc(cat)}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dc_{cat}"):
                delete_category(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat = c1.text_input("Nouvelle catégorie", key=f"nv_cat_{st.session_state.get('_fk',0)}", label_visibility="collapsed", placeholder="Nouvelle catégorie...")
        if c2.button("➕", key="ac", type="primary"):
            if nv_cat:
                add_category(nv_cat)
                st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                st.rerun()
    with col2:
        st.markdown("#### 🏢 Services")
        for srv in services:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{esc(srv)}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"ds_{srv}"):
                delete_service(srv)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_srv = c1.text_input("Nouveau service", key=f"nv_srv_{st.session_state.get('_fk',0)}", label_visibility="collapsed", placeholder="Nouveau service...")
        if c2.button("➕", key="as", type="primary"):
            if nv_srv:
                add_service(nv_srv)
                st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                st.rerun()

    st.markdown("---")
    st.markdown("### 🚜 Engins")
    st.markdown("#### 🏷️ Catégories Engins")
    col_eng = st.columns(2)[0]
    with col_eng:
        for cat in categories_engins:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{esc(cat)}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dce_{cat}"):
                delete_category_engin(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_eng = c1.text_input("Nouvelle catégorie engin", key=f"nv_cat_eng_{st.session_state.get('_fk',0)}", label_visibility="collapsed", placeholder="Nouvelle catégorie engin...")
        if c2.button("➕", key="ace", type="primary"):
            if nv_cat_eng:
                add_category_engin(nv_cat_eng)
                st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                st.rerun()

    st.markdown("---")
    st.markdown("### 🛵 Scooters")
    st.markdown("#### 🏷️ Catégories Scooters")
    col_sco = st.columns(2)[0]
    with col_sco:
        for cat in categories_scooters:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{esc(cat)}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dcs_{cat}"):
                delete_category_scooter(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_sco = c1.text_input("Nouvelle catégorie scooter", key=f"nv_cat_sco_{st.session_state.get('_fk',0)}", label_visibility="collapsed", placeholder="Nouvelle catégorie scooter...")
        if c2.button("➕", key="acs", type="primary"):
            if nv_cat_sco:
                add_category_scooter(nv_cat_sco)
                st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                st.rerun()

    st.markdown("---")
    st.markdown("### ⛳ Golfettes")
    st.markdown("#### 🏷️ Catégories Golfettes")
    col_golf = st.columns(2)[0]
    with col_golf:
        for cat in categories_golfettes:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{esc(cat)}</div>", unsafe_allow_html=True)
            if c2.button("🗑️", key=f"dcg_{cat}"):
                delete_category_golfette(cat)
                st.rerun()
        c1, c2 = st.columns([3, 1])
        nv_cat_golf = c1.text_input("Nouvelle catégorie golfette", key=f"nv_cat_golf_{st.session_state.get('_fk',0)}", label_visibility="collapsed", placeholder="Nouvelle catégorie golfette...")
        if c2.button("➕", key="acg", type="primary"):
            if nv_cat_golf:
                add_category_golfette(nv_cat_golf)
                st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔨 Contact Interventions WLG")
    st.markdown("<p class='page-intro'>Ces informations sont pré-remplies automatiquement dans le formulaire de déclaration d'intervention.</p>", unsafe_allow_html=True)
    p = parametres or {}
    col_c1, col_c2 = st.columns(2)
    cur_tel = p.get('contact_telephone', '')
    cur_hor = p.get('contact_horaires', '')
    new_tel = col_c1.text_input("📞 N° à appeler", value=cur_tel, placeholder="06 XX XX XX XX")
    new_hor = col_c2.text_input("🕐 Horaires", value=cur_hor, placeholder="8h-12h / 14h-17h")
    if st.button("💾 Enregistrer le contact", type="primary"):
        set_parametre('contact_telephone', new_tel.strip())
        set_parametre('contact_horaires', new_hor.strip())
        st.success("✅ Contact enregistré")
        st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
        st.rerun()

    st.markdown("---")
    st.markdown("### 📎 Liens Tableaux Excel")
    st.markdown("<p class='page-intro'>Ces liens apparaissent comme boutons cliquables sur le Dashboard.</p>", unsafe_allow_html=True)
    col_liens = st.columns(2)[0]
    with col_liens:
        for lien in liens:
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['h23_color']};'>{esc(lien.get('nom', ''))}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='background: {t['input_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; color: {t['intro_color']}; font-size: 0.8rem; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;'>{esc(lien.get('url', ''))}</div>", unsafe_allow_html=True)
            if c3.button("🗑️", key=f"dl_{lien.get('nom', '')}"):
                delete_lien(lien.get('nom', ''))
                st.rerun()
        with st.form(f"form_add_lien_{st.session_state.get('_fk',0)}"):
            c1, c2, c3 = st.columns([2, 3, 1])
            nv_nom = c1.text_input("Nom *", label_visibility="collapsed", placeholder="Ex : Véhicules 2024")
            nv_url = c2.text_input("URL *", label_visibility="collapsed", placeholder="https://...")
            if c3.form_submit_button("➕", type="primary"):
                if nv_nom and nv_url:
                    add_lien(nv_nom, nv_url)
                    st.session_state['_fk'] = st.session_state.get('_fk', 0) + 1
                    st.rerun()
                else:
                    st.error("❌ Nom et URL requis")
