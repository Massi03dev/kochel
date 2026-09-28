import sqlite3
import json
import random
import re
from pathlib import Path
from transformers import AutoTokenizer

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DB_PATH = BASE_DIR / "data" / "seed.sqlite"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Vocabolario BIO formale per kochel
LABEL_LIST = [
    "O",
    "B-COMPOSER",
    "I-COMPOSER",
    "B-WORK",
    "I-WORK",
    "B-CATALOG_PREFIX",
    "B-CATALOG_NUM",
    "B-CATALOG_SUB",
    "B-KEY",
    "I-KEY",
    "B-MOVEMENT_NUM",
    "B-MOVEMENT_NAME",
    "I-MOVEMENT_NAME",
    "B-PERFORMER",
    "I-PERFORMER",
    "B-YEAR",
]
LABEL_TO_ID = {label: i for i, label in enumerate(LABEL_LIST)}

# Salva il mapping labels.json per Hugging Face e ONNX Runtime
with open(OUTPUT_DIR / "labels.json", "w") as f:
    json.dump(LABEL_TO_ID, f, indent=2)

# Variazioni per comporre tonalità realistiche
KEY_ALIASES = {
    "major": ["major", "dur", "maggiore", "majeur"],
    "minor": ["minor", "moll", "minore", "mineur"],
}

# Movimenti finti ma realistici per sporcare i dati
MOVEMENTS = [
    ("I", "Allegro"),
    ("II", "Adagio"),
    ("III", "Scherzo"),
    ("IV", "Presto"),
    ("I", "Allegro con brio"),
    ("III", "Rondo"),
    ("1.", "Allegro maestoso"),
    ("2.", "Andante sostenuto"),
]

# Rumore tipico dei file audio reali
NOISE_TOKENS = [
    "FLAC",
    "MP3",
    "320kbps",
    "Remastered",
    "rec.",
    "Live 1972",
    "stereo",
    "mono",
    "CD1",
    "Track 01",
    "Deutsche Grammophon",
    "Decca",
    "EMI",
    "Warner Classics",
    "HQ",
    "disc 2",
]


def load_seed_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT composer_canonical, composer_short, title, catalog_prefix, catalog_num, catalog_sub, work_key FROM works"
    )
    works = cur.fetchall()

    cur.execute("SELECT canonical_name, aliases FROM performers")
    performers_raw = cur.fetchall()

    performers = []
    for name, aliases_json in performers_raw:
        alias_list = json.loads(aliases_json)
        performers.append([name] + alias_list)

    conn.close()
    return works, performers


def perturb_key(raw_key):
    if not raw_key or random.random() < 0.3:
        return None
    # Es. "C minor", "E flat major", "F sharp minor"
    parts = raw_key.strip().rsplit(" ", 1)
    if len(parts) == 2:
        note, mode = parts
    else:
        note, mode = raw_key, "major"

    mode_variant = random.choice(KEY_ALIASES.get(mode.lower(), [mode]))

    sep = random.choice([" ", "-", " "])
    if mode_variant in ["dur", "moll"]:
        return f"{note.lower()}{sep}{mode_variant}"
    return f"{note}{sep}{mode_variant}"


def generate_sample(works, performers):
    work = random.choice(works)
    comp_canon, comp_short, title, cat_prefix, cat_num, cat_sub, work_key = work

    # Scegli variante compositore
    composer_choice = random.choice([comp_short, comp_canon, comp_short.upper()])

    # Gestione catalogo
    chosen_prefix = None
    if cat_prefix:
        if random.random() < 0.2:
            chosen_prefix = cat_prefix.lower()
        else:
            chosen_prefix = cat_prefix

    # Esecutori (da 0 a 2 per traccia)
    sample_performers = []
    if random.random() < 0.8:
        p1 = random.choice(random.choice(performers))
        sample_performers.append(p1)
        if random.random() < 0.4:
            p2 = random.choice(random.choice(performers))
            if p2 != p1:
                sample_performers.append(p2)

    # Anno di registrazione simulato
    year = str(random.randint(1950, 2024)) if random.random() < 0.5 else None

    # Eventuale movimento
    mvt = random.choice(MOVEMENTS) if random.random() < 0.35 else None

    # Tonalità perturbata
    key_variant = perturb_key(work_key)

    # Costruzione tracciata dei blocchi
    # Ogni elemento è una tupla: (testo, label_tipo)
    blocks = []

    # Struttura dei template randomica
    template_type = random.choice(
        ["standard", "torrent_name", "id3_minimal", "catalog_first"]
    )

    if template_type == "standard":
        blocks.append((composer_choice, "COMPOSER"))
        blocks.append((random.choice([" - ", " ", ": "]), None))
        blocks.append((title, "WORK"))
        if key_variant:
            blocks.append((f" in {key_variant}", "KEY_BLOCK"))
        if chosen_prefix and cat_num:
            blocks.append((" " + chosen_prefix, "CATALOG_PREFIX"))
            blocks.append((" " + cat_num, "CATALOG_NUM"))
            if cat_sub:
                blocks.append((f" no. {cat_sub}", "CATALOG_SUB"))
        if mvt:
            blocks.append((f" - {mvt[0]}", "MOVEMENT_NUM"))
            blocks.append((f" {mvt[1]}", "MOVEMENT_NAME"))
        for perf in sample_performers:
            blocks.append((random.choice([" - ", " / ", " "]), None))
            blocks.append((perf, "PERFORMER"))
        if year:
            blocks.append((f" ({year})", "YEAR_BLOCK"))

    elif template_type == "torrent_name":
        # Formato rip audio: "01.Beethoven_Symphony.5_Op.67_Karajan_1962_FLAC"
        blocks.append((str(random.randint(1, 25)).zfill(2) + ". ", None))
        blocks.append((composer_choice, "COMPOSER"))
        blocks.append(("_", None))
        blocks.append((title.replace(" ", "_"), "WORK"))
        if chosen_prefix and cat_num:
            blocks.append((f"_{chosen_prefix}{cat_num}", "CAT_ATTACHED"))
        for perf in sample_performers:
            blocks.append((f"_{perf.replace(' ', '_')}", "PERFORMER"))
        if year:
            blocks.append((f"_{year}", "YEAR"))
        blocks.append((f"_{random.choice(NOISE_TOKENS)}", None))

    else:
        # Formato compatto: "Chopin op 9 no 2 rubinstein 1965"
        blocks.append((composer_choice, "COMPOSER"))
        blocks.append((" ", None))
        blocks.append((title, "WORK"))
        if chosen_prefix and cat_num:
            blocks.append((" " + chosen_prefix.replace(".", ""), "CATALOG_PREFIX"))
            blocks.append((" " + cat_num, "CATALOG_NUM"))
            if cat_sub:
                blocks.append((" " + cat_sub, "CATALOG_SUB"))
        for perf in sample_performers:
            blocks.append((" " + perf, "PERFORMER"))
        if year:
            blocks.append((" " + year, "YEAR"))

    # Rumore casuale aggiunto a fine stringa
    if random.random() < 0.25:
        blocks.append((" " + random.choice(NOISE_TOKENS), None))

    # Assemblaggio testo completo e calcolo offset precisi
    full_text = ""
    spans = []  # (start_char, end_char, label)

    for text, label_type in blocks:
        start_idx = len(full_text)
        full_text += text
        end_idx = len(full_text)

        if not label_type:
            continue

        # Sotto-parsing dei blocchi compositi
        if label_type == "KEY_BLOCK":
            # Salva solo la tonalità saltando " in "
            pos = text.lower().find(key_variant.lower())
            if pos != -1:
                k_start = start_idx + pos
                spans.append((k_start, k_start + len(key_variant), "KEY"))
            else:
                spans.append((start_idx, end_idx, "KEY"))
        elif label_type == "YEAR_BLOCK":
            y_start = start_idx + text.find(year)
            spans.append((y_start, y_start + len(year), "YEAR"))
        elif label_type == "CAT_ATTACHED":
            # prefisso e numero attaccati (es. Op.67)
            spans.append((start_idx + 1, end_idx, "CATALOG_ATTACHED"))
        else:
            # Tag diretto, pulendo eventuali spazi iniziali registrati
            clean_str = text.lstrip(" _-:/")
            offset = len(text) - len(clean_str)
            spans.append((start_idx + offset, end_idx, label_type))

    return full_text, spans


def align_tokens_with_spans(tokenizer, text, spans):
    encoding = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
    tokens = tokenizer.convert_ids_to_tokens(encoding["input_ids"])
    offset_mapping = encoding["offset_mapping"]

    labels = ["O"] * len(tokens)

    for start_char, end_char, label_type in spans:
        if label_type == "CAT_ATTACHED":
            # Split euristico sul token attaccato
            sub_label = "CATALOG_NUM"
        else:
            sub_label = label_type

        first_token = True
        for i, (tok_start, tok_end) in enumerate(offset_mapping):
            if tok_start >= tok_end:
                continue
            # Verifica intersezione tra token e span annotato
            if max(tok_start, start_char) < min(tok_end, end_char):
                prefix = "B-" if first_token else "I-"
                # Alcuni tag non necessitano di prefisso I- se sono atomici
                if sub_label in [
                    "CATALOG_PREFIX",
                    "CATALOG_NUM",
                    "CATALOG_SUB",
                    "YEAR",
                    "MOVEMENT_NUM",
                ]:
                    labels[i] = f"B-{sub_label}"
                else:
                    labels[i] = f"{prefix}{sub_label}"
                first_token = False

    ner_tag_ids = [LABEL_TO_ID.get(l, 0) for l in labels]
    return {"text": text, "tokens": tokens, "ner_tags": ner_tag_ids}


def main():
    print("Inizializzazione tokenizer MiniLM...")
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

    works, performers = load_seed_data()
    print(f"Caricate {len(works)} opere e {len(performers)} esecutori.")

    for split_name, count in [("train", 30000), ("val", 3000), ("test", 3000)]:
        print(f"Generazione split {split_name} ({count} campioni)...")
        file_path = OUTPUT_DIR / f"{split_name}.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for _ in range(count):
                text, spans = generate_sample(works, performers)
                sample = align_tokens_with_spans(tokenizer, text, spans)
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"Dataset generato con successo in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
