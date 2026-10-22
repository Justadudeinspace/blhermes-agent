"""Reviewed offline MCP acceptance fixture: one constant tool, no file/network access."""
from mcp.server import MCPServer

server = MCPServer('blhermes-acceptance')


@server.tool()
def acceptance_ping() -> str:
    """Return a constant acceptance marker without reading user state."""
    return 'BLHERMES_MCP_OK'


if __name__ == '__main__':
    server.run(transport='stdio')
