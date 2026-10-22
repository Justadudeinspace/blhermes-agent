"""Exercise an actual local MCP stdio child and bounded clean shutdown, offline."""
from __future__ import annotations

import asyncio
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


async def probe() -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from tools.mcp_tool_transport import _stdio_launch

    command, environment, cwd = _stdio_launch({'command': sys.executable})

    async with asyncio.timeout(30):
        params = StdioServerParameters(command=command, args=[str(Path(__file__).with_name('mcp_fixture.py'))], env=environment, cwd=cwd)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as client:
                await client.initialize()
                tools = await client.list_tools()
                assert any(tool.name == 'acceptance_ping' for tool in tools.tools)
                result = await client.call_tool('acceptance_ping', {})
                assert not result.is_error
                assert any(getattr(item, 'text', '') == 'BLHERMES_MCP_OK' for item in result.content)
    print('MCP_LOCAL_STDIO_OK')


if __name__ == '__main__':
    asyncio.run(probe())
