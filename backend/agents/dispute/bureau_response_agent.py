"""
Bureau Response Agent
=====================

Tracks credit bureau responses to dispatched dispute letters and
updates dispute lifecycle status accordingly.

Dispute lifecycle (7 states):
    pending → letter_generated → mailing_dispatched → bureau_received
    → investigating → resolved | denied

This agent:
    1. Monitors disputes that are in 'mailing_dispatched' or 'bureau_received' state.
    2. Checks FCRA 30-day response deadlines.
    3. Updates status when bureau responds (via manual input or webhook).
    4. Logs status transitions to status_history table.
    5. Enqueues FCRA reminder emails at Day 1, 3, and 25.

Integrations:
    - Supabase disputes, status_history, notification_log tables.
    - workers.email_worker.send_notification_email (Celery task).
    - services.database_optimizer for DB operations.

Inputs (via execute()):
    user_id         : str              – Owner UUID.
    dispute_id      : str | None       – Process a single dispute (or all if None).
    new_status      : str | None       – If provided, update dispute to this status.
    bureau_response : Dict | None      – Parsed bureau response document data.

Output (AgentResult.data):
    {
        "disputes_checked":    int,
        "disputes_updated":    int,
        "overdue_disputes":    int,     # past 30-day FCRA deadline
        "reminders_sent":      int,
        "status_transitions":  [
            {
                "dispute_id":  str,
                "old_status":  str,
                "new_status":  str,
                "changed_at":  str,
            },
            ...
        ],
    }
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agents.base import BaseAgent


# Valid status transitions
VALID_TRANSITIONS = {
    "pending":              ["letter_generated"],
    "letter_generated":     ["mailing_dispatched"],
    "mailing_dispatched":   ["bureau_received"],
    "bureau_received":      ["investigating"],
    "investigating":        ["resolved", "denied"],
}

# FCRA 30-day deadline milestones for email reminders
FCRA_REMINDER_DAYS = [1, 3, 25]


class BureauResponseAgent(BaseAgent):
    """Track bureau responses and manage dispute lifecycle."""

    def __init__(self) -> None:
        super().__init__()

    async def _fetch_active_disputes(
        self,
        user_id: str,
        dispute_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load disputes in active states from Supabase.

        Args:
            user_id:    Owner UUID.
            dispute_id: Optional single dispute to fetch.

        Returns:
            List of dispute records with id, status, created_at, bureau, etc.
        """
        # TODO:
        # 1. Query disputes table via database_optimizer.
        # 2. Filter to active statuses (not 'resolved' or 'denied').
        # 3. Return list of dicts.
        raise NotImplementedError

    async def _validate_transition(
        self,
        current_status: str,
        new_status: str,
    ) -> bool:
        """Check if a status transition is valid per the state machine.

        Args:
            current_status: Current dispute status string.
            new_status:     Proposed new status string.

        Returns:
            True if the transition is allowed.
        """
        allowed = VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    async def _update_dispute_status(
        self,
        dispute_id: str,
        old_status: str,
        new_status: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Update dispute status and write to status_history.

        Args:
            dispute_id: UUID of the dispute record.
            old_status: Previous status string.
            new_status: New status string.
            user_id:    Who made the change.

        Returns:
            Dict with dispute_id, old_status, new_status, changed_at.
        """
        # TODO:
        # 1. UPDATE disputes SET status = new_status WHERE id = dispute_id.
        # 2. INSERT INTO status_history (dispute_id, old_status, new_status, changed_by).
        # 3. INSERT INTO notification_log (user_id, 'dispute_update', metadata).
        # 4. Return transition record.
        raise NotImplementedError

    async def _check_fcra_deadlines(
        self,
        disputes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify disputes approaching or past the 30-day FCRA deadline.

        Args:
            disputes: Active dispute records.

        Returns:
            List of overdue/approaching dispute dicts with days_elapsed.
        """
        # TODO:
        # 1. For each dispute in 'mailing_dispatched' or 'bureau_received':
        #    a. Calculate days since created_at.
        #    b. If days_elapsed >= 30, mark as overdue.
        #    c. If days_elapsed in FCRA_REMINDER_DAYS, enqueue reminder.
        # 2. Return list of overdue disputes.
        raise NotImplementedError

    async def _send_fcra_reminder(
        self,
        user_id: str,
        dispute_id: str,
        day: int,
    ) -> None:
        """Enqueue an FCRA deadline reminder email.

        Args:
            user_id:    Owner UUID.
            dispute_id: Dispute UUID.
            day:        Which FCRA reminder day (1, 3, or 25).
        """
        # TODO:
        # 1. Call email_worker.send_notification_email.delay(
        #        user_id, f'fcra_day{day}', {'dispute_id': dispute_id, 'day': day}
        #    )
        raise NotImplementedError

    async def _run(
        self,
        *,
        user_id: str,
        dispute_id: Optional[str] = None,
        new_status: Optional[str] = None,
        bureau_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check disputes, update statuses, and send FCRA reminders.

        Args:
            user_id:          Owner UUID.
            dispute_id:       Process single dispute (or all if None).
            new_status:       Manual status update.
            bureau_response:  Parsed response data from bureau (future: OCR).

        Returns:
            Dict with disputes_checked, disputes_updated, overdue_disputes,
            reminders_sent, status_transitions.
        """
        # TODO:
        # 1. Fetch active disputes.
        # 2. If new_status provided, validate and apply transition.
        # 3. Check FCRA deadlines on remaining disputes.
        # 4. Send reminders for milestone days.
        # 5. Return summary.
        raise NotImplementedError
