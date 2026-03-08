# Architecture Review

Reviewed 25 files.

## arc-001-9138f39c - Pipeline hardcodes extractor/parser implementations
Severity: medium
Location: backend/services/tradeline_extraction/pipeline.py:39

TradelineExtractionPipeline instantiates concrete extractor/parser/storage classes directly, which makes swapping strategies or testing alternative parsers harder.

Recommendation:
Introduce dependency injection or factory-based initialization so different extractors/parsers can be configured without editing the pipeline class.

Snippet:
```
def __init__(self, use_real_world_parser: bool = True):
    self.pdf_extractor = TransUnionPDFExtractor()
    self.parser = RealWorldTransUnionParser() if use_real_world_parser else TransUnionTradelineParser()
```
