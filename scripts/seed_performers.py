import sqlite3
import json
from pathlib import Path

# Percorsi robusti basati sulla posizione dello script
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DB_PATH = DATA_DIR / "seed.sqlite"

PERFORMERS_DATA = [
    # Pianisti (soloist)
    ("Arthur Rubinstein", ["Rubinstein", "A. Rubinstein"], "soloist", "piano"),
    ("Glenn Gould", ["Gould", "G. Gould"], "soloist", "piano"),
    ("Maurizio Pollini", ["Pollini", "M. Pollini"], "soloist", "piano"),
    ("Martha Argerich", ["Argerich", "M. Argerich"], "soloist", "piano"),
    ("Vladimir Horowitz", ["Horowitz", "V. Horowitz"], "soloist", "piano"),
    ("Sviatoslav Richter", ["Richter", "S. Richter"], "soloist", "piano"),
    ("Claudio Arrau", ["Arrau", "C. Arrau"], "soloist", "piano"),
    ("Emil Gilels", ["Gilels", "E. Gilels"], "soloist", "piano"),
    ("Alfred Brendel", ["Brendel", "A. Brendel"], "soloist", "piano"),
    ("Krystian Zimerman", ["Zimerman", "K. Zimerman"], "soloist", "piano"),
    # Violinisti (soloist)
    ("Jascha Heifetz", ["Heifetz", "J. Heifetz"], "soloist", "violin"),
    ("David Oistrakh", ["Oistrakh", "D. Oistrakh"], "soloist", "violin"),
    ("Itzhak Perlman", ["Perlman", "I. Perlman"], "soloist", "violin"),
    ("Anne-Sophie Mutter", ["Mutter", "A. S. Mutter"], "soloist", "violin"),
    ("Yehudi Menuhin", ["Menuhin", "Y. Menuhin"], "soloist", "violin"),
    ("Hilary Hahn", ["Hahn", "H. Hahn"], "soloist", "violin"),
    # Violoncellisti (soloist)
    (
        "Mstislav Rostropovich",
        ["Rostropovich", "M. Rostropovich", "Slava"],
        "soloist",
        "cello",
    ),
    ("Yo-Yo Ma", ["Yo Yo Ma", "Yo-yo Ma", "Ma"], "soloist", "cello"),
    ("Pablo Casals", ["Casals", "P. Casals"], "soloist", "cello"),
    ("Jacqueline du Pré", ["du Pré", "du Pre", "J. du Pré"], "soloist", "cello"),
    # Direttori d'orchestra (conductor)
    ("Herbert von Karajan", ["Karajan", "HvK", "H. von Karajan"], "conductor", None),
    ("Leonard Bernstein", ["Bernstein", "L. Bernstein", "Lennie"], "conductor", None),
    ("Claudio Abbado", ["Abbado", "C. Abbado"], "conductor", None),
    ("Carlos Kleiber", ["Kleiber", "C. Kleiber"], "conductor", None),
    ("John Eliot Gardiner", ["Gardiner", "J. E. Gardiner"], "conductor", None),
    ("Otto Klemperer", ["Klemperer", "O. Klemperer"], "conductor", None),
    ("Georg Solti", ["Solti", "G. Solti"], "conductor", None),
    ("Sergiu Celibidache", ["Celibidache", "S. Celibidache"], "conductor", None),
    (
        "Wilhelm Furtwängler",
        ["Furtwängler", "Furtwangler", "W. Furtwängler"],
        "conductor",
        None,
    ),
    # Orchestre ed Ensemble (orchestra / ensemble)
    (
        "Berliner Philharmoniker",
        ["BPO", "Berlin Philharmonic", "Berliner Phil."],
        "orchestra",
        None,
    ),
    (
        "Wiener Philharmoniker",
        ["VPO", "Vienna Philharmonic", "Wiener Phil."],
        "orchestra",
        None,
    ),
    ("London Symphony Orchestra", ["LSO", "London Symphony"], "orchestra", None),
    ("Chicago Symphony Orchestra", ["CSO", "Chicago Symphony"], "orchestra", None),
    (
        "Concertgebouw Orchestra",
        ["Royal Concertgebouw", "Concertgebouw"],
        "orchestra",
        None,
    ),
    (
        "The English Baroque Soloists",
        ["English Baroque Soloists", "EBS"],
        "ensemble",
        None,
    ),
]


def seed_performers():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS performers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT,
            aliases TEXT,
            default_role TEXT,
            instrument TEXT
        )
    """)
    cur.execute("DELETE FROM performers")  # Reset tabella

    for name, aliases, role, inst in PERFORMERS_DATA:
        cur.execute(
            """
            INSERT INTO performers (canonical_name, aliases, default_role, instrument)
            VALUES (?, ?, ?, ?)
        """,
            (name, json.dumps(aliases), role, inst),
        )

    conn.commit()
    conn.close()
    print(f"Seed performers caricato con successo in {DB_PATH}.")


if __name__ == "__main__":
    seed_performers()
