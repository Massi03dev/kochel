import sys
import time
from pathlib import Path
import streamlit as st

# Assicura il caricamento corretto del modulo da src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import kochel

# 1. Configurazione Pagina
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.svg"
st.set_page_config(
    page_title="Kochel — Classical Music Metadata Resolver",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🎻",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 2. Design System & Tipografia d'Autore (Dark Luxury & Archival Feel)
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Reset e larghezza leggibile */
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
        max-width: 820px;
    }

    /* Palette e Sfondo Premium */
    body, [data-testid="stAppViewContainer"] {
        background-color: #0b0d11;
        color: #e2e4e9;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Hero Header */
    .hero-container {
        text-align: center;
        margin-bottom: 1.8rem;
    }

    .hero-title {
        font-family: 'Cinzel', serif;
        font-size: 2.6rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #f7f3ea;
        margin: 0.6rem 0 0.3rem 0;
        text-transform: uppercase;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        font-weight: 300;
        color: #9aa1b0;
        max-width: 580px;
        margin: 0 auto 1.2rem auto;
        line-height: 1.5;
    }

    .hero-meta-bar {
        display: inline-flex;
        align-items: center;
        gap: 16px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        padding: 5px 16px;
        font-size: 0.78rem;
        color: #838a99;
        letter-spacing: 0.03em;
    }

    .hero-meta-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .hero-meta-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #10b981;
    }

    /* Container Scheda Archivio */
    .archive-card {
        background: radial-gradient(circle at top left, rgba(30, 36, 48, 0.5), rgba(16, 19, 26, 0.85));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.6rem;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
        margin-top: 1.2rem;
        backdrop-filter: blur(12px);
    }

    .section-eyebrow {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 600;
        color: #d4af37; /* Oro antico classico */
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .composer-name {
        font-family: 'Cinzel', serif;
        font-size: 1.65rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: 0.04em;
        margin: 0;
        line-height: 1.2;
    }

    .source-token {
        font-size: 0.82rem;
        color: #717888;
        margin-top: 0.25rem;
        margin-bottom: 1rem;
    }

    .work-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #e5e8f0;
        margin-bottom: 0.85rem;
        line-height: 1.35;
    }

    /* Badge raffinati */
    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-right: 8px;
        margin-bottom: 6px;
    }

    .badge-catalog {
        background: rgba(197, 160, 89, 0.12);
        border: 1px solid rgba(197, 160, 89, 0.35);
        color: #f1cf88;
        font-family: 'Cinzel', serif;
        letter-spacing: 0.05em;
    }

    .badge-key {
        background: rgba(79, 131, 204, 0.12);
        border: 1px solid rgba(79, 131, 204, 0.3);
        color: #8cb8f0;
    }

    .badge-year {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #c0c5d0;
    }

    /* Performer Row */
    .performer-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 0.75rem 0.95rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .performer-name {
        font-size: 0.96rem;
        font-weight: 600;
        color: #f0f2f7;
    }

    .performer-role-tag {
        font-size: 0.76rem;
        text-transform: capitalize;
        padding: 2px 8px;
        border-radius: 6px;
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.25);
        color: #fbbf24;
    }

    .latency-footer {
        font-size: 0.76rem;
        color: #5d6473;
        margin-top: 1.2rem;
        text-align: right;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 6px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 3. Header & Identità di Marca
if LOGO_PATH.exists():
    col_l, col_img, col_r = st.columns([1, 0.65, 1])
    with col_img:
        st.image(str(LOGO_PATH), use_container_width=True)

hero_bar_html = """<div class="hero-container">
<h1 class="hero-title">Kochel</h1>
<p class="hero-subtitle">Deterministic entity resolver for unstructured classical music metadata.</p>
<div class="hero-meta-bar">
<div class="hero-meta-item"><span class="hero-meta-dot"></span>Sub-15ms CPU</div>
<div class="hero-meta-item">•</div>
<div class="hero-meta-item">MiniLM INT8 (ONNX)</div>
<div class="hero-meta-item">•</div>
<div class="hero-meta-item">Canonical SQLite Catalog</div>
</div>
</div>"""

if hasattr(st, "html"):
    st.html(hero_bar_html)
else:
    st.markdown(hero_bar_html, unsafe_allow_html=True)
st.write("")

# 4. Esempi Veloci tramite Pills
EXAMPLES = {
    "Beethoven 5 (Karajan)": "Beethoven Symphony no. 5 Op. 67 Karajan 1962",
    "Chopin Nocturne (Rubinstein)": "Chopin nocturne op 9 no 2 rubinstein rec 1965",
    "Mozart KV 622 (Argerich)": "Mozart KV622 Argerich",
    "Messy Torrent Rip": "01_Beethoven_Symphony.5_Op.67_Allegro_Karajan_BPO_1962_FLAC",
    "Inverted Artist / Composer": "Claudio Abbado Brahms Double Concerto Op 102 Live stereo",
    "Bach BWV 1046 (Gould)": "Bach BWV 1046 Gould",
    "Vivaldi Gloria": "Vivaldi RV 589 Gloria in D major",
}

if "query_input" not in st.session_state:
    st.session_state.query_input = "Beethoven Symphony no. 5 Op. 67 Karajan 1962"


def set_example(query: str):
    st.session_state.query_input = query


st.markdown(
    '<div style="font-size: 0.82rem; font-weight: 500; color: #838a99; margin-bottom: 0.4rem;">Select a curated test query:</div>',
    unsafe_allow_html=True,
)

# Renderizza i pulsanti di esempio in una riga compatta
chips_cols = st.columns([1, 1, 1, 1])
example_keys = list(EXAMPLES.keys())
for i, key in enumerate(example_keys[:4]):
    with chips_cols[i]:
        if st.button(key, key=f"chip_{i}", use_container_width=True):
            set_example(EXAMPLES[key])

chips_cols_2 = st.columns([1, 1, 1])
for i, key in enumerate(example_keys[4:]):
    with chips_cols_2[i]:
        if st.button(key, key=f"chip_2_{i}", use_container_width=True):
            set_example(EXAMPLES[key])

st.write("")

# 5. Form di Input
with st.form("resolver_form"):
    col_input, col_submit = st.columns([5.5, 1.2], vertical_alignment="bottom")
    with col_input:
        query_val = st.text_input(
            "Search or Paste Raw Classical Track String",
            value=st.session_state.query_input,
            placeholder="e.g. Beethoven Symphony 5 Op. 67 Karajan 1962",
            label_visibility="collapsed",
        )
    with col_submit:
        submitted = st.form_submit_button(
            "Resolve", type="primary", use_container_width=True
        )

# 6. Elaborazione e Scheda di Risoluzione
if query_val and query_val.strip():
    t0 = time.perf_counter()
    result = kochel.parse(query_val.strip())
    latency_ms = (time.perf_counter() - t0) * 1000

    work = result.get("work", {})
    composer = work.get("composer", {})
    catalog = work.get("catalog", {})
    key = work.get("key")
    recording = result.get("recording", {})
    performers = recording.get("performers", [])
    year = recording.get("year")

    comp_canonical = composer.get("canonical") or "Unknown Composer"
    comp_raw = composer.get("raw")
    work_title = work.get("canonical_title") or "Unknown Work Title"

    # Composizione catalogo formattato (es. Op. 67, BWV 1046, KV 622)
    cat_badges = []
    if catalog.get("prefix") and catalog.get("number"):
        cat_str = f"{catalog['prefix']} {catalog['number']}"
        if catalog.get("sub_number"):
            cat_str += f" No. {catalog['sub_number']}"
        cat_badges.append(f'<span class="pill-badge badge-catalog">🎼 {cat_str}</span>')

    if key:
        cat_badges.append(f'<span class="pill-badge badge-key">🎹 {key}</span>')

    if year:
        cat_badges.append(f'<span class="pill-badge badge-year">📅 {year}</span>')

    # Scheda Risultati (Renderizzata con st.html per evitare che il parser Markdown scambi gli spazi per blocchi di codice)
    badges_html = "".join(cat_badges) if cat_badges else '<span style="color: #666; font-size: 0.85rem;">No catalog identified</span>'

    if performers:
        perf_cards = []
        for p in performers:
            p_name = p.get("name") or "Unknown"
            p_inst = p.get("instrument") or "Ensemble / Soloist"
            p_role = p.get("role", "artist")
            perf_cards.append(
                f'<div class="performer-card">'
                f'<div>'
                f'<div class="performer-name">{p_name}</div>'
                f'<div style="font-size: 0.78rem; color: #828a9b;">{p_inst}</div>'
                f'</div>'
                f'<span class="performer-role-tag">{p_role}</span>'
                f'</div>'
            )
        performers_html = "".join(perf_cards)
    else:
        performers_html = '<div style="color: #616773; font-style: italic; font-size: 0.88rem; padding: 1rem 0;">No performers detected in input query.</div>'

    card_html = f"""<div class="archive-card">
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
<div>
<div class="section-eyebrow">Composition & Catalog</div>
<div class="composer-name">{comp_canonical}</div>
<div class="source-token">Raw input: <i>"{comp_raw or comp_canonical}"</i></div>
<div class="work-title">{work_title}</div>
<div style="margin-top: 0.6rem;">{badges_html}</div>
</div>
<div>
<div class="section-eyebrow">Recording & Performers</div>
<div>{performers_html}</div>
</div>
</div>
<div class="latency-footer">
<span>Deterministic CPU inference in <b>{latency_ms:.2f} ms</b></span>
<span>•</span>
<span>INT8 MiniLM + Canonical SQLite</span>
</div>
</div>"""

    if hasattr(st, "html"):
        st.html(card_html)
    else:
        st.markdown(card_html, unsafe_allow_html=True)

    # 7. Dettagli JSON completi per ispezione
    with st.expander("🔍 View Raw Output Schema"):
        st.json(result)
