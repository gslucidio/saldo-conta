# Resumo FIC FIDC — Dashboard

Dashboard em Streamlit que recebe o extrato bancário do fundo (CSV) e a(s)
posição(ões) do fundo no(s) fundo(s) de liquidez (XLSX) e gera um texto pronto
para colar no WhatsApp.

Para **cada contraparte** que aparece nas movimentações PIX/TED, soma entrada,
saída e líquido. À parte, mostra o saldo (fundo de liquidez + conta):

```
FIC FIDC Kmr Capital

Marcos:
Entrada: R$ 510.000,00
Saída: R$ 0,00
Líquido: R$ 510.000,00
Leonardo:
Entrada: R$ 506.023,00
Saída: R$ 0,00
Líquido: R$ 506.023,00
...

Saldo (fundo de liquidez + conta): R$ 1.635,44
```

## Como funciona

O app identifica automaticamente cada contraparte das movimentações **PIX/TED**
do extrato — sem classificar ninguém como cotista ou prestador. Para cada uma:

- **Entrada** = soma dos créditos (dinheiro que entrou na conta do fundo).
- **Saída** = soma dos débitos (dinheiro que saiu, incluindo devoluções/estornos).
- **Líquido** = Entrada − Saída.

A classificação usa o flag de débito/crédito do próprio extrato, então uma linha
como `PIX - RECEBIDO DEVOLVIDO` (que é um débito) entra corretamente na saída e
um estorno no mesmo dia se anula. Variações do mesmo nome são agrupadas como a mesma pessoa.
Linhas de tarifa bancária não viram contraparte (já estão refletidas no saldo).

## Estrutura

```
fic-fidc-dashboard/
├── app.py             # UI Streamlit (uploads + resumo + sanity check)
├── core.py            # Parsing, agregação por pessoa e geração do texto
├── config.py          # Sufixos societários usados ao agrupar nomes
├── requirements.txt
└── README.md
```

A separação `app.py` / `core.py` deixa a lógica testável sem subir o Streamlit.

## Rodando localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Envie o CSV do extrato e um ou mais XLSX das
carteiras de liquidez e copie o texto (o bloco tem ícone de copiar no canto
superior direito).

## Deploy no Streamlit Community Cloud

1. Suba este diretório como repositório no GitHub.
2. Acesse <https://share.streamlit.io> e logue com o GitHub.
3. **Create app** → selecione o repositório, branch `main`, arquivo `app.py`.
4. **Deploy**. Em ~1 min a URL fica no ar.

## Premissas / como cada número é calculado

- **Saldo em conta**: soma de todos os lançamentos do CSV (crédito − débito).
  Em geral fica perto de R$ 0, pois os fundos varrem o caixa para o fundo de
  liquidez diariamente.
- **Saldo nos fundos de liquidez**: lido da linha "Total:" / coluna "Saldo
  Líquido" de cada XLSX. Vários XLSX são somados (um fundo pode aplicar em mais
  de um fundo de liquidez). Há opção de sobrescrever manualmente.
- **Entrada / Saída / Líquido por pessoa**: considera só PIX/TED, agrupado por
  contraparte. Transferências internas entre contas do banco e tarifas são
  ignoradas na lista (mas as tarifas continuam refletidas no saldo).

## Observação

Como o app não classifica contrapartes, prestadores de serviço (administradora,
gestora, auditoria) e veículos de investimento também aparecem na lista, com
saída e líquido negativo. Isso é proposital — a lista mostra todo mundo que
movimentou dinheiro, sem julgar quem é quem.
