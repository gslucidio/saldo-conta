"""
Lógica pura (parsing + cálculos + geração de texto) do dashboard FIC FIDC.
Sem dependência de Streamlit — facilita testes e reuso.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import IO

import pandas as pd
from openpyxl import load_workbook

from config import COTISTAS, DESPESAS, ABREV, MESES_PT


# =============================================================================
# Helpers de formatação
# =============================================================================

def fmt_brl(v: float) -> str:
    """Formata número como 'R$ 1.234,56' (padrão brasileiro)."""
    # Normaliza signed zero (-0.0 → 0.0) para evitar 'R$ -0,00'
    if v == 0:
        v = 0.0
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================================
# Parsers
# =============================================================================

def _ler_csv_bytes(data: bytes) -> pd.DataFrame:
    """Lê CSV semicolon-separated, tentando múltiplas codificações."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(BytesIO(data), sep=";", encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível decodificar o CSV.")


def parse_extrato(file: IO[bytes] | str) -> pd.DataFrame:
    """
    Lê o extrato bancário (CSV) e devolve um DataFrame normalizado,
    com coluna `valor_assinado` (positivo p/ crédito, negativo p/ débito).

    Aceita arquivo (file-like) ou caminho.
    """
    if isinstance(file, str):
        with open(file, "rb") as f:
            data = f.read()
    else:
        data = file.read()
    df = _ler_csv_bytes(data)

    df["dt_mov"] = pd.to_datetime(df["dt_mov"], format="%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["valor"])
    df["valor_assinado"] = df.apply(
        lambda r: r["valor"] if r["fl_debito_credito"] == "C" else -r["valor"],
        axis=1,
    )
    for col in ("ds_historico", "ds_complemento"):
        df[col] = df[col].fillna("").astype(str)
    return df.sort_values("dt_mov").reset_index(drop=True)


def parse_carteira(file: IO[bytes] | str) -> dict:
    """
    Lê o XLSX 'Saldo de Aplicações de Cotistas'.

    Estratégia:
      1. Localiza a coluna com cabeçalho 'Saldo Líquido'.
      2. Captura o nome do fundo de liquidez na linha 'Carteira:'.
      3. Captura o nome do cotista (regex no padrão '<num> - NOME - Aberto - ...').
      4. Lê o Saldo Líquido na linha 'Total:'.

    Retorna {saldo_liquido, fundo_liquidez, cotista_nome}.
    Qualquer campo pode vir None se o layout for diferente.
    """
    wb = load_workbook(file, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    saldo_col = None
    fundo_liquidez = None
    cotista_nome = None
    saldo_liquido = None

    for row in rows:
        if not row:
            continue
        for j, cell in enumerate(row):
            if cell is None:
                continue
            s = str(cell).strip()

            if saldo_col is None and ("Saldo Líquido" in s or "Saldo Liquido" in s):
                saldo_col = j

            if fundo_liquidez is None and "Carteira:" in s:
                for k in range(j + 1, len(row)):
                    nxt = row[k]
                    if nxt is None:
                        continue
                    nxt_s = str(nxt).strip()
                    if nxt_s and "CNPJ" not in nxt_s:
                        fundo_liquidez = nxt_s
                        break

            if cotista_nome is None:
                m = re.match(r"^\s*\d+\s*-\s*(.+?)\s*-\s*(Aberto|Fechado)", s)
                if m:
                    cotista_nome = m.group(1).strip()

            if saldo_liquido is None and s.startswith("Total:") and saldo_col is not None:
                if len(row) > saldo_col and row[saldo_col] is not None:
                    try:
                        saldo_liquido = float(row[saldo_col])
                    except (ValueError, TypeError):
                        pass

    return {
        "saldo_liquido": saldo_liquido,
        "fundo_liquidez": fundo_liquidez,
        "cotista_nome": cotista_nome,
    }


# =============================================================================
# Classificadores
# =============================================================================

def _classifica_cotista(complemento: str) -> str | None:
    comp = (complemento or "").upper()
    for nome, padroes in COTISTAS.items():
        for p in padroes:
            if p.upper() in comp:
                return nome
    return None


def _classifica_despesa(row) -> str | None:
    hist = (row["ds_historico"] or "").upper()
    comp = (row["ds_complemento"] or "").upper()
    for nome, padroes, onde in DESPESAS:
        alvo = comp if onde == "complemento" else hist
        for p in padroes:
            if p.upper() in alvo:
                return nome
    return None


# =============================================================================
# Cálculos
# =============================================================================

def computar_saldo_conta(df: pd.DataFrame) -> float:
    """Saldo final em conta-corrente = soma de todos os valores assinados."""
    return float(df["valor_assinado"].sum())


def computar_aportes(df: pd.DataFrame) -> dict:
    """
    Movimentos de cotistas via PIX/TED/TEC.
    Transferências internas entre contas do banco são ignoradas.
    Retorna {cotista: {entrada, saida, liquido}}.
    """
    sub = df.copy()
    sub["cotista"] = sub["ds_complemento"].apply(_classifica_cotista)
    sub = sub[sub["cotista"].notna()]
    mask_movs = sub["ds_historico"].str.contains(
        r"PIX|TED|TEC", case=False, regex=True
    )
    sub = sub[mask_movs]

    out = {}
    for nome in COTISTAS:
        s = sub[sub["cotista"] == nome]
        entrada = float(s.loc[s["valor_assinado"] > 0, "valor_assinado"].sum())
        saida = float(-s.loc[s["valor_assinado"] < 0, "valor_assinado"].sum())
        out[nome] = {
            "entrada": entrada,
            "saida": saida,
            "liquido": entrada - saida,
        }
    return out


def computar_gastos(df: pd.DataFrame, mes_ref: tuple | None = None):
    """
    Despesas por categoria, total e do mês de referência.
    Retorna (gastos, mes_ref) onde gastos = {categoria: {debitos, creditos, liquido, mes}}.
    """
    sub = df.copy()
    sub["categoria"] = sub.apply(_classifica_despesa, axis=1)
    sub = sub[sub["categoria"].notna()]

    if mes_ref is None and len(df) > 0:
        ult = df["dt_mov"].max()
        mes_ref = (ult.year, ult.month)

    gastos = {}
    for categoria, _, _ in DESPESAS:
        s = sub[sub["categoria"] == categoria]
        debitos = float(-s.loc[s["valor_assinado"] < 0, "valor_assinado"].sum())
        creditos = float(s.loc[s["valor_assinado"] > 0, "valor_assinado"].sum())
        liquido = debitos - creditos

        liquido_mes = 0.0
        if mes_ref:
            sm = s[
                (s["dt_mov"].dt.year == mes_ref[0])
                & (s["dt_mov"].dt.month == mes_ref[1])
            ]
            d_mes = float(-sm.loc[sm["valor_assinado"] < 0, "valor_assinado"].sum())
            c_mes = float(sm.loc[sm["valor_assinado"] > 0, "valor_assinado"].sum())
            liquido_mes = d_mes - c_mes

        gastos[categoria] = {
            "debitos": debitos,
            "creditos": creditos,
            "liquido": liquido,
            "mes": liquido_mes,
        }
    return gastos, mes_ref


# =============================================================================
# Geração do texto para WhatsApp
# =============================================================================

def gerar_resumo(
    nome_fundo: str,
    saldo_conta: float,
    saldo_liquidez: float,
    aportes: dict,
    gastos: dict,
    mes_ref: tuple | None,
) -> str:
    """Monta o texto final pronto para colar no WhatsApp."""
    out = [nome_fundo]
    out.append(
        f"- Saldo fundo de liquidez + saldo em conta: "
        f"{fmt_brl(saldo_conta + saldo_liquidez)}"
    )

    # Aportes — apenas cotistas com movimento, ordenados por líquido desc
    out.append("- Aportes por cotista:")
    cot_ord = sorted(
        [(n, d) for n, d in aportes.items() if d["entrada"] or d["saida"]],
        key=lambda x: x[1]["liquido"],
        reverse=True,
    )
    for nome, d in cot_ord:
        out.append(f"{nome}:")
        out.append(f"Entrada: {fmt_brl(d['entrada'])}")
        out.append(f"Saída: {fmt_brl(d['saida'])}")
        out.append(f"Líquido: {fmt_brl(d['liquido'])}")

    # Gastos do mês
    if mes_ref:
        total_mes = sum(g["mes"] for g in gastos.values())
        abrev_mes, vistos = [], set()
        for cat, g in gastos.items():
            if g["mes"] <= 0:
                continue
            ab = ABREV.get(cat)
            if ab and ab not in vistos:
                abrev_mes.append(ab)
                vistos.add(ab)
        sufixo = f" ({', '.join(abrev_mes)})" if abrev_mes else ""
        out.append(
            f"- Gastos do fundo em {MESES_PT[mes_ref[1]]}: "
            f"{fmt_brl(total_mes)}{sufixo}"
        )

    # Gastos desde o início
    total_geral = sum(g["liquido"] for g in gastos.values())
    out.append(f"- Gastos do fundo desde o início: {fmt_brl(total_geral)}")

    # Sorted: líquido desc, mas Tarifas vão pro fim
    cats_ord = sorted(
        [(c, g) for c, g in gastos.items() if g["liquido"] > 0],
        key=lambda x: (x[0].startswith("Tarifas"), -x[1]["liquido"]),
    )
    for cat, g in cats_ord:
        if g["creditos"] > 0:
            out.append(
                f"{cat}: Débitos: {fmt_brl(g['debitos'])}; "
                f"Reembolsos/Créditos: {fmt_brl(g['creditos'])}; "
                f"Líquido: {fmt_brl(g['liquido'])}"
            )
        else:
            out.append(f"{cat}: {fmt_brl(g['liquido'])}")

    return "\n".join(out)


def limpar_nome_fundo(nome_bruto: str | None) -> str:
    """Converte 'FIC FIDC ELANTRA RL' → 'FIC FIDC Elantra'."""
    if not nome_bruto:
        return "FIC FIDC"
    s = nome_bruto.title()
    s = re.sub(r"\bFic Fidc\b", "FIC FIDC", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRl\b\s*$", "", s).strip()
    return s
