import sys
import time
from pathlib import Path
import gradio as gr

# Ensure the package is resolved from src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import kochel

EXAMPLES = [
    ["Chopin nocturne op 9 no 2 rubinstein rec 1965"],
    ["Beethoven Symphony no. 5 Op. 67 Karajan 1962"],
    ["01_Beethoven_Symphony.5_Op.67_Allegro_Karajan_BPO_1962_FLAC"],
    ["Bach BWV 1046 Gould"],
    ["Mozart KV622 Argerich"],
    ["Claudio Abbado Brahms Double Concerto Op 102 Live stereo"],
    ["Vivaldi RV 589 Gloria in D major"],
]


def parse_metadata(raw_text: str):
    if not raw_text or not raw_text.strip():
        return {}, "⚠️ Please enter an input string."

    t0 = time.perf_counter()
    result = kochel.parse(raw_text.strip())
    latency_ms = (time.perf_counter() - t0) * 1000

    status = f"⚡ Processed in **{latency_ms:.2f} ms** on CPU (MiniLM INT8 + SQLite)"
    return result, status


# Gradio UI definition
with gr.Blocks(theme=gr.themes.Soft(), title="Kochel - Classical Music Parser") as demo:
    gr.Markdown("""
        # 🎼 Kochel: Classical Music Metadata Parser
        Extracts and normalizes classical music metadata from messy audio filenames, CD rips, or search queries.  
        Powered by an ultra-fast **quantized INT8 MiniLM encoder** coupled with an embedded **canonical SQLite catalog**.
        """)

    with gr.Row():
        with gr.Column(scale=5):
            input_text = gr.Textbox(
                label="Raw input string",
                placeholder="e.g. Beethoven Symphony 5 Op. 67 Karajan 1962",
                lines=2,
            )
            submit_btn = gr.Button("Parse Metadata", variant="primary")
            latency_badge = gr.Markdown("")

        with gr.Column(scale=6):
            output_json = gr.JSON(label="Canonical Resolved Metadata")

    submit_btn.click(
        fn=parse_metadata, inputs=[input_text], outputs=[output_json, latency_badge]
    )
    input_text.submit(
        fn=parse_metadata, inputs=[input_text], outputs=[output_json, latency_badge]
    )

    gr.Examples(
        examples=EXAMPLES,
        inputs=[input_text],
        fn=parse_metadata,
        outputs=[output_json, latency_badge],
        cache_examples=False,
    )

if __name__ == "__main__":
    demo.launch()
