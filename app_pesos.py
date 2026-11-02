"""
app_pesos.py
Execute com: streamlit run app_pesos.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Simulador de Pesos — RSL", page_icon="📊", layout="wide")

# ── Dados ──────────────────────────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    base = Path(__file__).resolve().parent / "ResultadoQualidade"
    arquivos = sorted(base.glob("*/consolidado_completo.csv"), reverse=True)
    if not arquivos:
        return None, None
    df = pd.read_csv(arquivos[0], dtype=str, encoding="utf-8-sig").fillna("")
    return df, str(arquivos[0])

PONTOS = {"SIM": 1.0, "PARCIAL": 0.5, "NÃO": 0.0, "NAO": 0.0}

DESCRICOES = {
    "Q1":  "Objetivos claramente especificados",
    "Q2":  "Metodologia ágil no contexto da prototipação",
    "Q3":  "Metodologia do estudo definida claramente",
    "Q4":  "Avaliação com usuários reais",
    "Q5":  "Comparação com prototipação tradicional",
    "Q6":  "Métricas de avaliação",
    "Q7":  "Contribuição prática (diretriz, framework etc.)",
    "Q8":  "Limitações e benefícios claros",
    "Q9":  "Etapas do processo de prototipação",
    "Q10": "Processo de uso da IA / modelo utilizado",
}

def calcular_score(row, pesos, modo):
    total_pond = sum(PONTOS.get(str(row.get(f"q{i}", "NÃO")).strip().upper(), 0.0) * pesos[f"Q{i}"]
                     for i in range(1, 11))
    total_peso = sum(pesos[f"Q{i}"] for i in range(1, 11))
    if modo == "overleaf":
        # Denominador fixo = 10 questões (não divide por sum(pesos))
        # Com pesos todos 1.0 → igual à ponderada. Com pesos altos → pode passar de 10.
        return round(total_pond, 2)
    return round((total_pond / total_peso) * 10.0, 2) if total_peso else 0.0

def imprimir_metricas_por_questao(df):
    """Imprime no terminal apenas a média de pontos por questão."""
    print("\n" + "="*80)
    print("NOTA MÉDIA POR QUESTÃO DE QUALIDADE")
    print("="*80)
    print(f"{'Questão':<12} {'Descrição':<50} {'Média':<8}")
    print("-" * 80)
    
    for i in range(1, 11):
        q_col = f"q{i}"
        valores = df[q_col].str.strip().str.upper().map(lambda x: PONTOS.get(x, 0.0))
        media = valores.mean()
        desc = DESCRICOES[f"Q{i}"][:47]
        print(f"Q{i:<11} {desc:<50} {media:>6.2f}")
    
    print("="*80 + "\n")

# ── Cabeçalho ──────────────────────────────────────────────────────────────────
st.title("📊 Simulador de Pesos — Qualidade da RSL")

df_raw, caminho = carregar_dados()
if df_raw is None:
    st.error("Nenhum consolidado_completo.csv encontrado.")
    st.stop()

st.caption(f"Fonte: `{caminho}`  —  **{len(df_raw)} artigos** carregados")

# ── Seletor de modo ────────────────────────────────────────────────────────────
col_m1, col_m2 = st.columns([2, 3])
with col_m1:
    modo = st.radio(
        "**Modo de cálculo:**",
        ["ponderada", "overleaf"],
        format_func=lambda x: "Média Ponderada" if x == "ponderada" else "Média Overleaf",
        horizontal=True,
        key="modo",
    )
with col_m2:
    if modo == "ponderada":
        st.info("**Ponderada:** `(Σ pontos × peso) / Σ pesos × 10`  — score sempre 0–10")
    else:
        st.warning("**Overleaf:** `Σ (pontos × peso) / 10`  — escala muda conforme os pesos")

st.divider()

# ── Lê pesos do session_state ANTES de renderizar a sidebar
# (necessário pra calcular o range do slider de corte)
pesos_atuais = {q: float(st.session_state.get(q, 1.0)) for q in DESCRICOES}

# Calcula range real dos scores com os pesos atuais
df_pre = df_raw.copy()
df_pre["_sim"] = df_pre.apply(lambda r: calcular_score(r, pesos_atuais, modo), axis=1)
_s_min = float(df_pre["_sim"].min())
_s_max = float(df_pre["_sim"].max())
if _s_min >= _s_max:
    _s_max = _s_min + 0.01
_s_step    = max(round((_s_max - _s_min) / 40, 2), 0.01)
_s_default = round(_s_min + (_s_max - _s_min) * 0.6, 2)

# ── Sidebar (UM único bloco) ────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚖️ Pesos das Questões")
    st.caption("Arraste para ajustar o peso de cada questão.")
    st.divider()

    st.markdown(f"**🎯 Nota de corte** `(range: {_s_min:.2f} – {_s_max:.2f})`")
    score_corte = st.slider(
        "corte_label",
        min_value=_s_min,
        max_value=_s_max,
        value=st.session_state.get(f"corte_{modo}", _s_default),
        step=_s_step,
        key=f"corte_{modo}",
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Peso por questão:**")

    pesos = {}
    for q, desc in DESCRICOES.items():
        pesos[q] = st.slider(
            f"{q} — {desc}",
            min_value=0.0, max_value=5.0, value=1.0, step=0.5,
            key=q,
        )

    st.divider()
    def _resetar():
        for q in DESCRICOES:
            st.session_state[q] = 1.0

    st.button("🔄 Resetar pesos para 1.0", on_click=_resetar)
    
    st.divider()
    def _imprimir():
        imprimir_metricas_por_questao(df_raw)
    
    st.button("📋 Printar Métricas", on_click=_imprimir)

# ── Cálculo final com os valores reais dos widgets ─────────────────────────────
df = df_raw.copy()
pesos_neutros = {f"Q{i}": 1.0 for i in range(1, 11)}

df["score_original"] = df.apply(lambda r: calcular_score(r, pesos_neutros, "ponderada"), axis=1)
df["score_simulado"]  = df.apply(lambda r: calcular_score(r, pesos, modo), axis=1)

CORTE_ORIG = 6.0
df["aprovado_orig"] = df["score_original"] >= CORTE_ORIG
df["aprovado_sim"]  = df["score_simulado"]  >= score_corte

total     = len(df)
ap_orig   = int(df["aprovado_orig"].sum())
ap_sim    = int(df["aprovado_sim"].sum())
salvos    = int((~df["aprovado_orig"] &  df["aprovado_sim"]).sum())
removidos = int(( df["aprovado_orig"] & ~df["aprovado_sim"]).sum())

# ── Métricas ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de artigos",     total)
c2.metric("Aprovados (original)", ap_orig, help=f"Ponderada neutra, corte {CORTE_ORIG}")
c3.metric("Aprovados (simulado)", ap_sim,  delta=ap_sim - ap_orig, delta_color="normal")
c4.metric("🟢 Salvos pelos pesos",    salvos,    delta=f"+{salvos}",    delta_color="normal")
c5.metric("🔴 Removidos pelos pesos", removidos, delta=f"-{removidos}", delta_color="inverse")

st.divider()

# ── Debug ──────────────────────────────────────────────────────────────────────
with st.expander("🔧 Debug — ver cálculo de um artigo"):
    artigos_lista = df["arquivo"].unique().tolist()
    art_sel = st.selectbox("Artigo", artigos_lista, key="debug_artigo")
    row_debug = df[df["arquivo"] == art_sel].iloc[0]
    PONTOS_D = {"SIM": 1.0, "PARCIAL": 0.5, "NÃO": 0.0, "NAO": 0.0}
    rows_debug = []
    total_p, total_w = 0.0, 0.0
    for i in range(1, 11):
        val = str(row_debug.get(f"q{i}", "NÃO")).strip().upper()
        pt  = PONTOS_D.get(val, 0.0)
        w   = pesos[f"Q{i}"]
        rows_debug.append({"Q": f"Q{i}", "Resposta": val, "Pontos": pt, "Peso": w, "Ponderado": round(pt * w, 4)})
        total_p += pt * w
        total_w += w
    st.dataframe(pd.DataFrame(rows_debug), hide_index=True)
    score_calc = round((total_p / total_w) * 10, 2) if total_w else 0.0
    st.write(f"**total_pond = {total_p}  /  total_peso = {total_w}  × 10 = {score_calc}**")
    st.write(f"score_simulado na tabela: **{float(row_debug['score_simulado']):.2f}**")
    st.write(f"Pesos lidos dos sliders: {pesos}")

st.divider()

# ── Gráficos ───────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Distribuição dos Scores")
    st.bar_chart(pd.DataFrame({
        "Original": df["score_original"],
        "Simulado": df["score_simulado"],
    }).apply(lambda c: c.value_counts().sort_index()))
with col_b:
    st.subheader("Peso atual por questão")
    st.bar_chart(pd.DataFrame({"Peso": list(pesos.values())}, index=list(pesos.keys())))

st.divider()

# ── Helpers de cor ─────────────────────────────────────────────────────────────
def colorir_q(val):
    v = str(val).strip().upper()
    if v == "SIM":           return "background-color:#c6efce;color:#276221;font-weight:bold"
    if v == "PARCIAL":       return "background-color:#fff2cc;color:#7d6608;font-weight:bold"
    if v in ("NÃO","NAO"):   return "background-color:#fce5cd;color:#7f0000"
    return ""

def colorir_score(val):
    try:
        return ("background-color:#c6efce;color:#276221;font-weight:bold"
                if float(val) >= score_corte
                else "background-color:#ffc7ce;color:#9c0006;font-weight:bold")
    except Exception:
        return ""

colunas_q = [f"q{i}" for i in range(1, 11) if f"q{i}" in df.columns]
colunas_exibir = ([c for c in ["arquivo", "base"] if c in df.columns]
                  + colunas_q + ["score_original", "score_simulado"])

def mostrar_tabela(df_show):
    st.write(f"**{len(df_show)}** artigos exibidos")
    styled = (
        df_show[colunas_exibir].style
        .map(colorir_q,    subset=colunas_q)
        .map(colorir_score, subset=["score_original", "score_simulado"])
        .format({"score_original": "{:.2f}", "score_simulado": "{:.2f}"})
    )
    st.dataframe(styled, width="stretch", height=420)

# ── Abas ───────────────────────────────────────────────────────────────────────
aba_res, aba_con = st.tabs(["📋 Resultado", "🔍 Consulta"])

with aba_res:
    st.subheader("Artigos")
    filtro_r = st.radio(
        "Mostrar:",
        ["Todos", "Aprovados (simulado)", "Reprovados (simulado)",
         "Salvos pelos pesos", "Removidos pelos pesos"],
        horizontal=True, key="filtro_resultado",
    )
    df_r = df.copy()
    if filtro_r == "Aprovados (simulado)":     df_r = df_r[df_r["aprovado_sim"]]
    elif filtro_r == "Reprovados (simulado)":  df_r = df_r[~df_r["aprovado_sim"]]
    elif filtro_r == "Salvos pelos pesos":     df_r = df_r[~df_r["aprovado_orig"] & df_r["aprovado_sim"]]
    elif filtro_r == "Removidos pelos pesos":  df_r = df_r[ df_r["aprovado_orig"] & ~df_r["aprovado_sim"]]
    mostrar_tabela(df_r)

with aba_con:
    st.subheader("🔍 Consulta por questão")
    st.caption("Filtre artigos por resposta em uma ou mais questões e veja as notas.")

    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        q_sel = st.selectbox(
            "Questão",
            ["(todas)"] + [f"Q{i}" for i in range(1, 11)],
            format_func=lambda x: x if x == "(todas)" else f"{x} — {DESCRICOES.get(x,'')}",
            key="consulta_q",
        )
    with col_f2:
        resp_sel = st.selectbox("Resposta", ["(qualquer)", "SIM", "PARCIAL", "NÃO"],
                                key="consulta_resp")
    with col_f3:
        texto_busca = st.text_input("🔎 Busca no arquivo / título",
                                    placeholder="ex: chatbot, agile…",
                                    key="consulta_texto")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        score_range = st.slider(
            f"Score simulado (range: {_s_min:.2f} – {_s_max:.2f})",
            min_value=_s_min, max_value=_s_max,
            value=(_s_min, _s_max),
            step=_s_step,
            key=f"score_range_{modo}",
        )
        score_min, score_max = score_range
    with col_s2:
        aprovacao_sel = st.radio("Status (simulado)",
                                 ["Todos", "Aprovados", "Reprovados"],
                                 key="consulta_aprovacao")

    df_c = df.copy()
    if q_sel != "(todas)" and resp_sel != "(qualquer)":
        df_c = df_c[df_c[q_sel.lower()].str.strip().str.upper() == resp_sel.upper()]
    if texto_busca.strip():
        t = texto_busca.strip().lower()
        df_c = df_c[
            df_c.get("arquivo", pd.Series(dtype=str)).str.lower().str.contains(t, na=False) |
            df_c.get("titulo",  pd.Series(dtype=str)).str.lower().str.contains(t, na=False)
        ]
    df_c = df_c[(df_c["score_simulado"] >= score_min) & (df_c["score_simulado"] <= score_max)]
    if aprovacao_sel == "Aprovados":   df_c = df_c[ df_c["aprovado_sim"]]
    elif aprovacao_sel == "Reprovados": df_c = df_c[~df_c["aprovado_sim"]]

    mostrar_tabela(df_c)
