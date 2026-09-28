import sqlite3
import urllib.request
import json
import re
from pathlib import Path

# Percorsi robusti basati sulla posizione dello script
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DB_PATH = DATA_DIR / "seed.sqlite"

# Lista canonica dei compositori per il core MVP
TARGET_COMPOSERS = [
    "Ludwig van Beethoven",
    "Johann Sebastian Bach",
    "Wolfgang Amadeus Mozart",
    "Johannes Brahms",
    "Frédéric Chopin",
    "Pyotr Ilyich Tchaikovsky",
    "Franz Schubert",
    "Antonio Vivaldi",
    "Gustav Mahler",
    "Claude Debussy",
]

# Mappatura esatta per il casing canonico dei prefissi
CANONICAL_PREFIXES = {
    "bwv": "BWV",
    "rv": "RV",
    "kv": "KV",
    "k.": "KV",
    "op.": "Op.",
    "opus": "Op.",
    "d.": "D.",
    "hob.": "Hob.",
    "l.": "L.",
}

# Regex avanzata per prefisso catalogo e numero
CATALOG_REGEX = re.compile(
    r"(?:,\s*)?(?:\b(op\.|opus|bwv|kv|k\.|hob\.|d\.|rv|l\.)\s*([posth\.\s]*\d+[a-z]?))",
    re.IGNORECASE,
)

# Regex per il sub-numero (es. "no. 1", "No. 2")
SUB_NUM_REGEX = re.compile(r"(?:no\.|n\.)\s*(\d+)", re.IGNORECASE)

# Regex per estrarre la tonalità in lingua inglese
KEY_REGEX = re.compile(
    r"\bin\s+([A-G](?:\s+flat|\s+sharp)?\s+(?:major|minor))\b", re.IGNORECASE
)


def parse_and_clean_work(raw_title: str):
    """
    Estrae tonalità, prefisso catalogo canonico, numero di catalogo,
    sub-numero e pulisce il titolo rimuovendo duplicati e punteggiatura orfana.
    """
    clean_title = raw_title
    cat_prefix, cat_num, cat_sub, work_key = None, None, None, None

    # 1. Estrazione Tonalità
    key_match = KEY_REGEX.search(clean_title)
    if key_match:
        work_key = key_match.group(1).capitalize()
        clean_title = clean_title.replace(key_match.group(0), "")

    # 2. Estrazione Catalogo Principale e Sub-numero
    cat_match = CATALOG_REGEX.search(clean_title)
    if cat_match:
        raw_prefix = cat_match.group(1).strip()
        cat_prefix = CANONICAL_PREFIXES.get(raw_prefix.lower(), raw_prefix.capitalize())

        raw_num = cat_match.group(2).strip()
        # Rimuove eventuali punti o spazi iniziali (es. .1080 -> 1080)
        clean_num = re.sub(r"^[.\s]+", "", raw_num).strip()
        cat_num = clean_num if clean_num else None

        remaining_text = clean_title[cat_match.end() :]
        sub_match = SUB_NUM_REGEX.search(remaining_text)
        if sub_match:
            cat_sub = sub_match.group(1)
            remaining_text = remaining_text.replace(sub_match.group(0), "")

        clean_title = clean_title[: cat_match.start()] + remaining_text

    # 3. Rimuovi cataloghi doppi rimasti orfani nel titolo (es. ", op. 25", ", op. posth.103")
    clean_title = re.sub(
        r",?\s*op\.(?:\s*posth\.)?\s*\d+[a-z]?",
        "",
        clean_title,
        flags=re.IGNORECASE,
    )

    # 4. Pulizia punteggiatura orfana e spazi multipli
    clean_title = re.sub(r"\s+([,.:])", r"\1", clean_title)
    clean_title = re.sub(r"[,/]\s*$", "", clean_title)
    clean_title = re.sub(r"\s{2,}", " ", clean_title).strip()

    return clean_title, cat_prefix, cat_num, cat_sub, work_key


def create_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composer_canonical TEXT,
            composer_short TEXT,
            title TEXT,
            catalog_prefix TEXT,
            catalog_num TEXT,
            catalog_sub TEXT,
            work_key TEXT
        )
    """)

    # Reset tabella works per rigenerare dati puliti
    cur.execute("DELETE FROM works")

    print("Download dati compositori da Open Opus...")
    url = "https://api.openopus.org/composer/list/pop.json"
    req = urllib.request.Request(url, headers={"User-Agent": "kochel-data-builder"})
    with urllib.request.urlopen(req) as resp:
        composers_data = json.loads(resp.read().decode())["composers"]

    total_inserted = 0

    for comp in composers_data:
        name = comp["complete_name"]
        if name not in TARGET_COMPOSERS:
            continue

        print(f"Scaricando ed elaborando opere per: {name}")
        comp_id = comp["id"]
        works_url = (
            f"https://api.openopus.org/work/list/composer/{comp_id}/genre/all.json"
        )
        works_req = urllib.request.Request(
            works_url, headers={"User-Agent": "kochel-data-builder"}
        )

        try:
            with urllib.request.urlopen(works_req) as w_resp:
                works = json.loads(w_resp.read().decode())["works"]
                batch = []
                for w in works:
                    raw_title = w["title"]
                    clean_title, cat_prefix, cat_num, cat_sub, work_key = (
                        parse_and_clean_work(raw_title)
                    )

                    batch.append(
                        (
                            name,
                            comp["name"],
                            clean_title,
                            cat_prefix,
                            cat_num,
                            cat_sub,
                            work_key,
                        )
                    )

                cur.executemany(
                    """
                    INSERT INTO works (
                        composer_canonical,
                        composer_short,
                        title,
                        catalog_prefix,
                        catalog_num,
                        catalog_sub,
                        work_key
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    batch,
                )
                total_inserted += len(batch)
        except Exception as e:
            print(f"Errore su {name}: {e}")

    conn.commit()
    conn.close()
    print(f"Completato! {total_inserted} opere salvate con successo in {DB_PATH}")


if __name__ == "__main__":
    create_db()
