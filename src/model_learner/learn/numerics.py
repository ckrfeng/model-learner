"""Standard-library Beta CDF and quantiles for equal-tail posterior intervals."""

from __future__ import annotations

import math

MAX_BETA_SHAPE_SUM = 100_000


def beta_cdf(x: float, alpha: float, beta: float) -> float:
    """Regularized incomplete beta via a continued fraction and symmetry.

    This is an exact-distribution numerical interval, not a normal approximation.
    The continued fraction uses modified Lentz iteration in double precision.
    """
    if not all(math.isfinite(value) for value in (x, alpha, beta)):
        raise ValueError("Beta arguments must be finite")
    if alpha < 0.5 or beta < 0.5 or not 0 <= x <= 1:
        raise ValueError(
            "supported Beta shapes are at least 0.5 and x must be in [0, 1]"
        )
    if alpha + beta > MAX_BETA_SHAPE_SUM:
        raise ValueError("supported Beta shape sum is at most 100,000")
    if x == 0 or x == 1:
        return x
    factor = math.exp(
        math.lgamma(alpha + beta)
        - math.lgamma(alpha)
        - math.lgamma(beta)
        + alpha * math.log(x)
        + beta * math.log1p(-x)
    )
    if x < (alpha + 1) / (alpha + beta + 2):
        result = factor * _fraction(x, alpha, beta) / alpha
    else:
        result = 1 - factor * _fraction(1 - x, beta, alpha) / beta
    return min(1.0, max(0.0, result))


def beta_quantile(probability: float, alpha: float, beta: float) -> float:
    """Invert the monotone CDF with bounded bisection (absolute error < 1e-14)."""
    # Validate shapes even for an endpoint probability.
    beta_cdf(0.5, alpha, beta)
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("probability must be finite and in [0, 1]")
    if probability in (0, 1):
        return probability
    lower, upper = 0.0, 1.0
    for _ in range(55):
        midpoint = (lower + upper) / 2
        if beta_cdf(midpoint, alpha, beta) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2


def _fraction(x: float, alpha: float, beta: float) -> float:
    tiny = 1e-300
    total = alpha + beta
    c = 1.0
    d = 1 - total * x / (alpha + 1)
    d = 1 / (d if abs(d) > tiny else tiny)
    value = d
    for iteration in range(1, 401):
        twice = 2 * iteration
        terms = (
            iteration
            * (beta - iteration)
            * x
            / ((alpha + twice - 1) * (alpha + twice)),
            -(alpha + iteration)
            * (total + iteration)
            * x
            / ((alpha + twice) * (alpha + twice + 1)),
        )
        for term in terms:
            d = 1 + term * d
            d = 1 / (d if abs(d) > tiny else tiny)
            c = 1 + term / c
            c = c if abs(c) > tiny else tiny
            delta = d * c
            value *= delta
        if abs(delta - 1) < 3e-14:
            return value
    raise ArithmeticError("Beta CDF continued fraction did not converge")
