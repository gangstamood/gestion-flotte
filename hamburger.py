"""
Module pour le bouton hamburger personnalisé de la sidebar.
"""
import streamlit as st
import streamlit.components.v1 as components
from styles import THEMES


def get_hamburger_script():
    """
    Génère le script JavaScript pour le bouton hamburger de la sidebar.
    Permet de contrôler l'ouverture/fermeture de la sidebar avec un bouton personnalisé.
    """
    t = THEMES[st.session_state['theme']]

    return f"""
<script>
(function() {{
    var doc = window.parent.document;
    var isMobile = window.parent.innerWidth <= 768;
    var sidebarOpen = !isMobile;
    var bgColor = '{t["hamburger_bg"]}';
    var hoverColor = '{t["hamburger_hover"]}';
    var textColor = '{t["h1_color"]}';

    function getSidebarWidth() {{
        if (window.parent.innerWidth <= 480) return Math.min(window.parent.innerWidth * 0.85, 280);
        if (window.parent.innerWidth <= 768) return Math.min(window.parent.innerWidth * 0.85, 300);
        return 300;
    }}

    function setSidebarState(open) {{
        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;
        sidebarOpen = open;
        var w = getSidebarWidth();
        if (open) {{
            sidebar.setAttribute('aria-expanded', 'true');
            sidebar.style.setProperty('transform', 'none', 'important');
            sidebar.style.setProperty('width', w + 'px', 'important');
            sidebar.style.setProperty('min-width', w + 'px', 'important');
            sidebar.style.setProperty('visibility', 'visible', 'important');
            if (isMobile) {{
                sidebar.style.setProperty('position', 'fixed', 'important');
                sidebar.style.setProperty('z-index', '99999', 'important');
                sidebar.style.setProperty('top', '0', 'important');
                sidebar.style.setProperty('left', '0', 'important');
                sidebar.style.setProperty('height', '100vh', 'important');
                sidebar.style.setProperty('box-shadow', '4px 0 20px rgba(0,0,0,0.3)', 'important');
            }} else {{
                sidebar.style.setProperty('position', 'relative', 'important');
                sidebar.style.removeProperty('z-index');
                sidebar.style.removeProperty('box-shadow');
            }}
        }} else {{
            sidebar.setAttribute('aria-expanded', 'false');
            sidebar.style.setProperty('transform', 'translateX(-' + w + 'px)', 'important');
            sidebar.style.setProperty('width', '0px', 'important');
            sidebar.style.setProperty('min-width', '0px', 'important');
            sidebar.style.setProperty('visibility', 'hidden', 'important');
            sidebar.style.setProperty('position', 'fixed', 'important');
        }}
        var btn = doc.getElementById('custom-hamburger');
        if (btn) btn.innerHTML = open ? '&#10005;' : '&#9776;';
    }}

    function createHamburger() {{
        var existing = doc.getElementById('custom-hamburger');
        if (existing) existing.remove();
        var btn = doc.createElement('button');
        btn.id = 'custom-hamburger';
        btn.innerHTML = '&#10005;';
        btn.style.cssText = 'position:fixed;top:14px;left:14px;z-index:999999;background:'+bgColor+';color:'+textColor+';border:1px solid rgba(128,128,128,0.2);border-radius:8px;width:40px;height:40px;font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,0.15);transition:all 0.2s;pointer-events:auto;';
        btn.onmouseover = function() {{ btn.style.background = hoverColor; }};
        btn.onmouseout = function() {{ btn.style.background = bgColor; }};
        btn.onclick = function(e) {{
            e.preventDefault();
            e.stopPropagation();
            setSidebarState(!sidebarOpen);
        }};
        doc.body.appendChild(btn);
    }}

    function init() {{
        createHamburger();
        setSidebarState(true);
    }}

    init();
    setTimeout(init, 300);
    setTimeout(init, 1000);
    setTimeout(init, 2500);
}})();
</script>
"""


def inject_hamburger():
    """
    Injecte le script du bouton hamburger dans la page.
    """
    components.html(get_hamburger_script(), height=0)