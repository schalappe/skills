# Redaction & PII Handling

Strip or mask sensitive fields before the event leaves the process. Load when touching logs that may see user input, auth headers, or payment data.

## Never log

- Passwords, API keys, bearer tokens, refresh tokens, session cookies
- Full credit-card PAN, CVV, bank-account numbers
- Social-security / national-ID numbers
- Unencrypted PII (raw email, phone, address) where consent or policy forbids it

## Key-name allowlist / denylist

```python
SENSITIVE_FIELDS = {"password", "token", "api_key", "secret", "ssn", "credit_card"}

def redact_sensitive(data: dict) -> dict:
    """Replace sensitive fields with [REDACTED], recursively."""
    result = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = redact_sensitive(value)
        else:
            result[key] = value
    return result
```

Prefer an **allowlist** (explicit safe keys) for anything user-facing. Denylists drift behind new fields.

## Masking and hashing

Keep enough signal to debug without exposing the raw value.

```python
import hashlib

def mask_email(email: str) -> str:
    """Mask email while keeping some identifiability."""
    local, domain = email.split("@")
    return f"{local[0]}***@{domain}"

def hash_user_id(user_id: str, salt: str) -> str:
    """Hash user ID for privacy while keeping correlation."""
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()[:16]
```

Hash with a **per-deployment salt** so hashes can't be correlated across environments or leaked logs from different services.

## Where to apply

Redact inside the emit step, after context is fully built — not at each `add()`. That way a single audit of the emit path covers every call site.
