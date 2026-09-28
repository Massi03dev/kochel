import sqlite3
import json
import re
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "seed.sqlite"

# Parole comuni da ignorare durante il matching degli esecutori
STOPWORDS = {
    "in",
    "of",
    "the",
    "and",
    "for",
    "with",
    "rec",
    "live",
    "stereo",
    "mono",
    "major",
    "minor",
    "moll",
    "dur",
    "flac",
    "mp3",
    "cd",
    "track",
    "da",
    "di",
    "del",
    "della",
    "dei",
    "degli",
    "con",
    "su",
    "per",
    "tra",
    "fra",
}


class EntityResolver:
    def __init__(self, db_path: Path = None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        self._load_cache()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _load_cache(self):
        """Carica compositori ed esecutori in memoria per matching istantaneo e sicuro."""
        conn = self._get_connection()
        cur = conn.cursor()

        # 1. Cache Compositori
        cur.execute("SELECT DISTINCT composer_canonical, composer_short FROM works")
        self.composers = cur.fetchall()

        # 2. Cache Esecutori
        cur.execute(
            "SELECT canonical_name, aliases, default_role, instrument FROM performers"
        )
        self.performers_cache = []
        for name, aliases_raw, role, inst in cur.fetchall():
            aliases = json.loads(aliases_raw) if aliases_raw else []
            self.performers_cache.append(
                {
                    "canonical_name": name,
                    "aliases": [a.lower() for a in aliases],
                    "default_role": role,
                    "instrument": inst,
                    "tokens": set(name.lower().split() + [a.lower() for a in aliases]),
                }
            )
        conn.close()

    @staticmethod
    def _clean_catalog_sub(raw_sub: str):
        if not raw_sub:
            return None
        match = re.search(r"\d+[a-zA-Z]?", raw_sub)
        return match.group(0) if match else raw_sub.strip()

    def _match_single_performer(self, candidate_str: str):
        cand = candidate_str.strip().lower()
        if not cand or cand in STOPWORDS or len(cand) < 3:
            return None

        for p in self.performers_cache:
            # 1. Match esatto sul nome o sugli alias
            if cand == p["canonical_name"].lower() or cand in p["aliases"]:
                return {
                    "name": p["canonical_name"],
                    "role": p["default_role"],
                    "instrument": p["instrument"],
                }
            # 2. Match su cognome o sigla (es. "Karajan" o "BPO")
            if cand in p["tokens"]:
                return {
                    "name": p["canonical_name"],
                    "role": p["default_role"],
                    "instrument": p["instrument"],
                }
        return None

    def resolve(self, spans: dict) -> dict:
        raw_composer = spans.get("composer")
        raw_work = spans.get("work")
        raw_cat_prefix = spans.get("catalog_prefix")
        raw_cat_num = spans.get("catalog_num")
        if raw_cat_num:
            raw_cat_num = raw_cat_num.replace(" ", "")

        raw_cat_sub = self._clean_catalog_sub(spans.get("catalog_sub"))
        raw_performer = spans.get("performer")
        extracted_key = spans.get("key")

        conn = self._get_connection()
        cur = conn.cursor()

        canonical_composer = None
        swapped_performer = None

        # 1. Disambiguazione Compositore vs Interprete
        if raw_composer:
            raw_comp_clean = raw_composer.strip().lower()
            for c_canon, c_short in self.composers:
                if (
                    raw_comp_clean == c_short.lower()
                    or raw_comp_clean == c_canon.lower()
                    or c_short.lower() in raw_comp_clean
                ):
                    canonical_composer = c_canon
                    break

            # Se non è un compositore, verifica se è un interprete scambiato di posto
            if not canonical_composer:
                perf_match = self._match_single_performer(raw_composer)
                if perf_match:
                    swapped_performer = perf_match
                    if raw_work:
                        for c_canon, c_short in self.composers:
                            if (
                                c_short.lower() in raw_work.lower()
                                or c_canon.lower() in raw_work.lower()
                            ):
                                canonical_composer = c_canon
                                raw_work = re.sub(
                                    re.escape(c_short),
                                    "",
                                    raw_work,
                                    flags=re.IGNORECASE,
                                ).strip()
                                break

        # 2. Risoluzione Opera, Catalogo e Tonalità
        canonical_title = None
        catalog_canonical_prefix = None
        inferred_key = extracted_key

        if canonical_composer and raw_cat_num:
            query = """
                SELECT title, work_key, catalog_prefix, catalog_num 
                FROM works 
                WHERE composer_canonical = ? AND catalog_num = ?
            """
            params = [canonical_composer, raw_cat_num]
            if raw_cat_sub:
                query += " AND catalog_sub = ?"
                params.append(raw_cat_sub)

            cur.execute(query + " LIMIT 1", params)
            work_row = cur.fetchone()

            if not work_row and raw_cat_sub:
                cur.execute(
                    """
                    SELECT title, work_key, catalog_prefix, catalog_num 
                    FROM works WHERE composer_canonical = ? AND catalog_num = ? LIMIT 1
                """,
                    (canonical_composer, raw_cat_num),
                )
                work_row = cur.fetchone()

            if work_row:
                canonical_title = work_row[0]
                if not inferred_key and work_row[1]:
                    inferred_key = work_row[1]
                catalog_canonical_prefix = work_row[2]

        elif canonical_composer and raw_work:
            cur.execute(
                """
                SELECT title, work_key, catalog_prefix, catalog_num, catalog_sub
                FROM works 
                WHERE composer_canonical = ? AND title LIKE ?
                LIMIT 1
            """,
                (canonical_composer, f"%{raw_work.strip()}%"),
            )
            work_row = cur.fetchone()
            if work_row:
                canonical_title = work_row[0]
                if not inferred_key and work_row[1]:
                    inferred_key = work_row[1]
                catalog_canonical_prefix = work_row[2]
                raw_cat_num = raw_cat_num or work_row[3]
                raw_cat_sub = raw_cat_sub or work_row[4]

        # 3. Risoluzione Esecutori
        performers_resolved = []
        if swapped_performer:
            performers_resolved.append(swapped_performer)

        if raw_performer:
            # Suddivide su separatori o spazi multipli
            candidates = re.split(r"[,/_\s]+", raw_performer.strip())

            # Prova prima il blocco intero
            full_match = self._match_single_performer(raw_performer)
            if full_match and full_match not in performers_resolved:
                performers_resolved.append(full_match)
            else:
                # Prova i singoli candidati
                for cand in candidates:
                    match = self._match_single_performer(cand)
                    if match and match not in performers_resolved:
                        performers_resolved.append(match)

            # Se nessun interprete è stato riconosciuto, controlla che non sia un falso positivo
            if not performers_resolved:
                clean_p = raw_performer.strip()
                is_noise = False

                # Controllo bidirezionale con il titolo (es. "Gloria in" contiene "Gloria")
                if canonical_title:
                    c_title_low = canonical_title.lower()
                    p_low = clean_p.lower()
                    if p_low in c_title_low or c_title_low in p_low:
                        is_noise = True

                # Se tutti i token residui sono stopwords (es. "in")
                words_left = [
                    w
                    for w in re.split(r"\s+", clean_p.lower())
                    if w not in STOPWORDS
                ]
                if not words_left:
                    is_noise = True

                if not is_noise:
                    performers_resolved.append(
                        {
                            "name": raw_performer,
                            "role": "unknown",
                            "instrument": None,
                        }
                    )

        conn.close()

        return {
            "work": {
                "composer": {
                    "raw": raw_composer,
                    "canonical": canonical_composer or raw_composer,
                },
                "canonical_title": canonical_title or raw_work,
                "catalog": {
                    "prefix": catalog_canonical_prefix
                    or (raw_cat_prefix.upper() if raw_cat_prefix else None),
                    "number": raw_cat_num,
                    "sub_number": raw_cat_sub,
                },
                "key": inferred_key,
            },
            "recording": {"year": spans.get("year"), "performers": performers_resolved},
        }
