"""Shim de compatibilidad para el servidor MCP de StockWise.

Permite ejecutar el servidor vía:
  python server.py
  fastmcp dev inspector server.py
  fastmcp call server.py <tool>
Delegando a stockwise.interfaces.mcp.server.
"""

from stockwise.interfaces.mcp.server import main, mcp

if __name__ == "__main__":
    main()
