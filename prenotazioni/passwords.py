"""Utility functions per la generazione di password sicure.

Questo modulo espone `generate_strong_password` che crea password
criptograficamente sicure che rispettano requisiti minimi di complessità.
"""
from __future__ import annotations

import secrets
import string
from typing import Optional


_AMBIGUOUS = set('Il1O0')


def generate_strong_password(length: int = 16, avoid_ambiguous: bool = True) -> str:
    """Genera una password forte e casuale.

    Requisiti garantiti:
    - contiene almeno una lettera maiuscola
    - contiene almeno una lettera minuscola
    - contiene almeno una cifra
    - contiene almeno un carattere speciale

    Args:
        length: lunghezza complessiva della password (minimo 8)
        avoid_ambiguous: rimuove caratteri ambigui come 'I', 'l', '1', 'O', '0'

    Returns:
        password casuale come stringa
    """
    if length < 8:
        length = 8

    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    specials = '!@#$%^&*()-_=+[]{};:,.<>?/\\|`~'

    if avoid_ambiguous:
        def _filter(s: str) -> str:
            return ''.join(ch for ch in s if ch not in _AMBIGUOUS)

        uppercase = _filter(uppercase)
        lowercase = _filter(lowercase)
        digits = _filter(digits)
        # leave specials unchanged

    # Ensure at least one of each required category
    required = [secrets.choice(uppercase), secrets.choice(lowercase), secrets.choice(digits), secrets.choice(specials)]

    # Build the remaining pool
    pool = uppercase + lowercase + digits + specials

    # Fill the rest
    remaining = [secrets.choice(pool) for _ in range(length - len(required))]

    # Combine and shuffle securely
    password_chars = required + remaining
    secrets.SystemRandom().shuffle(password_chars)

    return ''.join(password_chars)
