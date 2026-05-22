"""
Dashboard FIC FIDC — UI Streamlit.

Fluxo:
  1. Upload do extrato bancário (CSV) e de uma ou mais carteiras de fundo de
     liquidez (XLSX) — um fundo pode aplicar em vários fundos de liquidez.
  2. Identifica automaticamente cada contraparte das movimentações PIX/TED e
     soma entrada (créditos), saída (débitos) e líquido de cada uma.
  3. Mostra, à parte, o saldo (fundo de liquidez + conta).
  4. Gera o texto pronto para colar no WhatsApp.

Rodar localmente:  streamlit run app.py
"""
import streamlit as st

from core import (
    agregar_pessoas,
    computar_saldo_conta,
    fmt_brl,
    gerar_resumo,
    limpar_nome_fundo,
    parse_carteira,
    parse_extrato,
    somar_saldo_liquidez,
)

st.set_page_config(page_title="Resumo FIC FIDC", page_icon="📊", layout="centered")

st.title("📊 Resumo FIC FIDC para WhatsApp")
st.caption(
    "Upload do extrato bancário (CSV) e da(s) carteira(s) do fundo nos fundos "
    "de liquidez (XLSX). Cada contraparte é somada automaticamente e o resumo "
    "sai pronto para copiar."
)

extrato_file = st.file_uploader(
    "Extrato bancário (CSV)",
    type=["csv"],
    help="Arquivo `.CSV` exportado da conta do fundo, separador `;`.",
)
carteira_files = st.file_uploader(
    "Carteira(s) do fundo de liquidez (XLSX) — pode enviar mais de uma",
    type=["xlsx"],
    accept_multiple_files=True,
    help="Relatório 'Saldo de Aplicações de Cotistas'. Se o fundo aplica em "
         "vários fundos de liquidez, envie um XLSX de cada — os saldos são somados.",
)

if not extrato_file:
    st.info("⬆️ Envie ao menos o extrato bancário (CSV) para começar.")
    st.stop()

# --- Parsing ---
try:
    df = parse_extrato(extrato_file)
except Exception as e:
    st.error(f"Erro ao ler o extrato CSV: {e}")
    st.stop()

carteiras = []
for f in carteira_files or []:
    try:
        carteiras.append(parse_carteira(f))
    except Exception as e:
        st.warning(f"Não consegui ler a carteira '{f.name}': {e}")

# --- Saldos ---
saldo_conta = computar_saldo_conta(df)
saldo_liquidez = somar_saldo_liquidez(carteiras)

# --- Nome do fundo (default vindo do 1º XLSX que tiver cotista_nome) ---
nome_default = "FIC FIDC"
for c in carteiras:
    if c.get("cotista_nome"):
        nome_default = limpar_nome_fundo(c["cotista_nome"])
        break

# --- Agregação por pessoa ---
pessoas = agregar_pessoas(df)

with st.expander("⚙️ Ajustes", expanded=False):
    nome_fundo = st.text_input("Cabeçalho do resumo", value=nome_default)

    if not carteiras:
        st.warning("Nenhuma carteira XLSX enviada — informe o saldo manualmente.")
        saldo_liquidez = st.number_input(
            "Saldo total nos fundos de liquidez (R$)",
            value=0.0, step=0.01, format="%.2f",
        )
    else:
        sem_saldo = [c for c in carteiras if c.get("saldo_liquido") is None]
        if sem_saldo:
            st.warning(
                f"{len(sem_saldo)} carteira(s) sem saldo legível — confira abaixo."
            )
        if st.checkbox("Sobrescrever saldo dos fundos de liquidez", value=False):
            saldo_liquidez = st.number_input(
                "Saldo total nos fundos de liquidez (R$)",
                value=float(saldo_liquidez), step=0.01, format="%.2f",
            )

if pessoas.empty:
    st.warning("Nenhuma movimentação PIX/TED encontrada no extrato.")
    st.stop()

# --- Saída para WhatsApp ---
resumo = gerar_resumo(nome_fundo, saldo_conta + saldo_liquidez, pessoas)

st.subheader("📋 Copie e cole no WhatsApp")
st.code(resumo, language=None)  # st.code já tem botão de copiar embutido

# --- Detalhes / sanity check ---
with st.expander("🔍 Detalhes (sanity check)"):
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo em conta", fmt_brl(saldo_conta))
    c2.metric("Saldo fundos liquidez", fmt_brl(saldo_liquidez))
    c3.metric("Total consolidado", fmt_brl(saldo_conta + saldo_liquidez))

    st.write(
        f"**Período do extrato:** {df['dt_mov'].min():%d/%m/%Y} → "
        f"{df['dt_mov'].max():%d/%m/%Y} · {len(df)} lançamentos"
    )
    if carteiras:
        st.markdown("**Carteiras de liquidez carregadas:**")
        for c in carteiras:
            st.write(
                f"- {c.get('fundo_liquidez') or '—'} · cotista "
                f"{c.get('cotista_nome') or '—'} · "
                f"{fmt_brl(c.get('saldo_liquido') or 0.0)}"
            )

    st.markdown("**Movimentações por contraparte (PIX/TED):**")
    tabela = pessoas.copy()
    tabela.columns = ["Nome", "Entrada", "Saída", "Líquido"]
    st.dataframe(
        tabela.style.format({
            "Entrada": fmt_brl, "Saída": fmt_brl, "Líquido": fmt_brl,
        }),
        use_container_width=True,
        hide_index=True,
    )
