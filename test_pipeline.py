import sys
from pathlib import Path

# Assicura la visibilità del package src
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import kochel
import json
import time

test_queries = [
    "Chopin nocturne op 9 no 2 rubinstein rec 1965",
    "Beethoven Symphony no. 5 Op. 67 Karajan 1962",
    "Bach BWV 1046 Gould",
]

stress_queries = [
    # Nome file da torrent/rip CD con underscore e metadati audio
    "01_Beethoven_Symphony.5_Op.67_Allegro_Karajan_BPO_1962_FLAC",
    # Notazione compatta senza spazi ed esecutore abbreviato
    "Mozart KV622 Argerich",
    # Query parziale con solo movimento e catalogo
    "Vivaldi RV 589 Gloria in D major",
    # Stringa disordinata con rumore
    "Claudio Abbado Brahms Double Concerto Op 102 Live stereo",
]

print("=== STANDARD TEST QUERIES ===")
for query in test_queries:
    t0 = time.perf_counter()
    res = kochel.parse(query)
    latency = (time.perf_counter() - t0) * 1000

    print(f"\n--- Query: {query} ({latency:.2f} ms) ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))

print("\n\n=== STRESS TEST QUERIES ===")
for query in stress_queries:
    t0 = time.perf_counter()
    res = kochel.parse(query)
    latency = (time.perf_counter() - t0) * 1000

    print(f"\n--- Query: {query} ({latency:.2f} ms) ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))
