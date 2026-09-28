from extractor import TokenExtractor
import json
import time

extractor = TokenExtractor()

query = "Chopin nocturne op 9 no 2 rubinstein rec 1965"

# Misura latenza
start = time.perf_counter()
spans = extractor.extract_spans(query)
latency_ms = (time.perf_counter() - start) * 1000

print(f"Test query: '{query}'")
print(f"Latenza CPU: {latency_ms:.2f} ms")
print(json.dumps(spans, indent=2))
