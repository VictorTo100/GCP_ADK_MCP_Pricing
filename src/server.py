"""
Option Pricing MCP Server.

Black '76 model for pricing options.
"""

import os
import logging
from typing import Annotated
import asyncio

# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP
from pydantic import Field

from src.pricing.black76 import (
    OptionType,
    black76_price
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("option_pricing-mcp")

mcp = FastMCP(
    name="option-pricing-server"
)


from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy"})


@mcp.custom_route("/", methods=["GET"])
async def root(request):
    return JSONResponse({
        "service": "Option Pricing MCP Server",
        "model": "Black '76",
        "tools": ["price_option_black76"],
    })

@mcp.tool()
def price_option_black76(
        forward_price: Annotated[float, Field(gt=0, description="Current SPX index level (e.g., 5000)")],
        strike: Annotated[float, Field(gt=0, description="Strike price")],
        dcf: Annotated[float, Field(description=" day count fraction")],
        df: Annotated[float, Field(gt=0, description="discount factor")],
        implied_volatility: Annotated[float, Field(gt=0, description="Implied volatility (e.g., 0.15 for 15%)")],
        option_type: Annotated[str, Field(pattern="^(call|put)$", description="'call' or 'put'")]

) -> dict:
    """
    Price an SPX index option using Black '76 model.

    SPX options are European-style, cash-settled options on the S&P 500.
    The multiplier is $100 per index point.

    Returns the option premium and all Greeks.
    """
    #logger.info(f"price_option: SPX={spot}, K={strike}, DTE={days_to_expiry}, σ={volatility}")

    try:
        result = black76_price(forward_price, strike,dcf, df, implied_volatility, option_type=OptionType(option_type)
        )

        return {
            "status": "success",
            "instrument": "Option",
            "model": "Black '76",
            "type": option_type.upper(),
            "inputs": {
                "forward": forward_price,
                "strike": strike,
            },
            "pricing": {
                "premium": round(result.price, 2),
            },
            "greeks": {
                "delta": round(result.delta, 4),
                "gamma": round(result.gamma, 6),
                "vega_per_1pct_usd": round(result.vega * 100, 2),
            },
        }

    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.exception(f"Error: {e}")
        return {"status": "error", "message": str(e)}

def main() -> None:
    """Run the MCP server."""
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info("=" * 60)
    logger.info(f"Option Pricing MCP Server")
    logger.info("Model: Black '76")
    logger.info("=" * 60)
    logger.info(f"Listening on {host}:{port}")
    logger.info("Tools: price_option_black76")
    logger.info("=" * 60)

    asyncio.run(mcp.run_async(transport="streamable-http",  host=host, port=port,))

if __name__ == "__main__":
    main()


# logger = logging.getLogger(__name__)
# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
#
# mcp = FastMCP("MCP Server on Cloud Run")
#
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Use this to add two numbers together.
#
#     Args:
#         a: The first number.
#         b: The second number.
#
#     Returns:
#         The sum of the two numbers.
#     """
#     logger.info(f">>> Tool: 'add' called with numbers '{a}' and '{b}'")
#     return a + b
#
# if __name__ == "__main__":
#     logger.info(f" MCP server started on port {os.getenv('PORT', 8080)}")
#     # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
#     asyncio.run(
#         mcp.run_async(
#             transport="streamable-http",
#             host="0.0.0.0",
#             port=os.getenv("PORT", 8080),
#         )
#     )