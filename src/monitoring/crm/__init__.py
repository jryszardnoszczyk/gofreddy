"""CRM contacts module — lightweight contact tracking from social interactions."""

from .models import Contact
from .repository import PostgresContactRepository
from .service import ContactService

__all__ = [
    "Contact",
    "ContactService",
    "PostgresContactRepository",
]
