"""
Dashboard FIC FIDC — UI Streamlit.
Faz upload de extrato bancário (CSV) e carteira do fundo de liquidez (XLSX),
gera o resumo pronto para copiar no WhatsApp.

Rodar localmente:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from config import MESES_PT
from core import (
    computar_aportes,
    computar_gastos,
    computar_saldo_conta,
    fmt_brl,
    gerar_resumo,
    limpar_nome_fundo,
    parse_carteira,
    parse_extrato,
)

st.set_page_config(page_title="Resumo FIC FIDC", page_icon="📊", layout="centered")

st.title("📊 Resumo FIC FIDC para WhatsApp")
st.caption(
    "Faça upload do extrato bancário (CSV) e da posição do fundo no fundo "
    "de liquidez (XLSX). O resumo é gerado pronto para copiar e colar."
)

col1, col2 = st.columns(2)
with col1:
    extrato_file = st.file_uploader(
        "Extrato bancário (CSV)",
        type=["csv"],
        help="Arquivo `.CSV` exportado da conta do fundo, separador `;`.",
    )
with col2:
    carteira_file = st.file_uploader(
        "Carteira fundo de liquidez (XLSX)",
        type=["xlsx"],
        help="Relatório 'Saldo de Aplicações de Cotistas' com o fundo como cotista.",
    )

if not (extrato_file and carteira_file):
    st.info("⬆️ Aguardando upload dos dois arquivos.")
    st.stop()

# --- Parsing ---
try:
    df = parse_extrato(extrato_file)
    carteira = parse_carteira(carteira_file)
except Exception as e:
    st.error(f"Erro ao processar os arquivos: {e}")
    st.exception(e)
    st.stop()

# --- Ajustes (defaults vindos do XLSX) ---
nome_default = limpar_nome_fundo(carteira.get("cotista_nome"))

with st.expander("⚙️ Ajustes", expanded=False):
    nome_fundo = st.text_input("Cabeçalho do resumo", value=nome_default)

    saldo_lido = carteira.get("saldo_liquido")
    if saldo_lido is None:
        st.warning("Não consegui ler o Saldo Líquido do XLSX — informe abaixo.")
        saldo_liquidez = st.number_input(
            "Saldo no fundo de liquidez (R$)", value=0.0, step=0.01, format="%.2f"
        )
    else:
        override = st.checkbox("Sobrescrever saldo do fundo de liquidez", value=False)
        if override:
            saldo_liquidez = st.number_input(
                "Saldo no fundo de liquidez (R$)",
                value=float(saldo_lido), step=0.01, format="%.2f",
            )
        else:
            saldo_liquidez = float(saldo_lido)

    # Seletor de mês de referência
    meses = (
        df["dt_mov"].dt.to_period("M")
        .drop_duplicates()
        .sort_values(ascending=False)
    )
    opcoes_mes = [(p.year, p.month) for p in meses]
    rotulos = [f"{MESES_PT[m]}/{a}" for a, m in opcoes_mes]
    idx = st.selectbox(
        "Mês para 'Gastos do fundo em <mês>'",
        options=range(len(opcoes_mes)),
        format_func=lambda i: rotulos[i],
        index=0,
    )
    mes_ref = opcoes_mes[idx]

# --- Cálculos ---
saldo_conta = computar_saldo_conta(df)
aportes = computar_aportes(df)
gastos, mes_ref = computar_gastos(df, mes_ref)

# --- Saída para WhatsApp ---
resumo = gerar_resumo(nome_fundo, saldo_conta, saldo_liquidez, aportes, gastos, mes_ref)

st.subheader("📋 Copie e cole no WhatsApp")
# st.code já vem com botão de copiar embutido (ícone no canto superior direito)
st.code(resumo, language=None)

# --- Detalhes / sanity check ---
with st.expander("🔍 Detalhes (sanity check)"):
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo em conta", fmt_brl(saldo_conta))
    c2.metric("Saldo fundo liquidez", fmt_brl(saldo_liquidez))
    c3.metric("Total consolidado", fmt_brl(saldo_conta + saldo_liquidez))

    st.write(
        f"**Período do extrato:** {df['dt_mov'].min():%d/%m/%Y} → "
        f"{df['dt_mov'].max():%d/%m/%Y} · {len(df)} lançamentos"
    )
    st.write(f"**Fundo de liquidez (do XLSX):** {carteira.get('fundo_liquidez') or '—'}")
    st.write(f"**Cotista (do XLSX):** {carteira.get('cotista_nome') or '—'}")

    st.markdown("**Aportes por cotista**")
    aportes_df = pd.DataFrame(aportes).T[["entrada", "saida", "liquido"]]
    aportes_df.columns = ["Entrada", "Saída", "Líquido"]
    st.dataframe(aportes_df.style.format(fmt_brl), use_container_width=True)

    st.markdown("**Gastos por categoria**")
    gastos_df = pd.DataFrame(gastos).T[["debitos", "creditos", "liquido", "mes"]]
    gastos_df.columns = [
        "Débitos", "Créditos/Reemb.", "Líquido",
        f"No mês ({MESES_PT[mes_ref[1]]}/{mes_ref[0]})",
    ]
    st.dataframe(gastos_df.style.format(fmt_brl), use_container_width=True)
