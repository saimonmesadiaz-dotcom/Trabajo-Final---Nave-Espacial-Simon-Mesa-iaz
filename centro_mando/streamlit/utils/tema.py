import streamlit as st


def tema():
    st.markdown("""
    <style>
    /* =====================================================
       1. PALETA GENERAL: CENTRO DE MANDO GALÁCTICO
    ===================================================== */

    :root {
        --fondo: #070b1b;
        --panel: rgba(13, 20, 43, 0.88);
        --panel-claro: rgba(19, 30, 58, 0.92);
        --cian: #00eaff;
        --azul: #4388ff;
        --violeta: #9b5cff;
        --magenta: #ff35d3;
        --texto: #e5f7ff;
        --texto-suave: #91a9c4;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 15% 10%, #172653 0%, transparent 35%),
            radial-gradient(ellipse at 85% 80%, #241044 0%, transparent 38%),
            linear-gradient(145deg, #050817 0%, #0b1025 55%, #10091e 100%);
        color: var(--texto);
    }

    /* =====================================================
       2. ESTRELLAS ANIMADAS DEL FONDO
    ===================================================== */

    [data-testid="stAppViewContainer"] {
        position: relative;
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        opacity: 0.55;

        background-image:
            radial-gradient(2px 2px at 10% 20%, #ffffff 98%, transparent),
            radial-gradient(1px 1px at 25% 75%, #00eaff 98%, transparent),
            radial-gradient(2px 2px at 45% 35%, #ffffff 98%, transparent),
            radial-gradient(1px 1px at 65% 15%, #c8a6ff 98%, transparent),
            radial-gradient(2px 2px at 80% 60%, #ffffff 98%, transparent),
            radial-gradient(1px 1px at 92% 28%, #00eaff 98%, transparent),
            radial-gradient(1px 1px at 35% 50%, #ffffff 98%, transparent),
            radial-gradient(2px 2px at 72% 88%, #c8a6ff 98%, transparent);

        background-size: 420px 360px;
        animation: estrellas 18s linear infinite;
    }

    @keyframes estrellas {
        0% {
            transform: translateY(0);
            opacity: 0.35;
        }
        50% {
            opacity: 0.75;
        }
        100% {
            transform: translateY(-35px);
            opacity: 0.35;
        }
    }

    /* Mantiene el contenido por encima del fondo animado */
    [data-testid="stAppViewContainer"] > .main {
        position: relative;
        z-index: 1;
    }

    /* =====================================================
       3. PANEL LATERAL (AZUL, MÁS ANCHO, CON DESTELLOS)
    ===================================================== */

    @property --ang {
        syntax: "<angle>";
        inherits: false;
        initial-value: 0deg;
    }

    /* Un poco más ancho (cuando está abierto) */
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 320px !important;
        width: 320px !important;
    }

    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 25% 8%, #2f7bff55 0%, transparent 38%),
            radial-gradient(circle at 80% 70%, #1b5fe033 0%, transparent 45%),
            linear-gradient(180deg, #0f3d94 0%, #0a2a6e 45%, #071c4d 100%);
        border-right: 1px solid rgba(110, 190, 255, 0.6);
        box-shadow: 8px 0 34px rgba(20, 90, 255, 0.28);
        overflow: hidden;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: transparent;
    }

    /* Capa 1: puntitos que suben despacio y titilan */
    [data-testid="stSidebar"]::before,
    [data-testid="stSidebar"]::after {
        content: "";
        position: absolute;
        inset: -40px 0;
        pointer-events: none;
        z-index: 0;
    }

    [data-testid="stSidebar"]::before {
        background-image:
            radial-gradient(1.5px 1.5px at 12% 18%, #fff 98%, transparent),
            radial-gradient(1px 1px at 70% 12%, #bfe3ff 98%, transparent),
            radial-gradient(2px 2px at 40% 36%, #fff 98%, transparent),
            radial-gradient(1px 1px at 85% 48%, #9fd0ff 98%, transparent),
            radial-gradient(1.5px 1.5px at 22% 62%, #fff 98%, transparent),
            radial-gradient(1px 1px at 60% 78%, #bfe3ff 98%, transparent),
            radial-gradient(2px 2px at 90% 90%, #fff 98%, transparent),
            radial-gradient(1px 1px at 8% 92%, #9fd0ff 98%, transparent);
        background-size: 260px 300px;
        animation: lev1 9s ease-in-out infinite;
    }

    /* Capa 2: destellos más grandes con brillo */
    [data-testid="stSidebar"]::after {
        background-image:
            radial-gradient(3px 3px at 18% 28%, #ffffff 40%, #7cc4ff55 70%, transparent),
            radial-gradient(3px 3px at 75% 40%, #ffffff 40%, #7cc4ff55 70%, transparent),
            radial-gradient(2.5px 2.5px at 45% 70%, #ffffff 40%, #7cc4ff55 70%, transparent),
            radial-gradient(3px 3px at 88% 82%, #ffffff 40%, #7cc4ff55 70%, transparent);
        background-size: 300px 380px;
        filter: drop-shadow(0 0 5px #8fd0ff);
        animation: lev2 6s ease-in-out infinite;
    }

    @keyframes lev1 {
        0%, 100% { transform: translateY(0); opacity: 0.45; }
        50%      { transform: translateY(-26px); opacity: 1; }
    }

    @keyframes lev2 {
        0%, 100% { transform: translate(0, 0); opacity: 1; }
        33%      { transform: translate(8px, -16px); opacity: 0.35; }
        66%      { transform: translate(-6px, -30px); opacity: 0.9; }
    }

    /* Destellos en forma de brillo (no son texto) */
    .destellos {
        position: absolute;
        inset: 0;
        pointer-events: none;
        filter: drop-shadow(0 0 6px #9fd8ff);
    }

    .destellos i {
        position: absolute;
        width: 14px;
        height: 14px;
        background: #ffffff;
        clip-path: polygon(50% 0, 60% 40%, 100% 50%, 60% 60%, 50% 100%, 40% 60%, 0 50%, 40% 40%);
        opacity: 0;
        animation: destello 5s ease-in-out infinite;
    }

    @keyframes destello {
        0%, 100% { opacity: 0;   transform: translateY(0) scale(0.4) rotate(0deg); }
        50%      { opacity: 0.95; transform: translateY(-14px) scale(1.1) rotate(45deg); }
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        position: relative;
        z-index: 2;
        display: flex;
        flex-direction: column;
    }

    /* Orden: cabecera, GUÍA, páginas (todo más pegado arriba) */
    [data-testid="stSidebarHeader"] {
        order: 0;
        height: auto;
        min-height: 0;
        padding: 0.7rem 1rem 0.2rem 1rem;
        margin-bottom: 0;
    }

    [data-testid="stSidebarNav"] { order: 1; }

    [data-testid="stSidebarUserContent"] {
        order: 2;
        padding-top: 4px;
        padding-bottom: 2rem;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] li {
        color: #d6e9ff !important;
    }

    /* Guía: texto plano; se lee haciendo scroll en la barra */
    .guia {
        position: relative;
        margin: 6px 6px 8px 6px;
        padding: 0 4px;
        font-size: 13.5px;
        line-height: 1.55;
    }

    .guia-t {
        font-family: 'Orbitron', sans-serif;
        font-size: 12px;
        letter-spacing: 1.5px;
        color: #8fd8ff;
        margin: 6px 0 4px 0;
        text-shadow: 0 0 10px #4aa8ff;
    }

    .guia p { margin: 0 0 6px 0; }
    .guia ul, .guia ol { margin: 0 0 8px 0; padding-left: 18px; }
    .guia li { margin-bottom: 4px; }
    .guia b { color: #ffffff; }

    /* Navegación FIJA arriba (no se va al hacer scroll) */
    [data-testid="stSidebarNav"] {
        position: sticky;
        top: 0;
        z-index: 20;
        padding: 6px 10px 8px 6px;
        max-height: none;
        overflow: visible;
        background: linear-gradient(180deg, #0f3d94 0%, #0d3688 100%);
        border-bottom: 1px solid rgba(130, 200, 255, 0.35);
        box-shadow: 0 8px 14px -8px rgba(0, 10, 50, 0.7);
    }

    [data-testid="stSidebarNav"] ul { padding-top: 0; margin-top: 0; }

    [data-testid="stSidebarNav"] a {
        position: relative;
        border: 1px solid rgba(140, 200, 255, 0.25);
        border-radius: 12px;
        margin: 5px 4px;
        padding: 9px 12px;
        background: rgba(10, 40, 110, 0.35);
        transition: all 0.25s ease;
    }

    [data-testid="stSidebarNav"] a::before {
        content: "";
        position: absolute;
        inset: -2px;
        border-radius: 14px;
        padding: 2px;
        background: conic-gradient(
            from var(--ang),
            transparent 0%, #00eaff 15%, #ffffff 25%,
            #ff35d3 40%, transparent 55%
        );
        -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        -webkit-mask-composite: xor;
        mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
        mask-composite: exclude;
        opacity: 0;
        transition: opacity 0.25s;
        pointer-events: none;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(0, 234, 255, 0.16);
        box-shadow: 0 0 20px rgba(0, 234, 255, 0.45),
                    inset 0 0 14px rgba(0, 234, 255, 0.18);
        transform: translateX(4px);
    }

    [data-testid="stSidebarNav"] a:hover::before {
        opacity: 1;
        animation: giro 2.2s linear infinite;
    }

    @keyframes giro { to { --ang: 360deg; } }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(
            100deg,
            rgba(0, 234, 255, 0.25),
            rgba(155, 92, 255, 0.25)
        );
        border: 1px solid rgba(0, 234, 255, 0.8);
        box-shadow: 0 0 18px rgba(0, 234, 255, 0.3);
    }

    /* =====================================================
       3b. ENCABEZADO FIJO
    ===================================================== */

    .st-key-header_fijo {
        position: sticky;
        top: 3.2rem;
        z-index: 999;
        padding-bottom: 6px;
    }

    /* =====================================================
       4. ÁREA PRINCIPAL
    ===================================================== */

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: var(--cian) !important;
        text-shadow: 0 0 12px rgba(0, 234, 255, 0.32);
        letter-spacing: 1px;
    }

    h1 {
        font-weight: 800 !important;
    }

    p, li, label, .stCaption {
        color: var(--texto);
    }

    [data-testid="stCaptionContainer"] {
        color: var(--texto-suave);
    }

    /* Separadores */
    hr {
        border-color: rgba(0, 234, 255, 0.22) !important;
    }

    /* =====================================================
       5. MÉTRICAS Y PANELES
    ===================================================== */

    [data-testid="stMetric"] {
        background: linear-gradient(
            145deg,
            rgba(17, 31, 61, 0.95),
            rgba(13, 13, 37, 0.92)
        );
        border: 1px solid rgba(0, 234, 255, 0.42);
        border-radius: 16px;
        padding: 17px 19px;
        box-shadow:
            0 0 18px rgba(0, 234, 255, 0.08),
            inset 0 0 18px rgba(67, 136, 255, 0.04);
        transition: all 0.25s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: var(--cian);
        box-shadow: 0 0 22px rgba(0, 234, 255, 0.2);
    }

    [data-testid="stMetricLabel"] {
        color: #a9c6df !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--cian) !important;
        text-shadow: 0 0 12px rgba(0, 234, 255, 0.4);
    }

    /* Contenedores, expanders y formularios */
    [data-testid="stExpander"] {
        background: rgba(14, 22, 46, 0.78);
        border: 1px solid rgba(155, 92, 255, 0.38);
        border-radius: 14px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(0, 234, 255, 0.25) !important;
        border-radius: 16px !important;
    }

    /* =====================================================
       6. BOTONES
    ===================================================== */

    .stButton > button {
        border: 1px solid rgba(0, 234, 255, 0.65);
        border-radius: 11px;
        color: #eafcff;
        background: linear-gradient(
            100deg,
            rgba(0, 175, 220, 0.22),
            rgba(116, 65, 205, 0.25)
        );
        font-weight: 650;
        transition: all 0.25s ease;
    }

    .stButton > button:hover {
        color: white;
        border-color: var(--cian);
        background: linear-gradient(
            100deg,
            rgba(0, 234, 255, 0.28),
            rgba(255, 53, 211, 0.2)
        );
        box-shadow: 0 0 18px rgba(0, 234, 255, 0.22);
        transform: translateY(-2px);
    }

    /* Campos de texto */
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(10, 18, 39, 0.9);
        color: white;
        border-color: rgba(0, 234, 255, 0.35);
        border-radius: 10px;
    }

    /* Bitácora y bloques de código */
    [data-testid="stCode"] {
        border: 1px solid rgba(0, 234, 255, 0.18);
        border-radius: 13px;
        box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.18);
    }

    /* Mensajes de estado */
    [data-testid="stAlert"] {
        border-radius: 12px;
        border: 1px solid rgba(0, 234, 255, 0.25);
    }

    /* Oculta adornos innecesarios de Streamlit */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """, unsafe_allow_html=True)
