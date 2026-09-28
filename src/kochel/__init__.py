from .extractor import TokenExtractor
from .resolver import EntityResolver

_extractor = None
_resolver = None


def _get_pipeline():
    global _extractor, _resolver
    if _extractor is None:
        _extractor = TokenExtractor()
        _resolver = EntityResolver()
    return _extractor, _resolver


def parse(text: str) -> dict:
    """
    Esegue il parsing end-to-end e la risoluzione canonica di metadati musicali classici.
    """
    extractor, resolver = _get_pipeline()
    raw_spans = extractor.extract_spans(text)
    result = resolver.resolve(raw_spans)
    result["raw_input"] = text
    return result


__all__ = ["parse", "TokenExtractor", "EntityResolver"]
