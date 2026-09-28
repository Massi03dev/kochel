import sys
import time
from pathlib import Path
import streamlit as st

# Assicura il caricamento corretto del modulo da src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import kochel

# 1. Configurazione Pagina
st.set_page_config(
    page_title="Kochel | Classical Music Parser",
    page_icon="🎼",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 2. Stile CSS personalizzato (Card, Badge, Tipografia)
st.markdown(
    """
<style>
    /* Spaziatura generale e pulizia */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 780px;
    }
    
    /* Header badges */
    .tech-pill {
        display: inline-block;
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-weight: 500;
        margin-right: 6px;
        color: #888;
    }
    
    /* Card per i metadati */
    .meta-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    .meta-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .main-text {
        font-size: 1.35rem;
        font-weight: 600;
        line-height: 1.3;
        margin-bottom: 0.25rem;
    }
    
    .sub-text {
        font-size: 0.9rem;
        color: #888;
    }
    
    /* Tag colorati per catalogo e tonalità */
    .tag {
        display: inline-block;
        border-radius: 6px;
        padding: 3px 8px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .tag-catalog { background-color: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .tag-key { background-color: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .tag-role { background-color: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); text-transform: capitalize; }
    
    /* Badge latenza */
    .perf-badge {
        font-size: 0.82rem;
        color: #10b981;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 4px;
        margin-top: 0.4rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 3. Header & Branding
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.svg"
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=130)

st.title("Kochel: Classical Music Metadata Parser")
st.markdown("Ultra-fast parser & entity linker for messy classical music tracks.")
st.markdown(
    '<span class="tech-pill">⚡ Sub-15ms CPU</span>'
    '<span class="tech-pill">🧠 MiniLM INT8</span>'
    '<span class="tech-pill">🗄️ SQLite Catalog</span>',
    unsafe_allow_html=True,
)
st.write("")

# 4. Query di esempio selezionabili
EXAMPLES = {
    "Beethoven Symphony No. 5 (Karajan)": "Beethoven Symphony no. 5 Op. 67 Karajan 1962",
    "Chopin Nocturne (Rubinstein)": "Chopin nocturne op 9 no 2 rubinstein rec 1965",
    "Messy Torrent Filename": "01_Beethoven_Symphony.5_Op.67_Allegro_Karajan_BPO_1962_FLAC",
    "Bach Concerto (Gould)": "Bach BWV 1046 Gould",
    "Inverted Artist/Work": "Claudio Abbado Brahms Double Concerto Op 102 Live stereo",
    "Mozart KV 622 (Argerich)": "Mozart KV622 Argerich",
}

selected_label = st.selectbox(
    "💡 Select an example track or test your own:",
    options=["-- Custom Input --"] + list(EXAMPLES.keys()),
    index=1,
)

default_val = EXAMPLES[selected_label] if selected_label != "-- Custom Input --" else ""

# 5. Form di input
with st.form("parse_form", clear_on_submit=False):
    col_input, col_btn = st.columns([5, 1.2], vertical_alignment="bottom")
    with col_input:
        query_text = st.text_input(
            "Track title / search string",
            value=default_val,
            placeholder="e.g. Beethoven 5 Karajan 1962",
            label_visibility="collapsed",
        )
    with col_btn:
        submitted = st.form_submit_button(
            "Parse", type="primary", use_container_width=True
        )

# 6. Esecuzione e Rendering Risultati
if query_text:
    t0 = time.perf_counter()
    result = kochel.parse(query_text.strip())
    latency_ms = (time.perf_counter() - t0) * 1000

    work = result.get("work", {})
    composer = work.get("composer", {})
    catalog = work.get("catalog", {})
    key = work.get("key")
    recording = result.get("recording", {})
    performers = recording.get("performers", [])
    year = recording.get("year")

    st.markdown(
        f'<div class="perf-badge">⚡ Parsed & canonicalized in <b>{latency_ms:.2f} ms</b> on CPU</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    # Due colonne principali per le schede
    col_left, col_right = st.columns(2)

    with col_left:
        # Card Compositore & Opera
        comp_canon = composer.get("canonical") or "Unknown Composer"
        comp_raw = composer.get("raw")
        title_canon = work.get("canonical_title") or "Unknown Title"

        # Badge Catalogo (es. Op. 67 o BWV 1046)
        cat_str = ""
        if catalog.get("prefix") and catalog.get("number"):
            cat_str = f"{catalog['prefix']} {catalog['number']}"
            if catalog.get("sub_number"):
                cat_str += f" No. {catalog['sub_number']}"

        st.markdown(
            f"""
        <div class="meta-card">
            <div class="meta-title">Work & Composition</div>
            <div class="main-text">{comp_canon}</div>
            <div class="sub-text" style="margin-bottom: 0.8rem;">Recognized from: <i>"{comp_raw or comp_canon}"</i></div>
            <div style="font-size: 1.1rem; font-weight: 500; margin-bottom: 0.75rem;">{title_canon}</div>
            <div>
                {f'<span class="tag tag-catalog">{cat_str}</span>' if cat_str else ''}
                {f'<span class="tag tag-key">{key}</span>' if key else ''}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_right:
        # Card Esecutori & Incisione
        perf_html = ""
        if performers:
            for p in performers:
                name = p.get("name", "Unknown")
                role = p.get("role", "artist")
                inst = p.get("instrument")
                detail = f" • {inst}" if inst else ""
                perf_html += f"""
                <div style="margin-bottom: 0.65rem;">
                    <div style="font-weight: 600;">{name}</div>
                    <div style="margin-top: 2px;">
                        <span class="tag tag-role">{role}</span>
                        <span style="font-size: 0.8rem; color: #888;">{detail}</span>
                    </div>
                </div>
                """
        else:
            perf_html = '<div style="color: #777; font-style: italic;">No specific performer linked</div>'

        st.markdown(
            f"""
        <div class="meta-card">
            <div class="meta-title">Recording & Performers</div>
            <div style="margin-bottom: 0.75rem;">
                <span style="font-size: 0.95rem; font-weight: 600;">Release / Rec. Year:</span>
                <span style="font-size: 0.95rem; margin-left: 4px; color: #60a5fa;">{year or 'Not detected'}</span>
            </div>
            {perf_html}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Sezione JSON grezzo
    with st.expander("🔍 Inspect Full JSON Output"):
        st.json(result)
