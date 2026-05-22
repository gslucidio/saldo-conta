"""
Configuração do dashboard FIC FIDC.

O app agrega automaticamente cada contraparte das movimentações PIX/TED — sem
classificar ninguém. Aqui ficam apenas:
  - SUFIXOS_EMPRESA: sufixos societários removidos ao agrupar nomes, para juntar
    variações do mesmo nome (ex.: 'ELANTRA PARTICIPACOES' e '... LTDA').
  - PADROES_FUNDO_LIQUIDEZ: como identificar, no extrato, as linhas dos fundos de
    liquidez (usado na reconciliação extrato × carteira). Acrescente padrões se
    entrar um novo fundo de liquidez.
"""

SUFIXOS_EMPRESA = [
    "LTDA", "EIRELI", "ME", "EPP", "S.A.", "S.A", "S/A", "SA", "CIA", "S A",
]

# Substrings (sem acento, maiúsculas) que identificam um fundo de liquidez no
# campo ds_complemento do extrato. Cada chave é o nome curto exibido.
PADROES_FUNDO_LIQUIDEZ = {
    "ID RF": ["ID RF"],
    "ID SOBERANO": ["ID SOBERANO"],
}
