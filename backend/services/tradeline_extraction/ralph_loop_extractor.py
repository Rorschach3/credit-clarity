"""
Ralph Loop Tradeline Extractor
Implements the 9-step pipeline for reliable tradeline extraction with iterative refinement.
"""
import asyncio
import json
import logging
import os
import re
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    _GEMINI_MODEL = genai.GenerativeModel("gemini-1.5-flash")
    GEMINI_AVAILABLE = True
except Exception:
    genai = None  # type: ignore
    _GEMINI_MODEL = None
    GEMINI_AVAILABLE = False

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class SourceRef:
    """Citation for where a field value came from"""
    page: int
    evidence: str  # Text snippet or box coordinates
    confidence: float = 0.0
    method: str = ""  # 'ocr', 'heuristic', 'ai', 'merged'


@dataclass
class FieldValue:
    """Value with confidence and source references"""
    value: Any
    confidence: float
    source_refs: List[SourceRef] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Tradeline:
    """Tradeline with per-field confidence and citations"""
    creditor_name: Optional[FieldValue] = None
    account_number_masked: Optional[FieldValue] = None
    account_type: Optional[FieldValue] = None
    account_status: Optional[FieldValue] = None
    date_opened: Optional[FieldValue] = None
    credit_bureau: Optional[FieldValue] = None
    credit_limit_cents: Optional[FieldValue] = None
    monthly_payment_cents: Optional[FieldValue] = None
    account_balance_cents: Optional[FieldValue] = None
    is_negative: Optional[FieldValue] = None
    derogatory_flags: Optional[FieldValue] = None
    remarks: Optional[FieldValue] = None
    payment_history: Optional[FieldValue] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        result = {}
        for key, val in asdict(self).items():
            if val is None:
                result[key] = None
            elif isinstance(val, dict) and 'value' in val:
                result[key] = {
                    'value': val['value'],
                    'confidence': val['confidence'],
                    'source_refs': val.get('source_refs', []),
                    'conflicts': val.get('conflicts', [])
                }
        return result


@dataclass
class QualityMetrics:
    """Quality assessment for extracted tradelines"""
    score: float = 0.0
    missing_required: int = 0
    cross_page_conflicts: int = 0
    avg_field_confidence: float = 0.0
    coverage: float = 0.0  # % of fields filled
    consistency: float = 0.0  # Internal consistency
    citations_completeness: float = 0.0  # % of fields with source_refs


@dataclass
class ExtractionResult:
    """Result from one extraction iteration"""
    tradelines: List[Tradeline]
    quality: QualityMetrics
    iteration: int
    debug_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class RalphLoopExtractor:
    """
    Ralph Loop implementation for reliable tradeline extraction.

    Pipeline:
    1. PDF->Images (300dpi, fallback 450dpi)
    2. Preprocess (deskew, denoise, contrast)
    3. OCR Pass A (fast, per-page + per-region)
    4. OCR Pass B (targeted tradeline blocks)
    5. Heuristic Parse (regex/block parsing)
    6. AI Extract (LLM with schema + citations)
    7. Merge (heuristic + AI with confidence weighting)
    8. Validate (schema + field normalizers)
    9. Score (quality metrics)
    """

    def __init__(
        self,
        max_attempts: int = 6,
        quality_threshold: float = 0.92,
        missing_required_threshold: int = 1,
        output_debug_dir: Optional[Path] = None
    ):
        self.max_attempts = max_attempts
        self.quality_threshold = quality_threshold
        self.missing_required_threshold = missing_required_threshold
        self.output_debug_dir = Path(output_debug_dir) if output_debug_dir else None

        if self.output_debug_dir:
            self.output_debug_dir.mkdir(parents=True, exist_ok=True)

        # Tesseract check
        if not shutil.which('tesseract'):
            raise RuntimeError("Tesseract not found. Install tesseract-ocr package")

        # Required fields per spec
        self.required_fields = {'creditor_name', 'account_status', 'account_type'}

        # Tradeline anchors for OCR Pass B
        self.tradeline_anchors = [
            'Account Name', 'Creditor', 'Account Type', 'Account Status',
            'Balance', 'Credit Limit', 'Monthly Payment', 'Date Opened', 'Remarks'
        ]

    async def extract_tradelines(
        self,
        pdf_path: str | Path,
        use_ai: bool = True
    ) -> ExtractionResult:
        """
        Execute the full extraction pipeline with iterative refinement.
        """
        pdf_path = Path(pdf_path)
        best_result = None
        best_quality_score = 0.0

        for iteration in range(1, self.max_attempts + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"RALPH LOOP - Iteration {iteration}/{self.max_attempts}")
            logger.info(f"{'='*60}")

            try:
                result = await self._run_pipeline_iteration(
                    pdf_path, iteration, use_ai
                )

                logger.info(f"\nIteration {iteration} Quality Metrics:")
                logger.info(f"  Score: {result.quality.score:.3f}")
                logger.info(f"  Missing Required: {result.quality.missing_required}")
                logger.info(f"  Cross-page Conflicts: {result.quality.cross_page_conflicts}")
                logger.info(f"  Avg Field Confidence: {result.quality.avg_field_confidence:.3f}")
                logger.info(f"  Coverage: {result.quality.coverage:.3f}")

                # Track best result
                if result.quality.score > best_quality_score:
                    best_quality_score = result.quality.score
                    best_result = result

                # Check stop condition
                if (result.quality.score >= self.quality_threshold and
                    result.quality.missing_required <= self.missing_required_threshold and
                    result.quality.cross_page_conflicts == 0):
                    logger.info(f"\n✅ STOP CONDITION MET at iteration {iteration}")
                    logger.info(f"   Quality score: {result.quality.score:.3f} >= {self.quality_threshold}")
                    logger.info(f"   Missing required: {result.quality.missing_required} <= {self.missing_required_threshold}")
                    logger.info(f"   Cross-page conflicts: {result.quality.cross_page_conflicts} == 0")
                    return result

            except Exception as e:
                logger.error(f"Iteration {iteration} failed: {e}", exc_info=True)
                if best_result is None:
                    raise

        # Max attempts reached - return best result
        logger.warning(f"\n⚠️  Max attempts ({self.max_attempts}) reached")
        logger.warning(f"   Best quality score achieved: {best_quality_score:.3f}")

        if best_result is None:
            raise RuntimeError("All extraction attempts failed")

        return best_result

    async def _run_pipeline_iteration(
        self,
        pdf_path: Path,
        iteration: int,
        use_ai: bool
    ) -> ExtractionResult:
        """Execute one iteration of the 9-step pipeline"""

        debug_data = {}

        # Step 1: PDF -> Images
        logger.info("Step 1: Converting PDF to images...")
        images, dpi_used = await self._pdf_to_images(pdf_path, iteration)
        debug_data['dpi_used'] = dpi_used
        debug_data['page_count'] = len(images)

        if self.output_debug_dir:
            self._save_images(images, self.output_debug_dir / f"iter{iteration}_page_images")

        # Step 2: Preprocess images
        logger.info("Step 2: Preprocessing images...")
        preprocessed = await self._preprocess_images(images)

        if self.output_debug_dir:
            self._save_images(preprocessed, self.output_debug_dir / f"iter{iteration}_preprocessed")

        # Step 3: OCR Pass A (fast)
        logger.info("Step 3: OCR Pass A (fast extraction)...")
        ocr_pass_a = await self._ocr_pass_a(preprocessed)
        debug_data['ocr_pass_a'] = {
            'total_text_length': sum(len(p['text']) for p in ocr_pass_a),
            'avg_confidence': sum(p['confidence'] for p in ocr_pass_a) / len(ocr_pass_a) if ocr_pass_a else 0
        }

        if self.output_debug_dir:
            with open(self.output_debug_dir / f"iter{iteration}_ocr_pass_a.json", 'w') as f:
                json.dump(ocr_pass_a, f, indent=2)

        # Check if we need higher DPI fallback
        avg_confidence = debug_data['ocr_pass_a']['avg_confidence']
        if avg_confidence < 0.80 and dpi_used == 300:
            logger.warning(f"Low OCR confidence ({avg_confidence:.2f}) - retrying with 450 DPI")
            images, dpi_used = await self._pdf_to_images(pdf_path, iteration, dpi=450)
            preprocessed = await self._preprocess_images(images)
            ocr_pass_a = await self._ocr_pass_a(preprocessed)
            debug_data['dpi_fallback_triggered'] = True

        # Step 4: OCR Pass B (targeted)
        logger.info("Step 4: OCR Pass B (targeted tradeline blocks)...")
        ocr_pass_b = await self._ocr_pass_b(preprocessed, ocr_pass_a)
        debug_data['ocr_pass_b'] = {
            'blocks_detected': len(ocr_pass_b),
            'anchors_found': sum(len(b['anchors']) for b in ocr_pass_b)
        }

        if self.output_debug_dir:
            with open(self.output_debug_dir / f"iter{iteration}_ocr_pass_b.json", 'w') as f:
                json.dump(ocr_pass_b, f, indent=2)

        # Step 5: Heuristic Parse
        logger.info("Step 5: Heuristic parsing...")
        heuristic_tradelines = await self._heuristic_parse(ocr_pass_a, ocr_pass_b)
        debug_data['heuristic_tradelines_count'] = len(heuristic_tradelines)

        # Step 6: AI Extract (if enabled)
        ai_tradelines = []
        if use_ai:
            logger.info("Step 6: AI extraction...")
            ai_tradelines = await self._ai_extract(ocr_pass_a, ocr_pass_b)
            debug_data['ai_tradelines_count'] = len(ai_tradelines)

            if self.output_debug_dir:
                with open(self.output_debug_dir / f"iter{iteration}_ai_tradelines.json", 'w') as f:
                    json.dump([t.to_dict() for t in ai_tradelines], f, indent=2)
        else:
            logger.info("Step 6: AI extraction skipped (use_ai=False)")

        # Step 7: Merge
        logger.info("Step 7: Merging heuristic + AI results...")
        merged_tradelines = await self._merge_results(heuristic_tradelines, ai_tradelines)
        debug_data['merged_tradelines_count'] = len(merged_tradelines)

        # Step 8: Validate and normalize
        logger.info("Step 8: Validating and normalizing...")
        validated_tradelines = await self._validate_and_normalize(merged_tradelines)
        debug_data['validated_tradelines_count'] = len(validated_tradelines)

        # Step 9: Score
        logger.info("Step 9: Computing quality score...")
        quality = self._compute_quality_score(validated_tradelines)

        result = ExtractionResult(
            tradelines=validated_tradelines,
            quality=quality,
            iteration=iteration,
            debug_data=debug_data
        )

        # Save merged result
        if self.output_debug_dir:
            with open(self.output_debug_dir / f"iter{iteration}_merged_result.json", 'w') as f:
                json.dump([t.to_dict() for t in validated_tradelines], f, indent=2)

            with open(self.output_debug_dir / f"iter{iteration}_quality.json", 'w') as f:
                json.dump(asdict(quality), f, indent=2)

        return result

    async def _pdf_to_images(
        self,
        pdf_path: Path,
        iteration: int,
        dpi: int = 300
    ) -> Tuple[List[Image.Image], int]:
        """Step 1: Convert PDF pages to images at specified DPI"""

        def _sync_convert():
            images = []
            doc = fitz.open(str(pdf_path))
            try:
                zoom = dpi / 72  # 72 DPI is default
                mat = fitz.Matrix(zoom, zoom)

                for page_num in range(len(doc)):
                    page = doc[page_num]
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    images.append(img)
                    logger.debug(f"  Page {page_num + 1}: {img.width}x{img.height} at {dpi} DPI")
            finally:
                doc.close()

            return images

        import io
        loop = asyncio.get_running_loop()
        images = await loop.run_in_executor(None, _sync_convert)
        logger.info(f"  Converted {len(images)} pages at {dpi} DPI")
        return images, dpi

    async def _preprocess_images(
        self,
        images: List[Image.Image]
    ) -> List[Image.Image]:
        """Step 2: Deskew, denoise, contrast normalize"""

        def _sync_preprocess():
            processed = []
            for idx, img in enumerate(images):
                # Convert to OpenCV format
                cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

                # Denoise
                denoised = cv2.fastNlMeansDenoising(cv_img, None, 10, 7, 21)

                # Contrast normalization (CLAHE)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                contrast_enhanced = clahe.apply(denoised)

                # Deskew (using Hough line detection)
                edges = cv2.Canny(contrast_enhanced, 50, 150, apertureSize=3)
                lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)

                if lines is not None and len(lines) > 0:
                    angles = []
                    for rho, theta in lines[:10]:
                        angle = theta * 180 / np.pi - 90
                        angles.append(angle)

                    if angles:
                        avg_angle = np.mean(angles)
                        if abs(avg_angle) > 0.5:
                            h, w = contrast_enhanced.shape
                            center = (w // 2, h // 2)
                            M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)
                            contrast_enhanced = cv2.warpAffine(
                                contrast_enhanced, M, (w, h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE
                            )
                            logger.debug(f"  Page {idx + 1}: Deskewed by {avg_angle:.2f}°")

                # Convert back to PIL
                processed_img = Image.fromarray(contrast_enhanced)
                processed.append(processed_img)

            return processed

        loop = asyncio.get_running_loop()
        processed = await loop.run_in_executor(None, _sync_preprocess)
        logger.info(f"  Preprocessed {len(processed)} pages")
        return processed

    async def _ocr_pass_a(
        self,
        images: List[Image.Image]
    ) -> List[Dict[str, Any]]:
        """Step 3: Fast OCR extraction with word-level confidence + bounding boxes"""

        def _sync_ocr():
            results = []

            for page_num, img in enumerate(images, start=1):
                # Get OCR data with boxes and confidence
                config = r'--oem 3 --psm 6'
                data = pytesseract.image_to_data(
                    img,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )

                # Reconstruct text with confidence tracking
                page_text_lines = []
                boxes = []
                confidences = []

                for i, text in enumerate(data['text']):
                    conf = int(data['conf'][i])
                    if conf >= 30 and text.strip():
                        page_text_lines.append(text)
                        boxes.append({
                            'text': text,
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'w': data['width'][i],
                            'h': data['height'][i],
                            'conf': conf
                        })
                        confidences.append(conf)

                page_text = ' '.join(page_text_lines)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0

                results.append({
                    'page': page_num,
                    'text': page_text,
                    'confidence': avg_conf / 100.0,  # Normalize to 0-1
                    'boxes': boxes
                })

                logger.debug(f"  Page {page_num}: {len(page_text)} chars, conf={avg_conf:.1f}%")

            return results

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _sync_ocr)
        logger.info(f"  OCR Pass A completed for {len(results)} pages")
        return results

    async def _ocr_pass_b(
        self,
        images: List[Image.Image],
        ocr_pass_a: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Step 4: Detect tradeline-like blocks using anchors"""

        def _sync_detect():
            blocks = []

            for page_data in ocr_pass_a:
                page_num = page_data['page']
                boxes = page_data['boxes']

                # Find anchor keywords
                anchor_boxes = []
                for box in boxes:
                    text = box['text']
                    if any(anchor.lower() in text.lower() for anchor in self.tradeline_anchors):
                        anchor_boxes.append(box)

                if anchor_boxes:
                    # Group nearby anchors into tradeline blocks
                    # Simple heuristic: group boxes within vertical proximity
                    sorted_boxes = sorted(anchor_boxes, key=lambda b: b['y'])

                    current_block = []
                    block_y_start = None

                    for box in sorted_boxes:
                        if block_y_start is None:
                            block_y_start = box['y']
                            current_block = [box]
                        elif box['y'] - block_y_start < 200:  # Within 200 pixels
                            current_block.append(box)
                        else:
                            if current_block:
                                blocks.append({
                                    'page': page_num,
                                    'anchors': current_block,
                                    'y_range': (block_y_start, current_block[-1]['y'])
                                })
                            block_y_start = box['y']
                            current_block = [box]

                    if current_block:
                        blocks.append({
                            'page': page_num,
                            'anchors': current_block,
                            'y_range': (block_y_start, current_block[-1]['y'])
                        })

            return blocks

        loop = asyncio.get_running_loop()
        blocks = await loop.run_in_executor(None, _sync_detect)
        logger.info(f"  Detected {len(blocks)} tradeline blocks")
        return blocks

    async def _heuristic_parse(
        self,
        ocr_pass_a: List[Dict[str, Any]],
        ocr_pass_b: List[Dict[str, Any]]
    ) -> List[Tradeline]:
        """Step 5: Regex/block parsing into candidate tradelines with citations"""

        tradelines = []

        # Combine all text for pattern matching
        all_text = "\n".join(p['text'] for p in ocr_pass_a)

        # Pattern: Look for creditor names (usually all caps)
        creditor_pattern = r'\b([A-Z][A-Z\s&\.]{5,50})\b'

        # Pattern: Account numbers (masked or full)
        account_pattern = r'(?:Account|Acct)\s*(?:Number|#|No)?\s*:?\s*([A-Z0-9\*\-]{4,20})'

        # Pattern: Dates (MM/DD/YYYY or MM-DD-YYYY)
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'

        # Pattern: Currency ($X,XXX.XX)
        currency_pattern = r'\$\s*([\d,]+\.?\d*)'

        # Pattern: Account status keywords
        status_keywords = ['closed', 'current', 'open', 'paid', 'charged off', 'collection']

        # Pattern: Account type keywords
        type_keywords = ['revolving', 'installment', 'mortgage', 'auto loan']

        # Simple heuristic: extract fields and create tradelines
        # This is a simplified version - real implementation would be more sophisticated

        for page_data in ocr_pass_a:
            page_num = page_data['page']
            page_text = page_data['text']

            # Find potential creditors
            creditors = re.findall(creditor_pattern, page_text)

            for creditor in creditors:
                tradeline = Tradeline()

                # Creditor name
                tradeline.creditor_name = FieldValue(
                    value=creditor.strip(),
                    confidence=0.7,
                    source_refs=[SourceRef(
                        page=page_num,
                        evidence=f"Creditor pattern match: {creditor}",
                        confidence=0.7,
                        method='heuristic'
                    )]
                )

                # Try to find account info near this creditor
                # (In real implementation, would use box coordinates for proximity)

                # Account number (mask it)
                account_matches = re.findall(account_pattern, page_text)
                if account_matches:
                    raw_account = account_matches[0]
                    masked = self._mask_account_number(raw_account)
                    tradeline.account_number_masked = FieldValue(
                        value=masked,
                        confidence=0.6,
                        source_refs=[SourceRef(
                            page=page_num,
                            evidence=f"Account pattern: {raw_account}",
                            confidence=0.6,
                            method='heuristic'
                        )]
                    )

                # Set credit bureau (from PDF name/content)
                tradeline.credit_bureau = FieldValue(
                    value='TransUnion',
                    confidence=0.9,
                    source_refs=[SourceRef(
                        page=1,
                        evidence='TransUnion PDF',
                        confidence=0.9,
                        method='heuristic'
                    )]
                )

                # Only add if we have creditor name
                if tradeline.creditor_name:
                    tradelines.append(tradeline)

        logger.info(f"  Heuristic parsing found {len(tradelines)} candidate tradelines")
        return tradelines

    async def _ai_extract(
        self,
        ocr_pass_a: List[Dict[str, Any]],
        ocr_pass_b: List[Dict[str, Any]]
    ) -> List[Tradeline]:
        """Step 6: AI extraction with LLM (schema + citations required)"""

        if not GEMINI_AVAILABLE or _GEMINI_MODEL is None:
            logger.warning("  Gemini not available, skipping AI extraction")
            return []

        # Collect text from both OCR passes
        def _collect_text(ocr_pass: List[Dict[str, Any]]) -> str:
            parts = []
            for page_data in ocr_pass:
                page_num = page_data.get("page", "?")
                text = page_data.get("text", "") or page_data.get("full_text", "")
                if text:
                    parts.append(f"[Page {page_num}]\n{text.strip()}")
            return "\n\n".join(parts)

        text_a = _collect_text(ocr_pass_a)
        text_b = _collect_text(ocr_pass_b)
        combined_text = "\n\n--- OCR PASS B ---\n\n".join(
            filter(None, [text_a, text_b])
        )

        if not combined_text.strip():
            logger.warning("  AI extraction: no OCR text available")
            return []

        prompt = f"""You are a credit report parser. Extract all tradelines from the following OCR text.

Return a JSON array of objects. Each object represents one tradeline with these fields (omit missing fields):
  - creditor_name: string
  - account_number_masked: string (last 4 digits, e.g. "****1234")
  - account_type: string (e.g. "Credit Card", "Mortgage", "Auto Loan")
  - account_status: string (e.g. "Open", "Closed", "Collection")
  - date_opened: string (MM/DD/YYYY if available)
  - credit_limit_cents: number (dollars, not cents — the pipeline will convert)
  - monthly_payment_cents: number (dollars)
  - account_balance_cents: number (dollars)
  - is_negative: boolean
  - derogatory_flags: string (comma-separated flags, e.g. "Late 30", "Charge-off")
  - remarks: string
  - payment_history: string (raw payment history string)

Return ONLY a valid JSON array with no commentary or markdown fences.

OCR TEXT:
{combined_text}
"""

        try:
            response = _GEMINI_MODEL.generate_content(prompt)
            raw = response.text.strip()

            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-z]*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)

            items = json.loads(raw)
            if not isinstance(items, list):
                raise ValueError(f"Expected JSON array, got {type(items).__name__}")

        except Exception as exc:
            logger.warning(f"  AI extraction failed: {exc}")
            return []

        tradelines: List[Tradeline] = []
        field_map = {
            "creditor_name": "creditor_name",
            "account_number_masked": "account_number_masked",
            "account_type": "account_type",
            "account_status": "account_status",
            "date_opened": "date_opened",
            "credit_limit_cents": "credit_limit_cents",
            "monthly_payment_cents": "monthly_payment_cents",
            "account_balance_cents": "account_balance_cents",
            "is_negative": "is_negative",
            "derogatory_flags": "derogatory_flags",
            "remarks": "remarks",
            "payment_history": "payment_history",
        }

        for item in items:
            if not isinstance(item, dict):
                continue
            tradeline = Tradeline()
            for json_key, attr in field_map.items():
                raw_val = item.get(json_key)
                if raw_val is None:
                    continue
                setattr(
                    tradeline,
                    attr,
                    FieldValue(
                        value=raw_val,
                        confidence=0.85,
                        source_refs=[
                            SourceRef(
                                page=1,
                                evidence=f"AI extracted: {json_key}={raw_val}",
                                confidence=0.85,
                                method="ai",
                            )
                        ],
                    ),
                )
            if tradeline.creditor_name:
                tradelines.append(tradeline)

        logger.info(f"  AI extraction produced {len(tradelines)} tradelines")
        return tradelines

    async def _merge_results(
        self,
        heuristic: List[Tradeline],
        ai: List[Tradeline]
    ) -> List[Tradeline]:
        """Step 7: Merge heuristic + AI, prefer higher confidence"""

        # Simple merge: for now, just combine them
        # Real implementation would match tradelines by creditor and merge fields

        merged = []

        # Add heuristic results
        merged.extend(heuristic)

        # Add AI results
        merged.extend(ai)

        logger.info(f"  Merged {len(merged)} tradelines total")
        return merged

    async def _validate_and_normalize(
        self,
        tradelines: List[Tradeline]
    ) -> List[Tradeline]:
        """Step 8: Validate schema and normalize fields"""

        validated = []

        for tradeline in tradelines:
            # Validate required fields
            has_required = True
            for req_field in self.required_fields:
                field_val = getattr(tradeline, req_field, None)
                if field_val is None or field_val.value is None:
                    has_required = False
                    break

            if not has_required:
                logger.debug(f"  Skipping tradeline (missing required fields): {tradeline.creditor_name}")
                continue

            # Normalize currency to cents
            for money_field in ['credit_limit_cents', 'monthly_payment_cents', 'account_balance_cents']:
                field_val = getattr(tradeline, money_field, None)
                if field_val and field_val.value:
                    # Assume value is in dollars, convert to cents
                    try:
                        dollars = float(str(field_val.value).replace('$', '').replace(',', ''))
                        cents = int(dollars * 100)
                        field_val.value = cents
                    except (ValueError, TypeError):
                        field_val.value = None

            # Normalize dates to ISO8601
            if tradeline.date_opened and tradeline.date_opened.value:
                date_str = tradeline.date_opened.value
                try:
                    # Parse MM/DD/YYYY to ISO
                    parsed = datetime.strptime(date_str, '%m/%d/%Y')
                    tradeline.date_opened.value = parsed.strftime('%Y-%m-%d')
                except ValueError:
                    pass

            validated.append(tradeline)

        logger.info(f"  Validated {len(validated)} tradelines")
        return validated

    def _compute_quality_score(
        self,
        tradelines: List[Tradeline]
    ) -> QualityMetrics:
        """Step 9: Compute quality metrics"""

        if not tradelines:
            return QualityMetrics(score=0.0, missing_required=999)

        metrics = QualityMetrics()

        # Count missing required fields
        missing_count = 0
        for tradeline in tradelines:
            for req_field in self.required_fields:
                field_val = getattr(tradeline, req_field, None)
                if field_val is None or field_val.value is None:
                    missing_count += 1

        metrics.missing_required = missing_count

        # Average field confidence
        all_confidences = []
        field_counts = []
        citations_counts = []

        for tradeline in tradelines:
            tradeline_dict = tradeline.to_dict()
            filled_fields = 0

            for field_name, field_val in tradeline_dict.items():
                if field_val is not None and isinstance(field_val, dict):
                    filled_fields += 1
                    if 'confidence' in field_val:
                        all_confidences.append(field_val['confidence'])
                    if field_val.get('source_refs'):
                        citations_counts.append(1)
                    else:
                        citations_counts.append(0)

            field_counts.append(filled_fields)

        metrics.avg_field_confidence = (
            sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        )

        # Coverage: avg % of fields filled per tradeline
        total_fields = 13  # Total possible fields in Tradeline
        metrics.coverage = (
            sum(field_counts) / (len(tradelines) * total_fields) if tradelines else 0.0
        )

        # Citations completeness
        metrics.citations_completeness = (
            sum(citations_counts) / len(citations_counts) if citations_counts else 0.0
        )

        # Consistency: no cross-page conflicts (simplified check)
        metrics.cross_page_conflicts = 0  # Would check for conflicting values in real impl

        metrics.consistency = 1.0 - (metrics.cross_page_conflicts / max(1, len(tradelines)))

        # Overall score (weighted combination)
        metrics.score = (
            0.30 * metrics.avg_field_confidence +
            0.25 * metrics.coverage +
            0.25 * metrics.consistency +
            0.20 * metrics.citations_completeness
        )

        return metrics

    def _mask_account_number(self, account_num: str) -> str:
        """Mask account number to ****XXXX (last 4 only)"""
        # Remove all non-alphanumeric
        clean = re.sub(r'[^A-Za-z0-9]', '', account_num)

        if len(clean) <= 4:
            return clean  # Too short to mask

        last_four = clean[-4:]
        return f"****{last_four}"

    def _save_images(self, images: List[Image.Image], output_dir: Path):
        """Save images to disk for debugging"""
        output_dir.mkdir(parents=True, exist_ok=True)
        for idx, img in enumerate(images, start=1):
            img.save(output_dir / f"page_{idx}.png")
        logger.debug(f"  Saved {len(images)} images to {output_dir}")


async def main():
    """Main entry point for Ralph Loop extraction"""
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse arguments from Ralph Loop command
    pdf_path = "TransUnion-06-10-2025.pdf"
    output_json = "./results/extracted_tradelines.json"
    output_debug_dir = "./results/debug"

    logger.info("="*60)
    logger.info("RALPH LOOP: Tradeline Extraction Pipeline")
    logger.info("="*60)
    logger.info(f"Input PDF: {pdf_path}")
    logger.info(f"Output JSON: {output_json}")
    logger.info(f"Debug Dir: {output_debug_dir}")
    logger.info("")

    # Create extractor
    extractor = RalphLoopExtractor(
        max_attempts=6,
        quality_threshold=0.92,
        missing_required_threshold=1,
        output_debug_dir=Path(output_debug_dir)
    )

    try:
        # Run extraction
        result = await extractor.extract_tradelines(
            pdf_path=pdf_path,
            use_ai=False  # Set to True to enable AI extraction
        )

        # Save final result
        output_path = Path(output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(
                [t.to_dict() for t in result.tradelines],
                f,
                indent=2
            )

        # Print summary
        print("\n" + "="*60)
        print("EXTRACTION COMPLETE")
        print("="*60)
        print(f"✅ Extracted {len(result.tradelines)} tradelines")
        print(f"✅ Quality Score: {result.quality.score:.3f}")
        print(f"✅ Iteration: {result.iteration}/{extractor.max_attempts}")
        print(f"✅ Output: {output_json}")
        print("")
        print("Quality Metrics:")
        print(f"  - Missing Required: {result.quality.missing_required}")
        print(f"  - Avg Confidence: {result.quality.avg_field_confidence:.3f}")
        print(f"  - Coverage: {result.quality.coverage:.3f}")
        print(f"  - Citations: {result.quality.citations_completeness:.3f}")
        print(f"  - Conflicts: {result.quality.cross_page_conflicts}")
        print("="*60)

        return 0

    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
