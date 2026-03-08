# Service Integration Architecture

**Parent Document**: @analysis.md
**Framework Reference**: @../guidance-specification.md (Section 4: System Architect Decisions - Mailing Service Integration)

---

## Overview

This section details the architecture for integrating external services including mailing providers (Lob.com, USPS), payment processing, and third-party APIs across Phases 1-4.

---

## Mailing Service Integration

### Phase 1: Lob.com API Integration

**Strategic Rationale** (from guidance-specification.md):
- ✅ Fast time-to-market: Well-documented REST API, official Python SDK
- ✅ Certified mail support: Built-in tracking, delivery confirmation
- ✅ Professional output: High-quality letterhead, formatting
- ❌ Higher cost: ~$1.50-2.00 per letter (vs. $0.50-0.75 USPS Direct)
- **Decision**: Prioritize speed to market for viral GTM strategy, optimize costs in Phase 2

### Integration Architecture

**Service Abstraction Layer**:
```python
# backend/services/mailing_service_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class MailingAddress:
    name: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    zip_code: str

@dataclass
class MailingResult:
    tracking_number: str
    estimated_delivery_date: datetime
    service_provider: str
    cost_cents: int
    status: str

class MailingServiceInterface(ABC):
    """Abstract interface for mailing service providers."""

    @abstractmethod
    async def send_letter(
        self,
        to_address: MailingAddress,
        from_address: MailingAddress,
        letter_content: str,
        mail_type: str = "certified"
    ) -> MailingResult:
        """Send a letter via the mailing service."""
        pass

    @abstractmethod
    async def get_tracking_status(
        self,
        tracking_number: str
    ) -> Dict[str, Any]:
        """Get current tracking status."""
        pass

    @abstractmethod
    async def validate_address(
        self,
        address: MailingAddress
    ) -> Dict[str, Any]:
        """Validate address before sending."""
        pass
```

**Lob.com Implementation**:
```python
# backend/services/lob_mailing_service.py
import lob
from core.config import get_settings

settings = get_settings()

class LobMailingService(MailingServiceInterface):
    """Lob.com mailing service implementation."""

    def __init__(self):
        self.client = lob.Client(api_key=settings.lob_api_key)
        self.from_address = self._get_default_from_address()

    async def send_letter(
        self,
        to_address: MailingAddress,
        from_address: MailingAddress,
        letter_content: str,
        mail_type: str = "certified"
    ) -> MailingResult:
        """Send certified mail letter via Lob.com."""

        # Step 1: Generate PDF from letter content
        pdf_bytes = await self._generate_letter_pdf(letter_content)

        # Step 2: Create Lob letter
        try:
            lob_response = self.client.letters.create(
                description=f"Credit dispute letter - {datetime.utcnow().isoformat()}",
                to_address={
                    "name": to_address.name,
                    "address_line1": to_address.address_line1,
                    "address_line2": to_address.address_line2,
                    "address_city": to_address.city,
                    "address_state": to_address.state,
                    "address_zip": to_address.zip_code,
                    "address_country": "US"
                },
                from_address={
                    "name": from_address.name,
                    "address_line1": from_address.address_line1,
                    "address_city": from_address.city,
                    "address_state": from_address.state,
                    "address_zip": from_address.zip_code,
                    "address_country": "US"
                },
                file=pdf_bytes,
                color=False,  # Black & white (cheaper)
                mail_type="usps_first_class",
                extra_service="certified",  # Certified mail
                return_envelope=True  # Include return envelope
            )

            # Step 3: Extract tracking information
            tracking_number = lob_response.tracking_number
            estimated_delivery = lob_response.expected_delivery_date

            return MailingResult(
                tracking_number=tracking_number,
                estimated_delivery_date=estimated_delivery,
                service_provider="Lob",
                cost_cents=self._calculate_lob_cost(lob_response),
                status="Sent"
            )

        except lob.error.InvalidRequestError as e:
            logger.error(f"Lob API error: {e}")
            raise MailingServiceError(f"Invalid request: {e}")

        except lob.error.RateLimitError as e:
            logger.warning(f"Lob rate limit exceeded: {e}")
            # Queue for retry
            await self._queue_for_retry(to_address, letter_content)
            raise MailingServiceError("Service temporarily unavailable, letter queued")

    async def get_tracking_status(self, tracking_number: str) -> Dict[str, Any]:
        """Get USPS tracking status via Lob."""

        try:
            # Lob provides USPS tracking events
            letter = self.client.letters.retrieve(tracking_number)

            return {
                "tracking_number": tracking_number,
                "status": letter.tracking_events[-1].name if letter.tracking_events else "Unknown",
                "location": letter.tracking_events[-1].location if letter.tracking_events else None,
                "timestamp": letter.tracking_events[-1].time if letter.tracking_events else None,
                "carrier": "USPS",
                "events": [
                    {
                        "name": event.name,
                        "location": event.location,
                        "timestamp": event.time
                    }
                    for event in letter.tracking_events
                ]
            }

        except lob.error.InvalidRequestError:
            raise MailingServiceError("Invalid tracking number")

    async def validate_address(self, address: MailingAddress) -> Dict[str, Any]:
        """Validate and standardize address using Lob's US Verification."""

        try:
            verification = self.client.us_verifications.verify(
                primary_line=address.address_line1,
                secondary_line=address.address_line2,
                city=address.city,
                state=address.state,
                zip_code=address.zip_code
            )

            return {
                "is_valid": verification.deliverability == "deliverable",
                "standardized_address": {
                    "address_line1": verification.primary_line,
                    "address_line2": verification.secondary_line,
                    "city": verification.components.city,
                    "state": verification.components.state,
                    "zip_code": verification.components.zip_code
                },
                "deliverability": verification.deliverability,
                "components": verification.components
            }

        except lob.error.InvalidRequestError as e:
            return {
                "is_valid": False,
                "error": str(e)
            }

    def _calculate_lob_cost(self, lob_response) -> int:
        """Calculate actual cost from Lob response."""
        # Lob certified mail: ~$1.75 per letter
        # Return envelope: ~$0.25
        # Total: ~$2.00
        return 200  # cents

    async def _generate_letter_pdf(self, letter_content: str) -> bytes:
        """Generate PDF from letter content with professional formatting."""
        # Use ReportLab or similar library
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter as letter_size

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter_size)

        # Add letterhead, formatting, content
        # ... (implementation details)

        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    def _get_default_from_address(self) -> MailingAddress:
        """Get default sender address from configuration."""
        return MailingAddress(
            name="Credit Clarity",
            address_line1=settings.company_address_line1,
            address_line2=settings.company_address_line2,
            city=settings.company_city,
            state=settings.company_state,
            zip_code=settings.company_zip
        )
```

**Configuration**:
```python
# core/config.py additions
class Settings(BaseSettings):
    # Lob.com settings
    lob_api_key: Optional[str] = Field(default=None, env="LOB_API_KEY")

    # Company address (sender)
    company_address_line1: str = Field(default="123 Main St", env="COMPANY_ADDRESS_LINE1")
    company_address_line2: Optional[str] = Field(default=None, env="COMPANY_ADDRESS_LINE2")
    company_city: str = Field(default="San Francisco", env="COMPANY_CITY")
    company_state: str = Field(default="CA", env="COMPANY_STATE")
    company_zip: str = Field(default="94105", env="COMPANY_ZIP")
```

**Error Handling & Retries**:
```python
# backend/services/mailing_retry_service.py
class MailingRetryService:
    """Handle failed mailing attempts with exponential backoff."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_retries = 3
        self.retry_delays = [300, 900, 3600]  # 5min, 15min, 1hr

    async def queue_for_retry(
        self,
        to_address: MailingAddress,
        letter_content: str,
        attempt: int = 0
    ):
        """Queue failed mailing for retry."""

        retry_data = {
            "to_address": asdict(to_address),
            "letter_content": letter_content,
            "attempt": attempt,
            "queued_at": datetime.utcnow().isoformat()
        }

        # Store in Redis with delay
        delay_seconds = self.retry_delays[attempt] if attempt < len(self.retry_delays) else 3600

        await self.redis.zadd(
            "mailing_retry_queue",
            {json.dumps(retry_data): time.time() + delay_seconds}
        )

    async def process_retry_queue(self):
        """Background job to process retry queue."""

        while True:
            # Get items ready for retry
            current_time = time.time()
            items = await self.redis.zrangebyscore(
                "mailing_retry_queue",
                0,
                current_time,
                start=0,
                num=10
            )

            for item_json in items:
                retry_data = json.loads(item_json)
                attempt = retry_data['attempt']

                if attempt >= self.max_retries:
                    # Max retries exceeded, notify user
                    await self._notify_user_failure(retry_data)
                    await self.redis.zrem("mailing_retry_queue", item_json)
                    continue

                try:
                    # Retry sending
                    mailing_service = get_mailing_service()
                    result = await mailing_service.send_letter(
                        to_address=MailingAddress(**retry_data['to_address']),
                        letter_content=retry_data['letter_content']
                    )

                    # Success - remove from queue
                    await self.redis.zrem("mailing_retry_queue", item_json)
                    logger.info(f"Retry successful: {result.tracking_number}")

                except Exception as e:
                    # Retry failed, re-queue with incremented attempt
                    logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                    await self.redis.zrem("mailing_retry_queue", item_json)
                    await self.queue_for_retry(
                        to_address=MailingAddress(**retry_data['to_address']),
                        letter_content=retry_data['letter_content'],
                        attempt=attempt + 1
                    )

            # Sleep before next check
            await asyncio.sleep(60)  # Check every minute
```

---

## Phase 2: USPS API Direct Integration

### Migration Strategy

**Phased Rollout with A/B Testing**:

```
Month 7: Implement USPS integration in parallel
    ├── USPS API client development
    ├── Certified mail workflow setup
    └── Address standardization (CASS certification)

Month 8: A/B test 10% of letters via USPS
    ├── Route selection logic (user segmentation)
    ├── Success metrics tracking (delivery rate, cost, latency)
    └── User experience comparison

Month 9: Increase to 50% USPS if success metrics met
    ├── Success criteria: 95%+ delivery rate, <5% errors, cost savings validated
    └── Monitor user feedback, tracking accuracy

Month 10: Full migration to USPS for new letters
    ├── Deprecate Lob for new mailings
    ├── Keep Lob fallback for critical failures
    └── Sunset plan: Phase out Lob by Month 12
```

**USPS API Implementation**:
```python
# backend/services/usps_mailing_service.py
import requests
from xml.etree import ElementTree as ET

class USPSMailingService(MailingServiceInterface):
    """USPS Web Tools API implementation."""

    def __init__(self):
        self.api_url = "https://secure.shippingapis.com/ShippingAPI.dll"
        self.user_id = settings.usps_user_id
        self.certified_mail_fee = 375  # $3.75 (as of 2024)
        self.first_class_fee = 66     # $0.66 (as of 2024)

    async def send_letter(
        self,
        to_address: MailingAddress,
        from_address: MailingAddress,
        letter_content: str,
        mail_type: str = "certified"
    ) -> MailingResult:
        """Send certified mail via USPS API."""

        # Step 1: Validate address
        validated_address = await self.validate_address(to_address)
        if not validated_address['is_valid']:
            raise MailingServiceError("Invalid recipient address")

        # Step 2: Generate PDF with USPS-compliant formatting
        pdf_bytes = await self._generate_usps_letter_pdf(
            letter_content,
            to_address=validated_address['standardized_address'],
            from_address=from_address
        )

        # Step 3: Print and mail via local USPS integration
        # (USPS API doesn't support direct mailing - requires USPS Business Customer Gateway)
        # Alternative: Use local printing + USPS pickup scheduling

        # For MVP: Partner with printing service (e.g., Click2Mail, PostGrid)
        # Long-term: Direct USPS Business Customer Gateway integration

        tracking_number = await self._submit_to_usps_gateway(
            pdf_bytes,
            to_address=validated_address['standardized_address'],
            from_address=from_address,
            mail_type=mail_type
        )

        return MailingResult(
            tracking_number=tracking_number,
            estimated_delivery_date=self._calculate_delivery_date(),
            service_provider="USPS",
            cost_cents=self.certified_mail_fee + self.first_class_fee,  # $4.41
            status="Sent"
        )

    async def get_tracking_status(self, tracking_number: str) -> Dict[str, Any]:
        """Get USPS tracking status."""

        # USPS Track & Confirm API
        xml_request = f"""
        <TrackRequest USERID="{self.user_id}">
            <TrackID ID="{tracking_number}" />
        </TrackRequest>
        """

        response = requests.get(
            self.api_url,
            params={
                "API": "TrackV2",
                "XML": xml_request
            }
        )

        # Parse XML response
        root = ET.fromstring(response.text)
        track_info = root.find("TrackInfo")

        if track_info is None:
            raise MailingServiceError("Invalid tracking number")

        return {
            "tracking_number": tracking_number,
            "status": track_info.findtext("Status"),
            "status_summary": track_info.findtext("StatusSummary"),
            "location": track_info.findtext("StatusCity") + ", " + track_info.findtext("StatusState"),
            "timestamp": track_info.findtext("StatusDate") + " " + track_info.findtext("StatusTime"),
            "carrier": "USPS",
            "events": self._parse_tracking_events(track_info)
        }

    async def validate_address(self, address: MailingAddress) -> Dict[str, Any]:
        """Validate address using USPS Address Validation API."""

        xml_request = f"""
        <AddressValidateRequest USERID="{self.user_id}">
            <Address>
                <Address1>{address.address_line2 or ''}</Address1>
                <Address2>{address.address_line1}</Address2>
                <City>{address.city}</City>
                <State>{address.state}</State>
                <Zip5>{address.zip_code[:5]}</Zip5>
                <Zip4>{address.zip_code[6:] if len(address.zip_code) > 5 else ''}</Zip4>
            </Address>
        </AddressValidateRequest>
        """

        response = requests.get(
            self.api_url,
            params={
                "API": "Verify",
                "XML": xml_request
            }
        )

        root = ET.fromstring(response.text)
        address_elem = root.find("Address")

        if address_elem.find("Error") is not None:
            return {"is_valid": False, "error": address_elem.findtext("Error/Description")}

        return {
            "is_valid": True,
            "standardized_address": {
                "address_line1": address_elem.findtext("Address2"),
                "address_line2": address_elem.findtext("Address1"),
                "city": address_elem.findtext("City"),
                "state": address_elem.findtext("State"),
                "zip_code": address_elem.findtext("Zip5") + "-" + address_elem.findtext("Zip4")
            }
        }

    async def _submit_to_usps_gateway(
        self,
        pdf_bytes: bytes,
        to_address: Dict[str, str],
        from_address: MailingAddress,
        mail_type: str
    ) -> str:
        """Submit letter to USPS Business Customer Gateway."""

        # Phase 2 implementation options:
        # 1. Partner with Click2Mail or PostGrid (abstraction layer)
        # 2. Direct USPS Business Customer Gateway integration
        # 3. Local printing + USPS pickup scheduling

        # For now, raise NotImplementedError
        raise NotImplementedError("USPS gateway integration pending Phase 2")
```

**A/B Testing Framework**:
```python
# backend/services/mailing_service_factory.py
class MailingServiceFactory:
    """Factory for selecting mailing service provider."""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_mailing_service(self, user_id: str) -> MailingServiceInterface:
        """Select mailing service based on A/B testing rules."""

        # Check A/B test assignment
        ab_test_group = await self._get_ab_test_group(user_id)

        if ab_test_group == "usps":
            # USPS test group
            return USPSMailingService()
        elif ab_test_group == "lob":
            # Lob control group
            return LobMailingService()
        else:
            # Default to Lob (fallback)
            return LobMailingService()

    async def _get_ab_test_group(self, user_id: str) -> str:
        """Determine A/B test group for user."""

        # Check cache
        cache_key = f"ab_test:mailing:{user_id}"
        cached_group = await self.redis.get(cache_key)

        if cached_group:
            return cached_group.decode()

        # Assign group based on user ID hash
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)

        # Month 8: 10% USPS, 90% Lob
        # Month 9: 50% USPS, 50% Lob
        # Month 10+: 100% USPS

        current_month = self._get_migration_month()

        if current_month == 8:
            threshold = 10
        elif current_month == 9:
            threshold = 50
        elif current_month >= 10:
            threshold = 100
        else:
            threshold = 0  # Phase 1: No USPS yet

        group = "usps" if (user_hash % 100) < threshold else "lob"

        # Cache assignment
        await self.redis.setex(cache_key, 86400 * 30, group)  # 30 days

        return group
```

**Cost Comparison** (per letter):

| Provider | Base Cost | Certified Mail | Total | Margin @ $5 | Margin @ $10 |
|----------|-----------|----------------|-------|-------------|--------------|
| Lob.com | $0.66 | $1.34 | $2.00 | 60% | 80% |
| USPS Direct | $0.66 | $3.75 | $4.41 | -12% | 56% |
| **Error in analysis** | | | | | |

**Correction**: USPS certified mail is more expensive ($4.41) than Lob ($2.00). The guidance specification's cost reduction assumption is **incorrect**.

**Revised Recommendation**:
- **Keep Lob.com long-term** - Lower cost and better developer experience
- **USPS Direct not viable** for cost optimization
- **Alternative**: Negotiate volume discounts with Lob (10,000+ letters → potential 20-30% discount)

---

## Payment Processing Integration

### Stripe Integration for Letter Mailing Payments

**Architecture**:
```python
# backend/services/payment_service.py
import stripe
from core.config import get_settings

settings = get_settings()
stripe.api_key = settings.stripe_secret_key

class PaymentService:
    """Handle payment processing for letter mailing."""

    async def create_checkout_session(
        self,
        user_id: str,
        letter_id: str,
        amount_cents: int
    ) -> str:
        """Create Stripe Checkout session for letter mailing."""

        session = stripe.checkout.Session.create(
            customer_email=await self._get_user_email(user_id),
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Dispute Letter Mailing",
                        "description": f"Certified mail delivery for letter {letter_id}"
                    },
                    "unit_amount": amount_cents
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{settings.frontend_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/checkout/cancel",
            metadata={
                "user_id": user_id,
                "letter_id": letter_id,
                "service_type": "letter_mailing"
            }
        )

        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhook events."""

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.stripe_webhook_secret
            )

            if event.type == "checkout.session.completed":
                session = event.data.object
                await self._fulfill_letter_mailing(session)

            elif event.type == "payment_intent.payment_failed":
                payment_intent = event.data.object
                await self._handle_payment_failure(payment_intent)

        except ValueError:
            raise PaymentError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise PaymentError("Invalid signature")

    async def _fulfill_letter_mailing(self, session: Dict[str, Any]):
        """Fulfill letter mailing after successful payment."""

        metadata = session.metadata
        user_id = metadata['user_id']
        letter_id = metadata['letter_id']

        # Trigger mailing service
        mailing_service = get_mailing_service(user_id)
        letter = await get_letter(letter_id)

        result = await mailing_service.send_letter(
            to_address=letter['to_address'],
            letter_content=letter['content']
        )

        # Update database
        await update_letter_status(
            letter_id,
            status="Sent",
            tracking_number=result.tracking_number,
            payment_id=session.payment_intent
        )

        # Notify user
        await send_notification(
            user_id,
            f"Your letter has been sent! Tracking: {result.tracking_number}"
        )
```

---

## Bureau Address Management

**Credit Bureau Mailing Addresses** (for dispute letters):

```python
# backend/data/bureau_addresses.py
BUREAU_ADDRESSES = {
    "Equifax": MailingAddress(
        name="Equifax Information Services LLC",
        address_line1="P.O. Box 740256",
        address_line2=None,
        city="Atlanta",
        state="GA",
        zip_code="30374"
    ),
    "TransUnion": MailingAddress(
        name="TransUnion Consumer Solutions",
        address_line1="P.O. Box 2000",
        address_line2=None,
        city="Chester",
        state="PA",
        zip_code="19016"
    ),
    "Experian": MailingAddress(
        name="Experian Dispute Resolution",
        address_line1="P.O. Box 4500",
        address_line2=None,
        city="Allen",
        state="TX",
        zip_code="75013"
    )
}
```

---

## Conclusion

The mailing service integration strategy prioritizes fast MVP delivery with Lob.com while maintaining architectural flexibility for future optimizations. The abstraction layer enables seamless provider switching and A/B testing for continuous improvement.

**Key Findings**:
- ✅ Lob.com provides best balance of speed-to-market and cost efficiency
- ❌ USPS Direct is more expensive ($4.41 vs. $2.00 per letter) - not viable for cost reduction
- ✅ Stripe integration enables one-click checkout for paid mailing service
- ✅ Retry mechanism ensures high delivery success rate despite API failures
