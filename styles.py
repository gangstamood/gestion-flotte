def get_css(t):
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp {{ background: {t['bg']}; font-family: 'Inter', sans-serif; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{background: transparent !important; pointer-events: none;}}
    [data-testid="stToolbar"] {{display: none !important;}}
    [data-testid="stDecoration"] {{display: none !important;}}
    [data-testid="stSidebar"] {{ background: {t['sidebar_bg']}; border-right: 1px solid {t['card_border']}; }}
    .main .block-container {{ padding: 2rem 3rem; max-width: 1400px; }}
    h1 {{ color: {t['h1_color']} !important; font-weight: 700 !important; font-size: 2rem !important; margin-bottom: 0.5rem !important; }}
    h2, h3 {{ color: {t['h23_color']} !important; font-weight: 600 !important; }}
    [data-testid="stMetric"] {{ background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 16px; padding: 1.5rem; box-shadow: {t['card_shadow']}; }}
    [data-testid="stMetric"]:hover {{ transform: translateY(-2px); box-shadow: {t['card_hover_shadow']}; }}
    [data-testid="stMetric"] label {{ color: {t['metric_label']} !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: {t['metric_value']} !important; font-size: 2.5rem !important; font-weight: 700 !important; }}
    .stTextInput > div > div > input, .stSelectbox > div > div, .stTextArea > div > div > textarea, .stNumberInput > div > div > input {{ background-color: {t['input_bg']} !important; border: 1px solid {t['input_border']} !important; border-radius: 10px !important; color: {t['h1_color']} !important; }}
    .stTextInput > label, .stSelectbox > label, .stTextArea > label, .stNumberInput > label, .stDateInput > label, .stTimeInput > label {{ color: {t['label_color']} !important; font-weight: 500 !important; }}
    .stButton > button {{ background: {t['btn_bg']}; color: white; border: none; border-radius: 10px; padding: 0.6rem 1.5rem; font-weight: 600; box-shadow: {t['btn_shadow']}; }}
    .stButton > button:hover {{ transform: translateY(-1px); box-shadow: {t['btn_hover_shadow']}; }}
    .stDownloadButton > button {{ background: {t['dl_btn_bg']}; box-shadow: {t['dl_btn_shadow']}; }}
    [data-testid="stForm"] {{ background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 16px; padding: 1.5rem; }}
    .stDataFrame {{ background: {t['df_bg']}; border-radius: 12px; border: 1px solid {t['card_border']}; }}
    .streamlit-expanderHeader {{ background: {t['expander_bg']} !important; border: 1px solid {t['expander_border']} !important; border-radius: 10px !important; color: {t['expander_color']} !important; }}
    hr {{ border-color: {t['hr_color']} !important; margin: 2rem 0 !important; }}
    p, .stText, .stMarkdown {{ color: {t['text_color']}; }}
    strong {{ color: {t['strong_color']}; }}
    .page-intro {{ color: {t['intro_color']}; font-size: 0.95rem; margin-bottom: 2rem; }}
    .sidebar-title {{ color: {t['sidebar_title']}; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; }}
    /* Sidebar nav buttons */
    [data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: {t['text_color']} !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        transition: background 0.2s !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: {t['input_bg']} !important;
        transform: none !important;
        box-shadow: none !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: {t['btn_bg']} !important;
        color: white !important;
        font-weight: 600 !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
        background: {t['btn_bg']} !important;
        opacity: 0.9;
    }}
    [data-testid="stSidebar"] .stExpander {{
        border: none !important;
        background: transparent !important;
        margin-bottom: 0.25rem;
    }}
    [data-testid="stSidebar"] .streamlit-expanderHeader {{
        background: transparent !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.5rem 0.25rem !important;
        color: {t['h23_color']} !important;
    }}
    [data-testid="stSidebar"] .streamlit-expanderContent {{
        padding: 0 0 0 0.5rem !important;
        border: none !important;
    }}
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: {t['scrollbar_track']}; }}
    ::-webkit-scrollbar-thumb {{ background: {t['scrollbar_thumb']}; border-radius: 4px; }}

    /* ===== RESPONSIVE MOBILE ===== */
    @media (max-width: 768px) {{
        .main .block-container {{ padding: 1rem 0.75rem; }}
        h1 {{ font-size: 1.4rem !important; }}
        h2, h3 {{ font-size: 1.1rem !important; }}
        [data-testid="stMetric"] {{ padding: 1rem; border-radius: 12px; }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{ font-size: 1.8rem !important; }}
        [data-testid="stMetric"] label {{ font-size: 0.75rem !important; }}
        .stButton > button {{ padding: 0.5rem 1rem; font-size: 0.85rem; border-radius: 8px; }}
        [data-testid="stForm"] {{ padding: 1rem; border-radius: 12px; }}
        [data-testid="stSidebar"] {{ width: 85vw !important; max-width: 300px; }}
        .sidebar-title {{ font-size: 1.2rem; }}
        .page-intro {{ font-size: 0.85rem; margin-bottom: 1rem; }}
        hr {{ margin: 1rem 0 !important; }}
    }}
    @media (max-width: 480px) {{
        .main .block-container {{ padding: 0.75rem 0.5rem; }}
        h1 {{ font-size: 1.2rem !important; }}
        [data-testid="stMetric"] {{ padding: 0.75rem; }}
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{ font-size: 1.5rem !important; }}
    }}
</style>
"""
