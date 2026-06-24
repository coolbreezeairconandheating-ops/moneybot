"""
Resolves the current-month MCX Crude Oil futures instrument_key by downloading
and filtering Upstox's instrument master file.

Why this exists: Upstox instrument keys for MCX futures are NOT stable strings
you can hardcode (e.g. just "CRUDEOIL") -- they're tied to a specific exchange
token per contract/expiry, and the active contract rolls over every month.
Hardcoding last month's key will silently break your bot. This module always
fetches the *current* file at startup so it stays correct without you having
to edit code every expiry.
"""

import gzip
import json
import logging
from datetime import datetime
from io import BytesIO

import requests

from . import config

logger = logging.getLogger(__name__)


def fetch_mcx_instruments() -> list[dict]:
    """Download and parse the MCX instrument master file."""
    resp = requests.get(config.MCX_INSTRUMENTS_URL, timeout=30)
    resp.raise_for_status()
    with gzip.open(BytesIO(resp.content)) as f:
        data = json.load(f)
    return data


def find_current_crudeoil_future(instruments: list[dict]) -> dict:
    """
    Filter for CRUDEOIL futures contracts and return the one with the
    nearest (soonest, but not yet expired) expiry -- i.e. the current month
    contract that's actively traded.
    """
    candidates = []
    now = datetime.now()

    for inst in instruments:
        name = (inst.get("name") or inst.get("trading_symbol") or "").upper()
        instrument_type = inst.get("instrument_type", "")
        segment = inst.get("segment", "")

        if "CRUDEOIL" not in name:
            continue
        if instrument_type != "FUT":
            continue
        if segment != "MCX_FO":
            continue

        expiry_raw = inst.get("expiry")
        if not expiry_raw:
            continue

        # Upstox expiry is typically epoch millis or an ISO string depending
        # on file version -- handle both defensively.
        try:
            if isinstance(expiry_raw, (int, float)):
                expiry_dt = datetime.fromtimestamp(expiry_raw / 1000)
            else:
                expiry_dt = datetime.fromisoformat(str(expiry_raw).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        if expiry_dt < now:
            continue  # already expired, skip

        candidates.append((expiry_dt, inst))

    if not candidates:
        raise RuntimeError(
            "No active CRUDEOIL futures contract found in MCX instrument file. "
            "Upstox may have changed their file format, or MCX trading may be "
            "disabled -- check https://community.upstox.com for announcements."
        )

    candidates.sort(key=lambda pair: pair[0])
    nearest_expiry, instrument = candidates[0]
    logger.info(
        "Resolved current CRUDEOIL future: %s (expiry %s, instrument_key %s)",
        instrument.get("trading_symbol"),
        nearest_expiry.date(),
        instrument.get("instrument_key"),
    )
    return instrument


def get_current_crudeoil_instrument_key() -> tuple[str, dict]:
    """Convenience wrapper: returns (instrument_key, full_instrument_dict)."""
    instruments = fetch_mcx_instruments()
    inst = find_current_crudeoil_future(instruments)
    return inst["instrument_key"], inst
