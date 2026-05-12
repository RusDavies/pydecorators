"""Executable examples for retry idempotency guidance."""

from useful_decorators import retry


class PaymentGateway:
    """Tiny fake gateway that deduplicates by idempotency key."""

    def __init__(self) -> None:
        self._charges: dict[str, str] = {}
        self.failures_remaining = 1

    def charge(self, *, amount_cents: int, idempotency_key: str) -> str:
        if idempotency_key in self._charges:
            return self._charges[idempotency_key]
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise ConnectionError("lost response from gateway")
        charge_id = f"charge:{amount_cents}:{idempotency_key}"
        self._charges[idempotency_key] = charge_id
        return charge_id


def idempotency_key_example() -> tuple[str, int]:
    """Retry a side-effecting operation only with an idempotency key."""

    gateway = PaymentGateway()
    attempts = 0

    @retry(attempts=2, exceptions=ConnectionError, sleep=lambda seconds: None)
    def submit_payment(*, amount_cents: int, idempotency_key: str) -> str:
        nonlocal attempts
        attempts += 1
        return gateway.charge(amount_cents=amount_cents, idempotency_key=idempotency_key)

    charge_id = submit_payment(amount_cents=5000, idempotency_key="invoice-123")
    duplicate = submit_payment(amount_cents=5000, idempotency_key="invoice-123")
    return charge_id if charge_id == duplicate else "duplicate-charge", attempts


def retry_read_example() -> str:
    """Reads are usually safer retry candidates than mutations."""

    failures_remaining = 1

    @retry(attempts=2, exceptions=TimeoutError, sleep=lambda seconds: None)
    def fetch_status() -> str:
        nonlocal failures_remaining
        if failures_remaining:
            failures_remaining -= 1
            raise TimeoutError("transient read timeout")
        return "ready"

    return fetch_status()
