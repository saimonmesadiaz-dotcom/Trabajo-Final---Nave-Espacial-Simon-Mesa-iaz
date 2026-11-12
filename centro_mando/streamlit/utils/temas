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
       3. PANEL LATERAL
    ===================================================== */

    [data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 20% 15%, #182b50 0%, transparent 35%),
            linear-gradient(180deg, #080e20 0%, #100d27 60%, #160d2b 100%);
        border-right: 1px solid rgba(0, 234, 255, 0.35);
        box-shadow: 8px 0 30px rgba(0, 0, 0, 0.35);
        overflow: hidden;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: transparent;
    }

    [data-testid="stSidebar"]::after {
        content: "✦      ·       ✧          ·       ✦";
        position: absolute;
        top: 15%;
        left: 12%;
        width: 80%;
        color: rgba(0, 234, 255, 0.28);
        font-size: 19px;
        letter-spacing: 13px;
        line-height: 4;
        pointer-events: none;
        animation: flotar 7s ease-in-out infinite;
    }

    @keyframes flotar {
        0%, 100% {
            transform: translateY(0);
            opacity: 0.35;
        }
        50% {
            transform: translateY(-12px);
            opacity: 0.8;
        }
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        position: relative;
        z-index: 2;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: #c8dff5 !important;
    }

    /* Navegación multipágina */
    [data-testid="stSidebarNav"] {
        position: relative;
        z-index: 2;
        padding-top: 12px;
    }

    [data-testid="stSidebarNav"] a {
        border: 1px solid transparent;
        border-radius: 12px;
        margin: 7px 5px;
        padding: 10px 12px;
        transition: all 0.25s ease;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(0, 234, 255, 0.12);
        border: 1px solid rgba(0, 234, 255, 0.5);
        box-shadow: 0 0 16px rgba(0, 234, 255, 0.15);
        transform: translateX(4px);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: linear-gradient(
            100deg,
            rgba(0, 234, 255, 0.2),
            rgba(155, 92, 255, 0.18)
        );
        border: 1px solid rgba(0, 234, 255, 0.65);
        box-shadow: 0 0 18px rgba(0, 234, 255, 0.16);
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
