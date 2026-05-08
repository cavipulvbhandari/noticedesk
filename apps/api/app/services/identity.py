"""PAN-centric identity utilities.

Implements the contract from Sprint 1:

* :func:`extract_pan_from_gstin`
* :func:`validate_pan_format`
* :func:`validate_gstin_format`
* :func:`resolve_client_by_pan`
* :func:`resolve_registration_by_identifier`
* :func:`reconcile_pan_gstin`

PAN format ``^[A-Z]{5}[0-9]{4}[A-Z]$``
GSTIN format ``^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$``

Whenever a notice is ingested, the PAN/GSTIN reconciliation in this module is
the hard gate that decides whether the notice can be routed to a client or
must be flagged for review. Never silently bypass it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PAN_REGEX: Final[re.Pattern[str]] = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
GSTIN_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$"
)


def validate_pan_format(pan: str) -> bool:
    """Return True iff ``pan`` is a syntactically valid 10-character PAN."""
    if not isinstance(pan, str):
        return False
    return PAN_REGEX.match(pan) is not None


def validate_gstin_format(gstin: str) -> bool:
    """Return True iff ``gstin`` is a syntactically valid 15-character GSTIN."""
    if not isinstance(gstin, str):
        return False
    return GSTIN_REGEX.match(gstin) is not None


def extract_pan_from_gstin(gstin: str) -> str:
    """Return positions 3-12 (1-indexed) of ``gstin`` — the embedded PAN.

    Raises:
        ValueError: if ``gstin`` is not a valid GSTIN.
    """
    if not validate_gstin_format(gstin):
        raise ValueError(f"invalid GSTIN: {gstin!r}")
    return gstin[2:12]


def extract_state_code_from_gstin(gstin: str) -> str:
    if not validate_gstin_format(gstin):
        raise ValueError(f"invalid GSTIN: {gstin!r}")
    return gstin[0:2]


def reconcile_pan_gstin(pan: str, gstin: str) -> bool:
    """Return True iff ``pan`` matches positions 3-12 of ``gstin``.

    Both inputs must be syntactically valid; otherwise returns False (a
    caller treating False as ``mismatch_blocked`` is correct in that case
    too — we will not route a notice with malformed identifiers).
    """
    if not (validate_pan_format(pan) and validate_gstin_format(gstin)):
        return False
    return extract_pan_from_gstin(gstin) == pan


@dataclass(frozen=True, slots=True)
class ClientRef:
    client_id: UUID
    tenant_id: UUID
    pan: str
    legal_name: str


@dataclass(frozen=True, slots=True)
class RegistrationRef:
    registration_id: UUID
    tenant_id: UUID
    client_id: UUID
    registration_type: str
    identifier_value: str
    state_code: str | None


async def resolve_client_by_pan(
    session: AsyncSession, tenant_id: UUID, pan: str
) -> ClientRef | None:
    """Look up a client by PAN within the current tenant.

    Returns ``None`` if no client exists. Caller is responsible for raising
    a routing-blocked error when this is the case.
    """
    if not validate_pan_format(pan):
        raise ValueError(f"invalid PAN: {pan!r}")
    row = (
        await session.execute(
            text(
                "SELECT client_id, tenant_id, pan, legal_name "
                "FROM clients WHERE tenant_id = :tid AND pan = :pan"
            ),
            {"tid": str(tenant_id), "pan": pan},
        )
    ).first()
    if row is None:
        return None
    return ClientRef(
        client_id=row[0],
        tenant_id=row[1],
        pan=row[2],
        legal_name=row[3],
    )


async def resolve_registration_by_identifier(
    session: AsyncSession, tenant_id: UUID, identifier_value: str
) -> RegistrationRef | None:
    """Look up an IT or GST registration by its identifier_value.

    For IT: ``identifier_value`` is the PAN.
    For GST: ``identifier_value`` is the GSTIN.
    """
    if not (validate_pan_format(identifier_value) or validate_gstin_format(identifier_value)):
        raise ValueError(f"invalid identifier: {identifier_value!r}")
    row = (
        await session.execute(
            text(
                "SELECT registration_id, tenant_id, client_id, registration_type, "
                "       identifier_value, state_code "
                "FROM client_registrations "
                "WHERE tenant_id = :tid AND identifier_value = :iv"
            ),
            {"tid": str(tenant_id), "iv": identifier_value},
        )
    ).first()
    if row is None:
        return None
    return RegistrationRef(
        registration_id=row[0],
        tenant_id=row[1],
        client_id=row[2],
        registration_type=row[3],
        identifier_value=row[4],
        state_code=row[5],
    )
