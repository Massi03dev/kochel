import json
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MODELS_DIR = Path(__file__).parent / "models"


class TokenExtractor:
    def __init__(self):
        # 1. Carica il tokenizer compilato
        self.tokenizer = Tokenizer.from_file(str(MODELS_DIR / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=128)

        # 2. Carica la mappa label
        with open(MODELS_DIR / "labels.json") as f:
            label_map = json.load(f)
        self.id2label = {int(v): k for k, v in label_map.items()}

        # 3. Sessione ONNX ottimizzata per CPU
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            str(MODELS_DIR / "kochel_minilm_quantized.onnx"),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )

    def extract_spans(self, text: str) -> dict:
        # Normalizzazione caratteri tipici da file audio (underscore -> spazi)
        normalized_text = text.replace("_", " ")

        enc = self.tokenizer.encode(normalized_text)
        if not enc.ids:
            return {}

        input_ids = np.array([enc.ids], dtype=np.int64)
        attention_mask = np.array([enc.attention_mask], dtype=np.int64)

        outputs = self.session.run(
            None, {"input_ids": input_ids, "attention_mask": attention_mask}
        )
        logits = outputs[0][0]
        preds = np.argmax(logits, axis=-1)

        spans = []
        curr_tag = None
        curr_start = None
        curr_end = None

        for pred_id, (start, end) in zip(preds, enc.offsets):
            if start == end:
                continue

            label = self.id2label.get(pred_id, "O")

            if label == "O":
                if curr_tag is not None:
                    spans.append((curr_tag, curr_start, curr_end))
                    curr_tag, curr_start, curr_end = None, None, None
                continue

            bio = label[0]
            tag = label[2:].lower()

            is_subword_continuation = (curr_tag == tag and start == curr_end)

            if bio == "B" and not is_subword_continuation:
                if curr_tag is not None:
                    spans.append((curr_tag, curr_start, curr_end))
                curr_tag = tag
                curr_start = start
                curr_end = end
            else:
                if curr_tag is None:
                    curr_tag = tag
                    curr_start = start
                curr_end = end

        if curr_tag is not None:
            spans.append((curr_tag, curr_start, curr_end))

        extracted = {
            "composer": None,
            "work": None,
            "catalog_prefix": None,
            "catalog_num": None,
            "catalog_sub": None,
            "key": None,
            "performer": None,
            "year": None,
            "movement_name": None,
        }

        for tag, s_idx, e_idx in spans:
            val = normalized_text[s_idx:e_idx].strip()
            if tag in extracted:
                if extracted[tag]:
                    extracted[tag] += f" {val}"
                else:
                    extracted[tag] = val

        return extracted
