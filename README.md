# Resumo FIC FIDC — Dashboard

Dashboard em Streamlit que recebe o extrato bancário do fundo (CSV) e a posição
do fundo no fundo de liquidez (XLSX) e devolve um texto formatado pronto para
copiar e enviar no WhatsApp:

```
FIC FIDC Elantra
- Saldo fundo de liquidez + saldo em conta: R$ 408,83
- Aportes por cotista:
Rodrigo:
Entrada: R$ 1.472.401,00
Saída: R$ 293.750,00
Líquido: R$ 1.178.651,00
...
- Gastos do fundo em maio: R$ 9.297,52 (ADM, Gestão, CVM)
- Gastos do fundo desde o início: R$ 46.740,83
Administradora ID: Débitos: R$ 54.072,87; Reembolsos/Créditos: R$ 31.421,06; Líquido: R$ 22.651,81
...
```

## Estrutura

```
fic-fidc-dashboard/
├── app.py             # UI Streamlit
├── core.py            # Lógica de parsing, cálculo e geração do texto
├── config.py          # Cotistas, categorias de despesa, abreviações
├── requirements.txt
└── README.md
```

A separação `app.py` / `core.py` deixa a lógica testável sem subir o Streamlit.

## Rodando localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Faz upload dos dois arquivos e copia o texto
do bloco que aparece (tem ícone de copiar no canto superior direito do bloco).

## Deploy no Streamlit Community Cloud

1. Suba este diretório como um repositório no GitHub (público ou privado).
2. Acesse <https://share.streamlit.io> e logue com a conta do GitHub.
3. Clique em **Create app** → selecione o repositório, branch (`main`) e
   o arquivo principal (`app.py`).
4. Clica em **Deploy**. Em ~1 min a URL fica disponível.

> Para repositório privado, o Streamlit Cloud pede para autorizar o GitHub App.

## Manutenção: quando editar `config.py`

Edite `config.py` quando:

- **Entrar novo cotista** → adicionar entrada em `COTISTAS` com o nome curto
  desejado e padrões a buscar no campo `ds_complemento` do extrato.
- **Mudar/entrar prestador** (administradora, gestora, auditor, etc.) →
  adicionar tupla em `DESPESAS` na ordem desejada de prioridade.
- **Ajustar abreviação no parêntese de "Gastos em <mês>"** → mexer em `ABREV`.
  Categorias sem entrada em `ABREV` (ex.: Tarifas) não aparecem no parêntese
  mas continuam somando no total.

Exemplo: substituindo a gestora atual

```python
DESPESAS = [
    ...
    ("Gestora NovaXYZ", ["NOVA XYZ ASSET"], "complemento"),
    ...
]
ABREV = {
    ...
    "Gestora NovaXYZ": "Gestão",
}
```

## Premissas / como cada número é calculado

- **Saldo em conta**: soma cumulativa de todas as linhas do CSV (crédito − débito).
- **Saldo no fundo de liquidez**: lido da célula na coluna "Saldo Líquido" e
  linha "Total:" do XLSX `Saldo de Aplicações de Cotistas`. Tem opção de
  sobrescrever manualmente caso o layout do XLSX seja diferente.
- **Aportes por cotista**: apenas lançamentos do tipo PIX/TED/TEC cujo
  `ds_complemento` casa com algum padrão do cotista. Transferências internas
  entre contas do banco são ignoradas.
- **Gastos do mês**: lançamentos classificados nas categorias de `DESPESAS`,
  filtrados pelo mês escolhido (default = mês mais recente no extrato).
  Categoria "Tarifas" entra no total mas não aparece no parêntese.
- **Gastos desde o início**: idem, considerando todo o extrato. Quando há
  reembolsos/créditos para uma mesma categoria (ex.: ID Corretora estornou
  alguns débitos), a linha mostra Débitos, Créditos e Líquido separadamente.

## Sanity check

Abre a seção "🔍 Detalhes (sanity check)" no app para conferir:

- Saldo em conta, saldo no fundo de liquidez e total consolidado
- Período coberto pelo extrato e número de lançamentos
- Tabela de aportes por cotista
- Tabela de gastos por categoria (débitos / créditos / líquido / no mês)
