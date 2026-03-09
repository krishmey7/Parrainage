# shop/sms_parser.py

"""
import re
from decimal import Decimal, InvalidOperation

# Regex : gère "Vous avez recu ..." et "Le retrait de ... est effectue ..."
SMS_REGEX = re.compile(
    r"(?:vous avez re[çc]u|le retrait de)\s+([\d\.,]+)\s*CDF.*?Ref[:\s]+([A-Z0-9\.]+)",
    flags=re.IGNORECASE | re.DOTALL
)

def parse_payment_sms(sms_text: str):

    #Retourne (amount_decimal, reference) ou (None, None) si non trouvé.

    m = SMS_REGEX.search(sms_text or "")
    if not m:
        return None, None

    raw_amount = m.group(1).strip()
    reference = m.group(2).strip()

    # Normaliser le montant
    normalized = raw_amount.replace(" ", "").replace(",", ".")
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None, None

    return amount, reference
"""



import re
from decimal import Decimal, InvalidOperation

PATTERNS = [
    # ancien format (CDF + Ref)
    re.compile(
        r"(?:vous avez re[çc]u|le retrait de)\s+([\d\.,]+)\s*(?:FC|CDF).*?Ref(?:erence)?[:\s]+([A-Z0-9\.]+)",
        flags=re.IGNORECASE | re.DOTALL
    ),

    # ⭐ pattern corrigé (ignore : "+ 4.000 Fc")
    re.compile(
        r"vous avez re[çc]u\s+([\d\.,]+)\s*(?:fc|cdf)\b(?!\s*\+).*?reference[:\s]+([A-Z0-9\.]+)",
        flags=re.IGNORECASE | re.DOTALL
    ),

    # format générique Montant
    re.compile(
        r"Montant\s*[:\-]\s*([\d\.,]+)\s*(?:[A-Z]{3})?\b.*?Ref(?:erence)?[:\s]+([A-Z0-9\.]+)",
        flags=re.IGNORECASE | re.DOTALL
    ),

    # fallback
    re.compile(
        r"(?:Ref(?:erence)?[:\s]+([A-Z0-9\.]+)).{0,80}?([\d\.,]+)\s*(?:CDF|FC|[A-Z]{2,3})?",
        flags=re.IGNORECASE | re.DOTALL
    ),
    re.compile(
        r"([\d\.,]+)\s*(?:CDF|FC|[A-Z]{2,3})?.{0,80}?Ref(?:erence)?[:\s]+([A-Z0-9\.]+)",
        flags=re.IGNORECASE | re.DOTALL
    ),
]

def _normalize_amount_str(raw_amount: str) -> str:
    s = raw_amount.replace("\u00A0", "").replace(" ", "").strip()
    if "." in s and "," in s:
        last_dot = s.rfind(".")
        last_comma = s.rfind(",")
        if last_comma > last_dot:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    return s

def parse_payment_sms(sms_text: str):
    text = sms_text or ""

    for pattern in PATTERNS:
        m = pattern.search(text)
        if not m:
            continue

        amount_str = m.group(1)
        reference = m.group(2)

        if not amount_str:
            continue

        normalized = _normalize_amount_str(amount_str)
        try:
            amount = Decimal(normalized)
        except InvalidOperation:
            continue

        if not reference:
            ref_m = re.search(r"Ref(?:erence)?[:\s]+([A-Z0-9\.]+)", text, re.IGNORECASE)
            reference = ref_m.group(1).strip() if ref_m else None

        return amount, reference

    return None, None
