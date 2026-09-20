"""
Página: Resumo Geral — a visão "pra mandar pro time/diretoria" sem filtros
nem gráficos: KPIs no topo + tabela por DPS ordenada do melhor pro pior SLA,
com linha de Total Geral. Pensada pra ser a versão que hoje vai numa
tabela solta; aqui vira tela própria, sempre igual, sem precisar mexer
em filtro nenhum pra ver o resumo do dia.
"""
import streamlit as st
from shared import *

df = st.session_state["df"]
agora = st.session_state["agora"]

deadline_min, deadline_max = df['deadline'].min(), df['deadline'].max()
periodo_label = (
    deadline_min.strftime('%d/%m/%Y') if deadline_min.date() == deadline_max.date()
    else f"{deadline_min.strftime('%d/%m/%Y')} a {deadline_max.strftime('%d/%m/%Y')}"
)

st.markdown(f"""
<div class="header-panel">
    <div>
        <div class="header-title">📊 {L("Resumo Geral", "总体概览")}</div>
        <div class="header-period">📅 {L("Período", "周期")}: {periodo_label}</div>
    </div>
    <div class="header-tagline">{L("Mais eficiência<br>para a sua entrega. 🚚", "为您的配送<br>提供更高效率。🚚")}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Filtro por Supervisor — só aparece se o mapa Ponto→Supervisor foi enviado
# ============================================================
tem_supervisor = st.session_state.get("tem_supervisor", False)
if tem_supervisor:
    supervisores_sel_resumo = st.multiselect(
        L("Filtrar por Supervisor", "按主管筛选"),
        sorted(df['supervisor'].dropna().unique()),
        key="supervisores_resumo"
    )
    if supervisores_sel_resumo:
        df = df[df['supervisor'].isin(supervisores_sel_resumo)]

# ============================================================
# KPIs — mesmo padrão visual da aba SLA
# ============================================================
total = len(df)
no_prazo = int((df['classe'] == 'No prazo').sum())
fora = int((df['classe'] == 'Fora do prazo').sum())
backlog = int((df['classe'] == 'Backlog').sum())
# Mesma fórmula da tabela (No Prazo / Total Geral, Backlog incluído no
# denominador) — pra bater com o rodapé "Total Geral" da tabela abaixo.
sla_geral = (no_prazo / total * 100) if total > 0 else 0.0

kpis = [
    ("📦", VERMELHO_PILL_BG, VERMELHO, L("Backlog", "积压件"), f"{backlog:,}".replace(",", ".")),
    ("🕐", LARANJA_PILL_BG, LARANJA, L("Fora do Prazo", "超时件"), f"{fora:,}".replace(",", ".")),
    ("✔", VERDE_PILL_BG, VERDE, L("No Prazo", "准时件"), f"{no_prazo:,}".replace(",", ".")),
    ("📦", CINZA_PILL_BG, CINZA_ESCURO, L("Total Geral", "总计"), f"{total:,}".replace(",", ".")),
    ("🎯", VERDE_PILL_BG, VERDE, L("SLA Geral", "总体SLA"), f"{sla_geral:.2f}%"),
]
cols_kpi = st.columns(5)
for col, (icone, bg, cor, label, valor) in zip(cols_kpi, kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-accent:{cor};">
            <div class="kpi-icon" style="background-color:{bg}; color:{cor};">{icone}</div>
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{valor}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# ============================================================
# Tabela por DPS — melhores no topo, piores por último
# ============================================================
g_ponto_resumo = agrupar(df, 'ponto').sort_values('pct_concluido', ascending=False)
render_html(
    montar_tabela_html(g_ponto_resumo, coluna_chave='ponto', rotulo_coluna='DPS')
)

st.write("")

# ============================================================
# Baixar como imagem (PNG) — mesmo formato de print da aba SLA, já reflete
# o filtro de supervisor se algum estiver selecionado.
# ============================================================
imagem_resumo = gerar_imagem_relatorio(
    None, g_ponto_resumo, False, agora.strftime('%d/%m/%Y %H:%M')
)
st.download_button(
    L("⬇️ Baixar como imagem (PNG)", "⬇️ 下载为图片 (PNG)"),
    data=imagem_resumo,
    file_name=f"resumo_geral_{agora.strftime('%Y%m%d_%H%M')}.png",
    mime="image/png",
)