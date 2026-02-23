import asyncio
import subprocess

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


def get_identity_token():
    return subprocess.check_output(
        ["/Users/vishruttalekar/google-cloud-sdk/bin/gcloud", "auth", "print-identity-token"],
        text=True
    ).strip()


async def test_server():
    token = get_identity_token()

    transport = StreamableHttpTransport(
        url="https://pricing-mcp-server-869786913402.europe-west1.run.app/mcp/",
        headers={"Authorization": f"Bearer {token}"},
    )

    async with Client(transport) as client:
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> Tool: {tool.name}")

        result = await client.call_tool(
            "price_option_black76",
            {
                "forward_price": 6250,
                "strike": 6750,
                "dcf": 0.25,
                "df": 0.9802,
                "implied_volatility": 0.15,
                "option_type": "call",
            },
        )
        print(f"<<< Result: {result[0].text}")


if __name__ == "__main__":
    asyncio.run(test_server())