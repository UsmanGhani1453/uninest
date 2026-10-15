from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    provider: str
    reference: str | None = None
    message: str = "Mock payment; no money was charged."


async def create_payment(amount: float, currency: str = "PKR") -> PaymentResult:
    # Mock adapter only. Do not treat this as a real payment.
    return PaymentResult(success=False, provider="mock", message=f"No payment processed for {amount:.2f} {currency}.")
