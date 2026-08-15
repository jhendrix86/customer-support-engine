"""
Real SLA deadline calculation, driven by Settings.

Previously tickets.py hardcoded the same 1/4/24/48-hour literals inline
while settings.sla_critical_hours/sla_high_hours/sla_medium_hours/
sla_low_hours existed and were never read by anything - two disconnected
sources of truth for the same numbers. This is now the one place that
math happens.
"""

from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from app.models.ticket import TicketPriority

_HOURS_BY_PRIORITY = {
    TicketPriority.CRITICAL: settings.sla_critical_hours,
    TicketPriority.HIGH: settings.sla_high_hours,
    TicketPriority.MEDIUM: settings.sla_medium_hours,
    TicketPriority.LOW: settings.sla_low_hours,
}


def compute_sla_deadline(priority: TicketPriority, from_time: Optional[datetime] = None) -> datetime:
    from_time = from_time or datetime.utcnow()
    hours = _HOURS_BY_PRIORITY.get(priority, settings.default_sla_hours)
    return from_time + timedelta(hours=hours)
