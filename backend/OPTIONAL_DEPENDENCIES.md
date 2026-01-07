# Optional Backend Dependencies

## Overview

Some advanced features require large ML libraries that are optional. The backend will work without them but with reduced functionality.

## AI/ML Features (Optional)

### Transformers + PyTorch
**Used for:** Advanced AI validation and NER (Named Entity Recognition)
**Size:** ~4GB download
**Installation:**
```bash
pip install transformers==4.35.0 torch torchvision torchaudio
```

**Features enabled:**
- AI-powered tradeline validation
- Named entity recognition for creditor names
- Text classification for account types
- Enhanced extraction accuracy

### Scikit-learn
**Used for:** TF-IDF similarity matching
**Size:** ~50MB
**Installation:**
```bash
pip install scikit-learn
```

**Features enabled:**
- Fuzzy matching for creditor names
- Similarity-based validation
- Text vectorization for comparison

## Status Without Optional Dependencies

✅ **Core functionality works:**
- PDF extraction with Document AI
- Basic tradeline parsing
- Credit report processing
- Database operations
- API endpoints

⚠️ **Limited functionality:**
- AI validation falls back to rule-based
- No NER for entity extraction
- No ML-based similarity matching

## Checking What's Installed

```bash
python -c "import transformers; print('✅ Transformers:', transformers.__version__)"
python -c "import torch; print('✅ PyTorch:', torch.__version__)"
python -c "import sklearn; print('✅ Scikit-learn:', sklearn.__version__)"
```

## Installation Options

### Option 1: Full Installation (Recommended for Production)
```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt  # Includes all dependencies
```

### Option 2: Minimal Installation (Faster, No AI)
```bash
cd backend
source ../venv/bin/activate
pip install fastapi uvicorn supabase google-cloud-documentai pydantic
```

### Option 3: Install AI Features Later
```bash
# Install core first
pip install -r requirements.txt --no-deps
# Then install AI features when needed
pip install transformers torch scikit-learn
```

## Code Changes Made

The following files now have optional imports:

1. **`services/advanced_parsing/ai_tradeline_validator.py`**
   - Gracefully handles missing `transformers`
   - Falls back to rule-based validation

2. **`services/advanced_parsing/multi_layer_extractor.py`**
   - Disables AI classifier if `transformers` unavailable
   - Uses alternative extraction methods

## Error Messages (Normal)

If optional dependencies are missing, you'll see warnings like:
```
⚠️  Transformers library not available. AI validation features will be limited.
⚠️  Scikit-learn not available. Some ML features will be limited.
```

These are informational only and don't prevent the system from working.

## Recommended Approach

For development:
- Start with minimal dependencies for speed
- Add AI features when testing advanced validation

For production:
- Install all dependencies for full feature set
- Monitor memory usage (PyTorch can be heavy)

## Memory Requirements

- **Minimal:** ~500MB RAM
- **With Transformers:** ~2-4GB RAM (depending on models loaded)
- **Full AI stack:** ~4-6GB RAM

## Disk Space

- **Minimal:** ~100MB
- **With dependencies:** ~6GB (mostly PyTorch and model weights)
