"""
simulador_pesos.py
Simula o impacto de pesos nas questões de qualidade SEM rodar a IA novamente.
Lê o consolidado_completo.csv já gerado e mostra quais artigos mudariam de status.

Como usar:
  1. Ajuste PESOS_SIMULACAO abaixo com os pesos que quiser testar
  2. Execute: python simulador_pesos.py
  3. Veja o relatório e o arquivo simulacao_resultado.xlsx gerado
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule

# ============================================================
# CONFIGURAÇÕES — ajuste aqui
# ============================================================

# CSV gerado pelo qualidade.py (o mais recente)
_base = Path(__file__).resolve().parent / "ResultadoQualidade"
_ultima = sorted(_base.glob("*/consolidado_completo.csv"), reverse=True)
if not _ultima:
    raise FileNotFoundError(f"Nenhum consolidado_completo.csv encontrado em {_base}")
CSV_ENTRADA = str(_ultima[0])

SCORE_CORTE = 6.0   # mesmo corte do qualidade.py

# Filtra o relatorio/Excel pra mostrar so artigos com score SIMULADO >= esse valor.
# None = sem filtro (mostra todos)
# Exemplos: 7.0, 8.0, 6.5
FILTRO_SCORE_MINIMO = None

# Pesos que você quer testar — mude à vontade e rode de novo
# 1.0 = padrão | 2.0 = dobro de importância | 0.5 = metade
PESOS_SIMULACAO = {
    "Q1":  1.0,   # Objetivos claramente especificados
    "Q2":  2.0,   # Metodologia ágil no contexto da prototipação  << PESO 2
    "Q3":  1.0,   # Metodologia do estudo definida claramente
    "Q4":  1.0,   # Avaliação com usuários reais
    "Q5":  3.0,   # Comparação com prototipação tradicional       << PESO 3
    "Q6":  1.0,   # Métricas de avaliação
    "Q7":  1.0,   # Contribuição prática (diretriz, framework etc.)
    "Q8":  1.0,   # Limitações e benefícios claros
    "Q9":  3.0,   # Etapas do processo de prototipação            << PESO 3
    "Q10": 2.0,   # Processo de uso da IA / modelo utilizado      << PESO 2
}
# ============================================================


PONTOS = {"SIM": 1.0, "PARCIAL": 0.5, "NÃO": 0.0, "NAO": 0.0}


# ── helpers de estilo ──────────────────────────────────────────────────────────
def _fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def _font(bold=False, color="000000", size=10, name="Arial"):
    return Font(bold=bold, color=color, size=size, name=name)

def _border_thin():
    s = Side(style="thin", color="CCCCCC")
    return Border(left=s, right=s, top=s, bottom=s)

def _center():
    return Alignment(horizontal="center", vertical="center", wrap_text=True)

def _left():
    return Alignment(horizontal="left", vertical="center", wrap_text=True)


def _salvar_excel_formatado(df: pd.DataFrame, caminho: Path,
                            pesos: dict, score_corte: float):
    colunas_base = ["arquivo", "base", "titulo",
                    "q1","q2","q3","q4","q5","q6","q7","q8","q9","q10",
                    "score_original", "score_simulado",
                    "aprovado_original", "aprovado_simulado", "mudanca"]
    colunas = [c for c in colunas_base if c in df.columns]
    dados = df[colunas].copy().reset_index(drop=True)

    wb = Workbook()

    # ── Aba 1: Resultado ───────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Resultado"
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 32

    # cabeçalhos bonitos
    CABECALHOS = {
        "arquivo":           "Arquivo",
        "base":              "Base",
        "titulo":            "Titulo",
        "q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4", "q5": "Q5",
        "q6": "Q6", "q7": "Q7", "q8": "Q8", "q9": "Q9", "q10": "Q10",
        "score_original":    "Score\nOriginal",
        "score_simulado":    "Score\nSimulado",
        "aprovado_original": "Aprovado\nOriginal",
        "aprovado_simulado": "Aprovado\nSimulado",
        "mudanca":           "Mudanca",
    }

    LARGURAS = {
        "arquivo": 38, "base": 10, "titulo": 50,
        "q1":6,"q2":6,"q3":6,"q4":6,"q5":6,
        "q6":6,"q7":6,"q8":6,"q9":6,"q10":6,
        "score_original":10,"score_simulado":10,
        "aprovado_original":10,"aprovado_simulado":10,
        "mudanca":22,
    }

    HDR_FILL   = _fill("1F3864")   # azul escuro
    HDR_FILL_Q = _fill("2E5F9E")   # azul médio para colunas Q com peso != 1
    HDR_FONT   = _font(bold=True, color="FFFFFF", size=9)

    for ci, col in enumerate(colunas, start=1):
        cel = ws.cell(row=1, column=ci, value=CABECALHOS.get(col, col.upper()))
        q_key = col.upper()
        if col.startswith("q") and pesos.get(q_key, 1.0) != 1.0:
            cel.fill = HDR_FILL_Q
        else:
            cel.fill = HDR_FILL
        cel.font = HDR_FONT
        cel.alignment = _center()
        cel.border = _border_thin()
        ws.column_dimensions[get_column_letter(ci)].width = LARGURAS.get(col, 12)

    # dados
    COR_SIM     = "D9EAD3"   # verde claro → SIM
    COR_PARCIAL = "FFF2CC"   # amarelo → PARCIAL
    COR_NAO     = "FCE5CD"   # laranja claro → NÃO
    COR_SALVO   = "B7E1CD"   # verde → salvo
    COR_REMOVIDO= "F4CCCC"   # vermelho → removido

    for ri, (_, row) in enumerate(dados.iterrows(), start=2):
        # zebra
        row_fill = _fill("F8F9FA") if ri % 2 == 0 else _fill("FFFFFF")
        for ci, col in enumerate(colunas, start=1):
            val = row[col]
            cel = ws.cell(row=ri, column=ci)
            cel.border = _border_thin()
            cel.font   = _font(size=9)

            # formatação por tipo de coluna
            if col in ("q1","q2","q3","q4","q5","q6","q7","q8","q9","q10"):
                v = str(val).strip().upper()
                cel.value     = v
                cel.alignment = _center()
                if v == "SIM":
                    cel.fill = _fill(COR_SIM)
                    cel.font = _font(bold=True, color="274E13", size=9)
                elif v == "PARCIAL":
                    cel.fill = _fill(COR_PARCIAL)
                    cel.font = _font(bold=True, color="7D6608", size=9)
                elif v in ("NÃO", "NAO"):
                    cel.fill = _fill(COR_NAO)
                    cel.font = _font(color="7F0000", size=9)
                else:
                    cel.fill = row_fill

            elif col in ("score_original", "score_simulado"):
                try:
                    num = float(val)
                except (ValueError, TypeError):
                    num = 0.0
                cel.value     = num
                cel.number_format = "0.00"
                cel.alignment = _center()
                if num >= score_corte:
                    cel.fill = _fill("C6EFCE")
                    cel.font = _font(bold=True, color="276221", size=9)
                else:
                    cel.fill = _fill("FFC7CE")
                    cel.font = _font(bold=True, color="9C0006", size=9)

            elif col in ("aprovado_original", "aprovado_simulado"):
                v = str(val).strip().upper()
                cel.value     = v
                cel.alignment = _center()
                if v == "SIM":
                    cel.fill = _fill(COR_SIM)
                    cel.font = _font(bold=True, color="274E13", size=9)
                else:
                    cel.fill = _fill(COR_REMOVIDO)
                    cel.font = _font(bold=True, color="7F0000", size=9)

            elif col == "mudanca":
                v = str(val)
                cel.value     = v
                cel.alignment = _center()
                if v.startswith("++"):
                    cel.fill = _fill(COR_SALVO)
                    cel.font = _font(bold=True, color="1A4731", size=9)
                elif v.startswith("--"):
                    cel.fill = _fill(COR_REMOVIDO)
                    cel.font = _font(bold=True, color="7F0000", size=9)
                else:
                    cel.fill = row_fill

            elif col == "titulo":
                cel.value     = str(val)
                cel.alignment = _left()
                cel.fill      = row_fill

            else:
                cel.value     = str(val)
                cel.alignment = _left()
                cel.fill      = row_fill

    # ── Aba 2: Resumo de Pesos ────────────────────────────────────────────────
    ws2 = wb.create_sheet("Pesos Usados")
    ws2.column_dimensions["A"].width = 8
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 28

    for ci, txt in enumerate(["Questao", "Peso", "Impacto"], start=1):
        c = ws2.cell(row=1, column=ci, value=txt)
        c.fill = _fill("1F3864"); c.font = _font(bold=True, color="FFFFFF", size=10)
        c.alignment = _center(); c.border = _border_thin()

    total_pesos = sum(pesos.values())
    for ri, (q, p) in enumerate(pesos.items(), start=2):
        pct = p / total_pesos * 100
        barra = "#" * int(p * 6)
        ws2.cell(row=ri, column=1, value=q).alignment = _center()
        ws2.cell(row=ri, column=2, value=p).number_format = "0.0"
        ws2.cell(row=ri, column=2).alignment = _center()
        ws2.cell(row=ri, column=3, value=f"{pct:.1f}%  {barra}").alignment = _left()
        for ci in range(1, 4):
            c = ws2.cell(row=ri, column=ci)
            c.border = _border_thin()
            c.font = _font(size=10)
            if p != 1.0:
                c.fill = _fill("D0E4FF")
                c.font = _font(bold=True, size=10, color="1A4731" if p > 1 else "7F0000")
            else:
                c.fill = _fill("F8F9FA") if ri % 2 == 0 else _fill("FFFFFF")

    ws2.freeze_panes = "A2"

    wb.save(str(caminho))


def calcular_score_ponderado(row: pd.Series, pesos: dict) -> float:
    total_pond = 0.0
    total_peso = 0.0
    for i in range(1, 11):
        q = f"q{i}"
        peso = pesos.get(f"Q{i}", 1.0)
        val = str(row.get(q, "NÃO")).strip().upper()
        total_pond += PONTOS.get(val, 0.0) * peso
        total_peso += peso
    if total_peso == 0:
        return 0.0
    return round((total_pond / total_peso) * 10.0, 2)


def main():
    print(f"Lendo: {CSV_ENTRADA}\n")
    df = pd.read_csv(CSV_ENTRADA, dtype=str, encoding="utf-8-sig").fillna("")

    # Score original (sem peso — todos iguais a 1.0)
    pesos_neutros = {f"Q{i}": 1.0 for i in range(1, 11)}
    df["score_original"] = df.apply(lambda r: calcular_score_ponderado(r, pesos_neutros), axis=1)

    # Score com os pesos da simulação
    df["score_simulado"] = df.apply(lambda r: calcular_score_ponderado(r, PESOS_SIMULACAO), axis=1)

    df["aprovado_original"] = df["score_original"].apply(lambda s: "SIM" if s >= SCORE_CORTE else "NÃO")
    df["aprovado_simulado"] = df["score_simulado"].apply(lambda s: "SIM" if s >= SCORE_CORTE else "NÃO")

    df["mudanca"] = df.apply(
        lambda r: (
            "++ SALVO (era reprovado)"    if r["aprovado_original"] == "NÃO" and r["aprovado_simulado"] == "SIM" else
            "-- REMOVIDO (era aprovado)"  if r["aprovado_original"] == "SIM" and r["aprovado_simulado"] == "NÃO" else
            "sem mudanca"
        ), axis=1
    )

    # ---- Relatorio no terminal ----
    print("=" * 70)
    print("PESOS USADOS NA SIMULACAO")
    print("=" * 70)
    total_pesos = sum(PESOS_SIMULACAO.values())
    for q, p in PESOS_SIMULACAO.items():
        barra = "#" * int(p * 4)
        destaque = " << PESO DIFERENTE" if p != 1.0 else ""
        print(f"  {q:4s} | peso {p:.1f} | {barra}{destaque}")
    print(f"\n  Score maximo possivel: 10.0 (sempre normalizado)")
    print(f"  Corte de aprovacao  : {SCORE_CORTE}")

    salvos   = df[df["mudanca"].str.startswith("++")]
    removidos= df[df["mudanca"].str.startswith("--")]

    print(f"\n{'=' * 70}")
    print("IMPACTO DA SIMULACAO")
    print(f"{'=' * 70}")
    total = len(df)
    ap_orig = (df["aprovado_original"] == "SIM").sum()
    ap_sim  = (df["aprovado_simulado"] == "SIM").sum()
    print(f"  Total de artigos          : {total}")
    print(f"  Aprovados ANTES dos pesos : {ap_orig}  ({ap_orig/total*100:.1f}%)")
    print(f"  Aprovados DEPOIS dos pesos: {ap_sim}  ({ap_sim/total*100:.1f}%)")
    print(f"  Artigos SALVOS pelos pesos   : {len(salvos)}")
    print(f"  Artigos REMOVIDOS pelos pesos: {len(removidos)}")

    # ---- Aplica filtro de score minimo se configurado ----
    if FILTRO_SCORE_MINIMO is not None:
        df_filtrado = df[df["score_simulado"] >= FILTRO_SCORE_MINIMO].copy()
        print(f"\n  [FILTRO] score_simulado >= {FILTRO_SCORE_MINIMO}")
        print(f"  Artigos que passam no filtro: {len(df_filtrado)} de {total}")
    else:
        df_filtrado = df.copy()

    salvos_filtrados   = salvos[salvos["score_simulado"] >= (FILTRO_SCORE_MINIMO or 0)]
    removidos_filtrados= removidos[removidos["score_simulado"] >= (FILTRO_SCORE_MINIMO or 0)]

    if not salvos_filtrados.empty:
        print(f"\n{'-' * 70}")
        print("++ ARTIGOS QUE SERIAM SALVOS (reprovados -> aprovados):")
        print(f"{'-' * 70}")
        for _, r in salvos_filtrados.iterrows():
            delta = r["score_simulado"] - r["score_original"]
            print(f"  {r.get('arquivo', r.get('titulo','?'))[:60]}")
            print(f"    Score: {r['score_original']:.2f} -> {r['score_simulado']:.2f}  (+{delta:.2f})")
            for i in range(1, 11):
                q = f"q{i}"
                val = str(r.get(q, "")).strip().upper()
                peso = PESOS_SIMULACAO.get(f"Q{i}", 1.0)
                tag = f" [peso {peso}x]" if peso != 1.0 else ""
                print(f"    {f'Q{i}':4s}: {val}{tag}")
            print()

    if not removidos_filtrados.empty:
        print(f"\n{'-' * 70}")
        print("-- ARTIGOS QUE SERIAM REMOVIDOS (aprovados -> reprovados):")
        print(f"{'-' * 70}")
        for _, r in removidos_filtrados.iterrows():
            delta = r["score_simulado"] - r["score_original"]
            print(f"  {r.get('arquivo', r.get('titulo','?'))[:60]}")
            print(f"    Score: {r['score_original']:.2f} -> {r['score_simulado']:.2f}  ({delta:.2f})")
            print()

    # ---- Salva Excel formatado ----
    ts     = datetime.now().strftime("%H%M%S")
    sufixo = f"_filtro{FILTRO_SCORE_MINIMO}" if FILTRO_SCORE_MINIMO is not None else ""
    saida  = Path(CSV_ENTRADA).parent / f"simulacao_resultado{sufixo}_{ts}.xlsx"
    _salvar_excel_formatado(df_filtrado, saida, PESOS_SIMULACAO, SCORE_CORTE)

    print(f"\n{'=' * 70}")
    if FILTRO_SCORE_MINIMO is not None:
        print(f"Excel salvo com FILTRO >= {FILTRO_SCORE_MINIMO}: {saida}")
    else:
        print(f"Excel salvo (todos os artigos): {saida}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
