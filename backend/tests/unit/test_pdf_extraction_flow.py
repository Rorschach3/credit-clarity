"""
Tests verifying the PDF tradeline extraction flow matches the diagram:

  User uploads PDF
      → Frontend sends PDF to API
      → Backend extracts text
      → Backend parses text into tradelines (returned to frontend, NOT saved)
      → Frontend displays/edits tradelines
      → Frontend calls saveTradelines → Supabase upserts → UI confirms

The backend endpoint must return tradelines WITHOUT inserting to the database.
The frontend is solely responsible for persisting tradelines via saveTradelines.
"""
import io
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Ensure backend is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_pdf() -> bytes:
    """Return a minimal valid PDF byte string for upload tests."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n9\n%%EOF"
    )


MOCK_TRADELINES = [
    {
        "creditor_name": "CAPITAL ONE",
        "account_number": "4111XXXX1234",
        "account_balance": "$1,200",
        "account_status": "Open",
        "account_type": "Credit Card",
        "credit_bureau": "TransUnion",
        "is_negative": False,
    }
]

MOCK_PROCESSOR_RESULT = {
    "success": True,
    "tradelines": MOCK_TRADELINES,
    "method_used": "gemini_ai",
    "cost_estimate": 0.001,
    "processing_time": 1.5,
    "stats": {"pages": 1},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPDFExtractionFlow:
    """Verify the extraction flow: backend extracts+parses, frontend saves."""

    def test_endpoint_returns_tradelines_without_db_insert(self, client: TestClient, auth_headers):
        """
        Step 3→4 in diagram: backend extracts text and returns parsed
        tradelines to the frontend. The Supabase insert must NOT be called.
        """
        pdf_bytes = _make_minimal_pdf()

        mock_processor = MagicMock()
        mock_processor.process_credit_report_optimal = AsyncMock(
            return_value=MOCK_PROCESSOR_RESULT
        )

        with (
            patch("main.LegacyCreditReportProcessor", return_value=mock_processor),
            patch("main.supabase") as mock_supabase,
        ):
            # Verify: supabase.table().insert() must NOT be called
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table

            response = client.post(
                "/api/process-credit-report",
                files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"use_background": "false"},
                headers={"Authorization": auth_headers["Authorization"]},
            )

        assert response.status_code == 200
        data = response.json()

        # Response must be successful and contain tradelines
        assert data["success"] is True
        assert data["tradelines_found"] == len(MOCK_TRADELINES)
        assert len(data["tradelines"]) == len(MOCK_TRADELINES)
        assert data["tradelines"][0]["creditor_name"] == "CAPITAL ONE"

        # CRITICAL: Supabase insert must NOT have been called.
        # The frontend is responsible for saving (saveTradelines → upsert).
        mock_supabase.table.assert_not_called(), (
            "Backend must NOT insert tradelines to the database. "
            "Only the frontend saveTradelines call should persist data."
        )

    def test_endpoint_returns_all_required_fields(self, client: TestClient, auth_headers):
        """Response shape must give the frontend enough data to display and save."""
        pdf_bytes = _make_minimal_pdf()

        mock_processor = MagicMock()
        mock_processor.process_credit_report_optimal = AsyncMock(
            return_value=MOCK_PROCESSOR_RESULT
        )

        with (
            patch("main.LegacyCreditReportProcessor", return_value=mock_processor),
            patch("main.supabase"),
        ):
            response = client.post(
                "/api/process-credit-report",
                files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"use_background": "false"},
                headers={"Authorization": auth_headers["Authorization"]},
            )

        assert response.status_code == 200
        data = response.json()

        required_keys = {"success", "tradelines", "tradelines_found", "processing_method"}
        assert required_keys.issubset(data.keys()), (
            f"Response missing keys: {required_keys - set(data.keys())}"
        )

    def test_background_job_path_does_not_return_tradelines_directly(
        self, client: TestClient, auth_headers
    ):
        """
        For background jobs the endpoint returns a job_id instead of tradelines.
        The actual save happens inside the background worker after processing.
        This is an accepted variation of the diagram for async large files.
        """
        pdf_bytes = _make_minimal_pdf()

        fake_job_id = "job-abc-123"

        with patch("services.background_jobs.submit_pdf_processing_job", new=AsyncMock(return_value=fake_job_id)):
            response = client.post(
                "/api/process-credit-report",
                files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
                data={"use_background": "true"},
                headers={"Authorization": auth_headers["Authorization"]},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["job_id"] == fake_job_id
        assert data["status"] == "queued"
        # No tradelines in response — frontend polls and saves after job completes
        assert "tradelines" not in data or data.get("tradelines") is None

    def test_invalid_file_type_rejected(self, client: TestClient, auth_headers):
        """Non-PDF files must be rejected before any processing."""
        response = client.post(
            "/api/process-credit-report",
            files={"file": ("report.txt", io.BytesIO(b"not a pdf"), "text/plain")},
            data={"use_background": "false"},
            headers={"Authorization": auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "PDF" in data.get("error", "")

    def test_tiny_file_rejected(self, client: TestClient, auth_headers):
        """Files below minimum size must be rejected."""
        response = client.post(
            "/api/process-credit-report",
            files={"file": ("report.pdf", io.BytesIO(b"%PDF-tiny"), "application/pdf")},
            data={"use_background": "false"},
            headers={"Authorization": auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
