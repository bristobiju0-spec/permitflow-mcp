import anyio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def main():
    url = "https://sales-agent-pro.onrender.com/sse"
    print(f"Connecting to {url}...")
    
    try:
        async with sse_client(url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("Connected! Calling research_prospect...")
                result = await session.call_tool("research_prospect", arguments={"name": "Aladdin Baitfadhil", "company": "Omantel"})
                print("\nResult:")
                print(result.content[0].text)
    except Exception as e:
        print(f"Error connecting or calling tool: {e}")

if __name__ == "__main__":
    anyio.run(main)
