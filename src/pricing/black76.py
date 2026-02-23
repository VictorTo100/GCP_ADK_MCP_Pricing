"""
Black '76 Model for SPX Index Options.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class OptionType(str, Enum):
    """Option type: Call or Put."""
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class SPXOptionResult:
    """
    Result of SPX option pricing.

    Attributes:
        price: Option premium per index point (multiply by $100 for USD value)
        delta: Sensitivity to 1-point move in forward
        gamma: Rate of delta change per 1-point move
        vega: Sensitivity to 1% change in implied volatility
    """
    price: float
    delta: float
    gamma: float
    vega: float

    @property
    def dollar_price(self) -> float:
        """Option price in USD (SPX multiplier is $100)."""
        return self.price * 100.0

    def to_dict(self, decimals: int = 4) -> dict:
        """Convert to dictionary with rounded values."""
        return {
            "price": round(self.price, decimals),
            "dollar_price": round(self.dollar_price, 2),
            "delta": round(self.delta, decimals),
            "gamma": round(self.gamma, 6),
            "vega": round(self.vega, decimals),
        }


def norm_cdf(x: float) -> float:
    """Standard normal CDF using error function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black76_price(
        forward_price: float,
        strike: float,
        dcf: float,
        df: float,
        implied_volatility: float,
        option_type: OptionType | str,
) -> SPXOptionResult:
    """
    Price an SPX index option using Black '76.

    Call: C = df × [F × N(d1) - K × N(d2)]
    Put:  P = df × [K × N(-d2) - F × N(-d1)]

    Args:
        forward_price: Forward index level
        strike: Strike price
        dcf: Day count fraction (time to expiry in years)
        df: Discount factor e^(-rT)
        implied_volatility: Implied volatility (e.g., 0.15 for 15%)
        option_type: "call" or "put"

    Returns:
        SPXOptionResult with price and Greeks
    """
    if forward_price <= 0:
        raise ValueError(f"Forward must be positive, got {forward_price}")
    if strike <= 0:
        raise ValueError(f"Strike must be positive, got {strike}")
    if dcf <= 0:
        raise ValueError(f"DCF must be positive, got {dcf}")
    if implied_volatility <= 0:
        raise ValueError(f"Volatility must be positive, got {implied_volatility}")

    if isinstance(option_type, str):
        option_type = OptionType(option_type.lower())

    # d1, d2
    sqrt_t = math.sqrt(dcf)
    d_1 = (math.log(forward_price / strike) + (implied_volatility ** 2 / 2) * dcf) / (implied_volatility * sqrt_t)
    d_2 = d_1 - implied_volatility * sqrt_t

    pdf_d1 = norm_pdf(d_1)

    # Price
    if option_type == OptionType.CALL:
        price = df * (forward_price * norm_cdf(d_1) - strike * norm_cdf(d_2))
        delta = df * norm_cdf(d_1)
    else:
        price = df * (strike * norm_cdf(-d_2) - forward_price * norm_cdf(-d_1))
        delta = -df * norm_cdf(-d_1)

    # Gamma: ∂²V/∂F²
    gamma = df * pdf_d1 / (forward_price * implied_volatility * sqrt_t)

    # Vega: ∂V/∂σ (per 1% move)
    vega = df * forward_price * pdf_d1 * sqrt_t / 100.0

    return SPXOptionResult(
        price=price,
        delta=delta,
        gamma=gamma,
        vega=vega,
    )


if __name__ == "__main__":
    # Example: ATM 30-day option
    # F=5000, K=5000, T=30/365, r=5% → df=e^(-0.05*30/365)≈0.9959, vol=15%

    dcf = 30 / 365
    df = math.exp(-0.05 * dcf)

    call = black76_price(
        forward_price=5500,
        strike=5000,
        dcf=dcf,
        df=df,
        implied_volatility=0.15,
        option_type="call",
    )

    print("ATM Call (F=5000, K=5000, 30 days, 15% vol)")
    print(f"  Price:  {call.price:.2f} pts (${call.dollar_price:,.2f})")
    print(f"  Delta:  {call.delta:.4f}")
    print(f"  Gamma:  {call.gamma:.6f}")
    print(f"  Vega:   {call.vega:.4f} pts/1% vol (${call.vega * 100:.2f})")