# Pacote do módulo de mapeamento de rede
from flask import Blueprint

# Blueprint único que contém a rota de UI e as APIs
from .routes import rede_bp

__all__ = ["rede_bp"]
