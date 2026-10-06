"""
Punto de entrada compatible para el servidor MCP de Análisis Bursátil.
Reenvía la ejecución al servidor centralizado en server.py.
"""
from server import mcp

if __name__ == "__main__":
    mcp.run()