"""
Configuração do dashboard FIC FIDC.

O app agrega automaticamente cada contraparte que aparece nas movimentações
PIX/TED do extrato — sem classificar ninguém. A única configuração aqui é a
lista de sufixos societários removidos ao agrupar nomes, para que variações do
mesmo nome (ex.: 'ELANTRA PARTICIPACOES' e 'ELANTRA PARTICIPACOES LTDA') sejam
tratadas como a mesma pessoa.
"""

SUFIXOS_EMPRESA = [
    "LTDA", "EIRELI", "ME", "EPP", "S.A.", "S.A", "S/A", "SA", "CIA", "S A",
]
