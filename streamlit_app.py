import sys
import time
from pathlib import Path
import streamlit as st

# Assicura la risoluzione del package kochel da src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import kochel

st.set_page_config(
    page_title="Kochel - Classical Music Parser", page_icon="🎼", layout="centered"
)

st.title("🎼 Kochel: Classical Music Metadata Parser")
st.markdown(
    "Extracts and normalizes classical music metadata using a compact **INT8 MiniLM** "
    "transformer and an embedded **canonical SQLite catalog**."
)

sample_queries = [
    "Chopin nocturne op 9 no 2 rubinstein rec 1965",
    "Beethoven Symphony no. 5 Op. 67 Karajan 1962",
    "01_Beethoven_Symphony.5_Op.67_Allegro_Karajan_BPO_1962_FLAC",
    "Bach BWV 1046 Gould",
    "Mozart KV622 Argerich",
    "Claudio Abbado Brahms Double Concerto Op 102 Live stereo",
    "Vivaldi RV 589 Gloria in D major",
]

selected_example = st.selectbox(
    "💡 Choose an example or type your own below:", [""] + sample_queries
)
default_text = (
    selected_example
    if selected_example
    else "Beethoven Symphony no. 5 Op. 67 Karajan 1962"
)

input_query = st.text_input("Raw input query / audio filename:", value=default_text)

if st.button("Parse Metadata", type="primary") or input_query:
    if input_query.strip():
        t0 = time.perf_counter()
        result = kochel.parse(input_query.strip())
        latency = (time.perf_counter() - t0) * 1000

        st.caption(f"⚡ Inferred and linked in **{latency:.2f} ms** on CPU")
        st.json(result)
