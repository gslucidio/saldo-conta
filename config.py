"""
Configuração do dashboard FIC FIDC.

Edite este arquivo quando:
  - Entrar um novo cotista no fundo
  - Mudar a administradora/gestora/prestador
  - Quiser ajustar a abreviação que aparece no parêntese do resumo mensal
"""

# Cotistas:
#   chave   = nome curto que aparece no resumo do WhatsApp
#   valor   = lista de padrões a buscar em ds_complemento (case-insensitive,
#             substring match — qualquer um casa)
COTISTAS = {
    "Rodrigo": ["RODRIGO DOS SANTOS"],
    "Juliano": ["JULIANO FERREIRA"],
    "José": ["JOSE MAURICIO", "JOSÉ MAURICIO"],
    "Elantra Participações": ["ELANTRA PARTICIPACOES", "ELANTRA PARTICIPAÇÕES"],
}

# Categorias de despesa: lista de tuplas (nome, [padrões], onde_buscar).
# `onde_buscar`:
#   "complemento" — procura em ds_complemento (contraparte do lançamento)
#   "historico"   — procura em ds_historico  (tipo do lançamento)
# A ordem importa: o 1º padrão que casar é o vencedor.
DESPESAS = [
    ("Administradora ID",           ["ID CORRETORA"],                  "complemento"),
    ("Gestora QLZ",                 ["QLZ ASSET"],                     "complemento"),
    ("Gestora VIZ",                 ["VIZ GESTORA"],                   "complemento"),
    ("CVM",                         ["COMISSAO DE VALORES", "CVM"],    "complemento"),
    ("ANBIMA",                      ["ANBIMA"],                        "complemento"),
    ("Auditoria NIX",               ["NIX AUDITORES"],                 "complemento"),
    ("Tarifas bancárias (PIX/TED)", ["TARIFA"],                        "historico"),
]

# Abreviações usadas no parêntese de "Gastos do fundo em <mês>: R$ X (ADM, Gestão, CVM)".
# Categorias sem entrada aqui (ex: Tarifas) NÃO aparecem no parêntese.
ABREV = {
    "Administradora ID": "ADM",
    "Gestora QLZ":       "Gestão",
    "Gestora VIZ":       "Gestão",
    "CVM":               "CVM",
    "ANBIMA":            "ANBIMA",
    "Auditoria NIX":     "Auditoria",
}

MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março",     4: "abril",
    5: "maio",    6: "junho",     7: "julho",     8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}
