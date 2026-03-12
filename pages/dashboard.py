import html
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import (
    retourner_vehicule, retourner_scooter, retourner_engin, _is_engin_active_today
)

esc = html.escape


def _render_planning_engins(t, engins, attributions_engins, services):
    st.markdown("### 📅 Planning Engins — Semaine")
    if 'eng_sem_offset' not in st.session_state:
        st.session_state['eng_sem_offset'] = 0

    today_date = datetime.now().date()
    lundi = today_date - timedelta(days=today_date.weekday())
    semaine_debut = lundi + timedelta(weeks=st.session_state['eng_sem_offset'])
    semaine_fin_nav = semaine_debut + timedelta(days=6)

    col_nav1, col_nav2, col_nav3 = st.columns([1, 3, 1])
    if col_nav1.button("← Préc.", key="dash_eng_prev"):
        st.session_state['eng_sem_offset'] -= 1
        st.rerun()
    nav_color = t['h23_color']
    col_nav2.markdown(
        f"<h4 style='text-align:center; color:{nav_color}'>Semaine du {semaine_debut.strftime('%d/%m/%Y')} au {semaine_fin_nav.strftime('%d/%m/%Y')}</h4>",
        unsafe_allow_html=True
    )
    if col_nav3.button("Suiv. →", key="dash_eng_next"):
        st.session_state['eng_sem_offset'] += 1
        st.rerun()

    if not engins:
        st.info("Aucun engin enregistré")
        return

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

    planning_html = f"<div style='overflow-x:auto'><table style='width:100%; border-collapse:collapse;'><thead><tr>"
    planning_html += f"<th style='{th_s} text-align:left; min-width:110px;'>Engin</th>"
    planning_html += f"<th style='{th_s} min-width:52px;'>Slot</th>"
    for i, jour in enumerate(jours_sem):
        jour_color = '#f59e0b' if jour == today_date else hc
        planning_html += f"<th style='{th_s} color:{jour_color}; min-width:88px;'>{JOURS_FR[i]}<br>{jour.strftime('%d/%m')}</th>"
    planning_html += "</tr></thead><tbody>"

    for eng in engins:
        num = eng.get('numero_serie', '')
        eng_label = f"<b>{esc(num)}</b><br><small style='color:{ic}'>{esc(eng.get('type',''))} {esc(eng.get('marque',''))}</small>"
        for pi, (periode, icon) in enumerate([('Matin', '🌅'), ('Après-midi', '🌇')]):
            planning_html += "<tr>"
            if pi == 0:
                planning_html += f"<td rowspan='2' style='{td_eng_s}'>{eng_label}</td>"
            planning_html += f"<td style='{td_slot_s}'>{icon} {periode}</td>"
            for jour in jours_sem:
                svc = _get_slot(num, jour, periode)
                if svc:
                    bg = svc_color.get(svc, '#6b7280')
                    planning_html += f"<td style='{td_s} background:{bg}; color:white; font-weight:500;'>{esc(svc)}</td>"
                else:
                    planning_html += f"<td style='{td_s} color:{ic};'>—</td>"
            planning_html += "</tr>"

    planning_html += "</tbody></table></div>"
    st.markdown(planning_html, unsafe_allow_html=True)

    legende = " ".join(
        f"<span style='background:{svc_color.get(s,'#6b7280')}; color:white; padding:0.2rem 0.6rem; border-radius:12px; font-size:0.75rem; margin-right:0.3rem;'>{esc(s)}</span>"
        for s in services
    )
    st.markdown(f"<div style='margin-top:0.6rem'>{legende}</div>", unsafe_allow_html=True)


def render_dashboard(t, vehicules, attributions, scooters, attributions_scooters,
                     engins, attributions_engins, interventions, interventions_scooters,
                     interventions_engins, services, liens):
    st.markdown("# 📊 Tableau de Bord")
    st.markdown("<p class='page-intro'>Vue d'ensemble de votre flotte</p>", unsafe_allow_html=True)

    if liens:
        st.markdown("### 📎 Tableaux de bord")
        cols = st.columns(min(len(liens), 4))
        for i, lien in enumerate(liens):
            with cols[i % 4]:
                st.link_button(f"📄 {lien.get('nom', '')}", lien.get('url', ''), use_container_width=True)
        st.markdown("---")

    nb_vehicules = len(vehicules)
    sorties_en_cours = [a for a in attributions if not a.get('retourne')]
    nb_en_sortie = len(sorties_en_cours)
    nb_scooters = len(scooters)
    nb_engins = len(engins)
    interventions_en_cours_v = [i for i in interventions if i.get('statut') == "En cours"]
    interventions_en_cours_e = [i for i in interventions_engins if i.get('statut') == "En cours"]
    interventions_en_cours_s = [i for i in interventions_scooters if i.get('statut') == "En cours"]
    nb_interventions = len(interventions_en_cours_v) + len(interventions_en_cours_e) + len(interventions_en_cours_s)

    vh_map = {v['immatriculation']: v for v in vehicules}
    sco_map = {s['immatriculation']: s for s in scooters}
    eng_map = {e['numero_serie']: e for e in engins}
    sorties_set_vh = {a['immatriculation'] for a in attributions if not a.get('retourne')}
    sorties_set_sco = {a['immatriculation'] for a in attributions_scooters if not a.get('retourne')}
    sorties_set_eng = {a['numero_serie'] for a in attributions_engins if _is_engin_active_today(a)}
    interv_set_vh = {i['immatriculation'] for i in interventions if i.get('statut') == "En cours"}
    interv_set_sco = {i['immatriculation'] for i in interventions_scooters if i.get('statut') == "En cours"}
    interv_set_eng = {i['numero_serie'] for i in interventions_engins if i.get('statut') == "En cours"}

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🚙 Véhicules", nb_vehicules)
        if st.button("📋 Détails", key="btn_vehicules", use_container_width=True):
            st.session_state['dashboard_detail'] = 'vehicules' if st.session_state.get('dashboard_detail') != 'vehicules' else None
    with col2:
        st.metric("🔑 Distribué", nb_en_sortie)
        if st.button("📋 Détails", key="btn_en_sortie", use_container_width=True):
            st.session_state['dashboard_detail'] = 'en_sortie' if st.session_state.get('dashboard_detail') != 'en_sortie' else None
    with col3:
        st.metric("🛵 Scooters", nb_scooters)
        if st.button("📋 Détails", key="btn_scooters", use_container_width=True):
            st.session_state['dashboard_detail'] = 'scooters' if st.session_state.get('dashboard_detail') != 'scooters' else None
    with col4:
        st.metric("🚜 Engins", nb_engins)
        if st.button("📋 Détails", key="btn_engins", use_container_width=True):
            st.session_state['dashboard_detail'] = 'engins' if st.session_state.get('dashboard_detail') != 'engins' else None
    with col5:
        st.metric("🔨 Interventions", nb_interventions)
        if st.button("📋 Détails", key="btn_interventions", use_container_width=True):
            st.session_state['dashboard_detail'] = 'interventions' if st.session_state.get('dashboard_detail') != 'interventions' else None

    detail = st.session_state.get('dashboard_detail')

    if detail == 'vehicules':
        st.markdown("---")
        st.markdown("### 🚙 Détail des Véhicules")
        if vehicules:
            for v in vehicules:
                immat = v.get('immatriculation', '')
                en_sortie = immat in sorties_set_vh
                en_interv = immat in interv_set_vh
                if en_interv:
                    statut = "🔧 En intervention"
                    couleur = "#f59e0b"
                elif en_sortie:
                    statut = "🔑 Distribué"
                    couleur = "#ef4444"
                else:
                    statut = "✅ Disponible"
                    couleur = "#10b981"
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid {couleur};border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;font-size:1rem;'>{esc(immat)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(v.get('marque',''))} — {esc(v.get('type',''))}</span>
                    <br/><span style='color:{couleur};font-weight:500;font-size:0.9rem;'>{statut}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun véhicule enregistré")

    elif detail == 'en_sortie':
        st.markdown("---")
        st.markdown("### 🔑 Véhicules distribués")
        if sorties_en_cours:
            for a in sorties_en_cours:
                immat = a.get('immatriculation', '')
                info_v = vh_map.get(immat, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #ef4444;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{esc(immat)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(info_v.get('marque',''))} — {esc(info_v.get('type',''))}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>📅 Sorti le {esc(a.get('date',''))} à {esc(a.get('heure',''))}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>🏢 Service : {esc(a.get('service',''))}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>📆 Retour prévu : {esc(a.get('date_retour_prevue','N/A'))}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun véhicule distribué actuellement")

    elif detail == 'engins':
        st.markdown("---")
        st.markdown("### 🚜 Détail des Engins")
        if engins:
            for e in engins:
                num = e.get('numero_serie', '')
                en_sortie = num in sorties_set_eng
                en_interv = num in interv_set_eng
                if en_interv:
                    statut = "🔧 En intervention"
                    couleur = "#f59e0b"
                elif en_sortie:
                    statut = "🔑 Distribué"
                    couleur = "#ef4444"
                else:
                    statut = "✅ Disponible"
                    couleur = "#10b981"
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid {couleur};border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;font-size:1rem;'>{esc(num)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(e.get('marque',''))} — {esc(e.get('type',''))}</span>
                    <br/><span style='color:{couleur};font-weight:500;font-size:0.9rem;'>{statut}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun engin enregistré")

    elif detail == 'scooters':
        st.markdown("---")
        st.markdown("### 🛵 Détail des Scooters")
        if scooters:
            for s in scooters:
                immat = s.get('immatriculation', '')
                en_sortie = immat in sorties_set_sco
                en_interv = immat in interv_set_sco
                if en_interv:
                    statut = "🔧 En intervention"
                    couleur = "#f59e0b"
                elif en_sortie:
                    statut = "🔑 Distribué"
                    couleur = "#ef4444"
                else:
                    statut = "✅ Disponible"
                    couleur = "#10b981"
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid {couleur};border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;font-size:1rem;'>{esc(immat)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(s.get('marque',''))} — {esc(s.get('type',''))}</span>
                    <br/><span style='color:{couleur};font-weight:500;font-size:0.9rem;'>{statut}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Aucun scooter enregistré")

    elif detail == 'interventions':
        st.markdown("---")
        st.markdown("### 🔨 Interventions en cours")
        if interventions_en_cours_v:
            st.markdown("#### 🚗 Véhicules")
            for i in interventions_en_cours_v:
                immat = i.get('immatriculation', '')
                info_v = vh_map.get(immat, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #f59e0b;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{esc(immat)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(info_v.get('marque',''))} — {esc(info_v.get('type',''))}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>🔧 {esc(i.get('type',''))} — 📅 {esc(i.get('date',''))} à {esc(i.get('heure',''))}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>💬 {esc(i.get('commentaire',''))}</span>
                </div>""", unsafe_allow_html=True)
        if interventions_en_cours_s:
            st.markdown("#### 🛵 Scooters")
            for i in interventions_en_cours_s:
                immat = i.get('immatriculation', '')
                info_s = sco_map.get(immat, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #f59e0b;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{esc(immat)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(info_s.get('marque',''))} — {esc(info_s.get('type',''))}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>🔧 {esc(i.get('type',''))} — 📅 {esc(i.get('date',''))} à {esc(i.get('heure',''))}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>💬 {esc(i.get('commentaire',''))}</span>
                </div>""", unsafe_allow_html=True)
        if interventions_en_cours_e:
            st.markdown("#### 🚜 Engins")
            for i in interventions_en_cours_e:
                num = i.get('numero_serie', '')
                info_e = eng_map.get(num, {})
                st.markdown(f"""<div style='background:{t['card_bg']};border:1px solid {t['card_border']};border-left:4px solid #f59e0b;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:0.5rem;'>
                    <span style='color:{t['h1_color']};font-weight:600;'>{esc(num)}</span>
                    <span style='color:{t['label_color']};margin-left:1rem;'>{esc(info_e.get('marque',''))} — {esc(info_e.get('type',''))}</span><br/>
                    <span style='color:{t['text_color']};font-size:0.85rem;'>🔧 {esc(i.get('type',''))} — 📅 {esc(i.get('date',''))} à {esc(i.get('heure',''))}</span>
                    <span style='color:{t['text_color']};font-size:0.85rem;margin-left:1rem;'>💬 {esc(i.get('commentaire',''))}</span>
                </div>""", unsafe_allow_html=True)
        if not interventions_en_cours_v and not interventions_en_cours_e and not interventions_en_cours_s:
            st.info("Aucune intervention en cours")

    st.markdown("---")
    _render_planning_engins(t, engins, attributions_engins, services)

    st.markdown("---")
    st.markdown("### 🔍 Filtres")
    col_f1, col_f2 = st.columns(2)
    types_dispo = (["Tous"] + sorted(set(v['type'] for v in vehicules))) if vehicules else ["Tous"]
    filtre_type = col_f1.selectbox("Type", types_dispo)
    filtre_service = col_f2.selectbox("Service", ["Tous"] + services)

    st.markdown("---")
    st.markdown("### 📋 Sorties du Jour")
    aujourd_hui = datetime.now().strftime("%d/%m/%Y")

    with st.expander("🚗 Véhicules", expanded=False):
        sorties_jour = [a for a in attributions if a.get('date') == aujourd_hui and not a.get('retourne')]
        if sorties_jour:
            df = pd.DataFrame(sorties_jour)
            df['type'] = df['immatriculation'].map(lambda x: vh_map.get(x, {}).get('type', ''))
            df['marque'] = df['immatriculation'].map(lambda x: vh_map.get(x, {}).get('marque', ''))
            if filtre_type != "Tous":
                df = df[df['type'] == filtre_type]
            if filtre_service != "Tous":
                df = df[df['service'] == filtre_service]
            if len(df) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df[df['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        st.dataframe(df_srv[['immatriculation', 'type', 'marque', 'date', 'heure']], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Aucune attribution")
        else:
            st.warning("⚠️ Aucune attribution")

    with st.expander("🛵 Scooters", expanded=False):
        sorties_jour_sco = [a for a in attributions_scooters if a.get('date') == aujourd_hui and not a.get('retourne')]
        if sorties_jour_sco:
            df_sco = pd.DataFrame(sorties_jour_sco)
            df_sco['type'] = df_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('type', ''))
            df_sco['marque'] = df_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('marque', ''))
            if filtre_service != "Tous":
                df_sco = df_sco[df_sco['service'] == filtre_service]
            if len(df_sco) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_sco[df_sco['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        cols_sco = ['immatriculation', 'type', 'marque', 'date', 'heure']
                        if 'casque' in df_srv.columns:
                            cols_sco.append('casque')
                        st.dataframe(df_srv[cols_sco], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Aucune attribution")
        else:
            st.warning("⚠️ Aucune attribution")

    with st.expander("🚜 Engins", expanded=False):
        sorties_jour_eng = [a for a in attributions_engins if _is_engin_active_today(a)]
        if sorties_jour_eng:
            df_eng = pd.DataFrame(sorties_jour_eng)
            df_eng['type'] = df_eng['numero_serie'].map(lambda x: eng_map.get(x, {}).get('type', ''))
            df_eng['marque'] = df_eng['numero_serie'].map(lambda x: eng_map.get(x, {}).get('marque', ''))
            if filtre_service != "Tous":
                df_eng = df_eng[df_eng['service'] == filtre_service]
            if len(df_eng) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_eng[df_eng['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        cols_show = [c for c in ['numero_serie', 'type', 'marque', 'date', 'date_fin', 'periode'] if c in df_srv.columns]
                        st.dataframe(df_srv[cols_show], use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Aucune attribution")
        else:
            st.warning("⚠️ Aucune attribution")

    st.markdown("---")
    st.markdown("### 🔙 Retours du Jour")

    with st.expander("🚗 Véhicules retournés aujourd'hui", expanded=False):
        retours_jour = [a for a in attributions if a.get('retourne', '').startswith(aujourd_hui)]
        if retours_jour:
            df_ret = pd.DataFrame(retours_jour)
            df_ret['type'] = df_ret['immatriculation'].map(lambda x: vh_map.get(x, {}).get('type', ''))
            df_ret['marque'] = df_ret['immatriculation'].map(lambda x: vh_map.get(x, {}).get('marque', ''))
            if filtre_type != "Tous":
                df_ret = df_ret[df_ret['type'] == filtre_type]
            if filtre_service != "Tous":
                df_ret = df_ret[df_ret['service'] == filtre_service]
            if len(df_ret) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_ret[df_ret['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        st.dataframe(df_srv[['immatriculation', 'type', 'marque', 'date', 'retourne']], use_container_width=True, hide_index=True)
            else:
                st.info("✅ Aucun retour aujourd'hui")
        else:
            st.info("✅ Aucun retour aujourd'hui")

    with st.expander("🛵 Scooters retournés aujourd'hui", expanded=False):
        retours_jour_sco = [a for a in attributions_scooters if a.get('retourne', '').startswith(aujourd_hui)]
        if retours_jour_sco:
            df_ret_sco = pd.DataFrame(retours_jour_sco)
            df_ret_sco['type'] = df_ret_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('type', ''))
            df_ret_sco['marque'] = df_ret_sco['immatriculation'].map(lambda x: sco_map.get(x, {}).get('marque', ''))
            if filtre_service != "Tous":
                df_ret_sco = df_ret_sco[df_ret_sco['service'] == filtre_service]
            if len(df_ret_sco) > 0:
                for srv in (services if filtre_service == "Tous" else [filtre_service]):
                    df_srv = df_ret_sco[df_ret_sco['service'] == srv]
                    if len(df_srv) > 0:
                        st.markdown(f"#### 🔹 {srv}")
                        cols_ret_sco = ['immatriculation', 'type', 'marque', 'date', 'retourne']
                        if 'casque' in df_srv.columns:
                            cols_ret_sco.append('casque')
                        st.dataframe(df_srv[cols_ret_sco], use_container_width=True, hide_index=True)
            else:
                st.info("✅ Aucun retour aujourd'hui")
        else:
            st.info("✅ Aucun retour aujourd'hui")

    st.markdown("---")
    st.markdown("### 🔙 Retourner un Véhicule")
    sortis = [a for a in attributions if not a.get('retourne')]
    if sortis:
        col_r1, col_r2 = st.columns([3, 1])
        immat_ret = col_r1.selectbox("Véhicule", [f"{v['immatriculation']} - {v['service']}" for v in sortis])
        if col_r2.button("✅ Retourner", type="primary", key="ret_vh"):
            retourner_vehicule(immat_ret.split(" - ")[0])
            st.success("✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun véhicule distribué")

    st.markdown("---")
    st.markdown("### 🔙 Retourner un Scooter")
    sortis_sco = [a for a in attributions_scooters if not a.get('retourne')]
    if sortis_sco:
        col_r1, col_r2 = st.columns([3, 1])
        options_sco = []
        for v in sortis_sco:
            casque_info = f" | Casque: {v['casque']}" if v.get('casque') else ""
            options_sco.append(f"{v['immatriculation']} - {v['service']}{casque_info}")
        immat_ret_sco = col_r1.selectbox("Scooter", options_sco)
        if col_r2.button("✅ Retourner", type="primary", key="ret_sco"):
            retourner_scooter(immat_ret_sco.split(" - ")[0])
            st.success("✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun scooter distribué")

    st.markdown("---")
    st.markdown("### 🔙 Retourner un Engin")
    sortis_engins_dash = [a for a in attributions_engins if _is_engin_active_today(a)]
    if sortis_engins_dash:
        col_r1, col_r2 = st.columns([3, 1])
        engin_ret_dash = col_r1.selectbox("Engin", [f"{e['numero_serie']} - {e['service']}" for e in sortis_engins_dash])
        if col_r2.button("✅ Retourner", type="primary", key="ret_eng_dash"):
            retourner_engin(engin_ret_dash.split(" - ")[0])
            st.success("✅ Retourné !")
            st.rerun()
    else:
        st.info("Aucun engin distribué")
