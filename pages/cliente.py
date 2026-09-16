"""
Página: SLA por Cliente — desempenho de entrega agrupado por
客户名称(Nome do cliente). Mesmo padrão de filtros da tabela de DSP
(Estado, Ponto, faixa de SLA, volume mínimo) + busca por nome.
"""
import streamlit as st
import plotly.express as px
from shared import *

df = st.session_state["df"]

st.markdown(f"""
<div class="header-panel">
    <div>
        <div class="header-title">👤 {L("SLA por Cliente", "客户SLA")}</div>
        <div class="header-period">{L("Desempenho de entrega agrupado por cliente", "按客户汇总的配送表现")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if 'cliente' not in df.columns:
    st.info(L(
        "Esta base não traz a coluna de nome do cliente — não é possível abrir por cliente.",
        "本次数据不包含客户名称字段——无法按客户查看。"
    ))
    st.stop()

# ============================================================
# Filtros — mesmo padrão da tabela de DSP
# ============================================================
fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
with fcol1:
    estados_sel_cli = st.multiselect(L("Estado", "州"), sorted(df['estado_dest'].dropna().unique()), key="estados_cli")
with fcol2:
    pontos_sel_cli = st.multiselect(L("Ponto (DSP)", "网点 (DSP)"), sorted(df['ponto'].dropna().unique()), key="pontos_cli")
with fcol3:
    faixa_sla_cli = st.slider(L("Faixa de % Concluído no Prazo (%)", "准时完成率区间 (%)"), 0, 100, (0, 100), key="faixa_cli")
with fcol4:
    volume_min_cli = st.number_input(L("Volume mínimo", "最小件量"), min_value=0, value=0, step=10, key="vol_min_cli")
with fcol5:
    busca_cliente = st.text_input(L("Buscar cliente", "搜索客户"), placeholder=L("parte do nome...", "输入部分名称..."), key="busca_cli")

df_cli = df.copy()
if estados_sel_cli:
    df_cli = df_cli[df_cli['estado_dest'].isin(estados_sel_cli)]
if pontos_sel_cli:
    df_cli = df_cli[df_cli['ponto'].isin(pontos_sel_cli)]

g_cliente = agrupar(df_cli, 'cliente')
g_cliente = g_cliente[
    (g_cliente['pct_concluido'] >= faixa_sla_cli[0]) & (g_cliente['pct_concluido'] <= faixa_sla_cli[1])
]
g_cliente = g_cliente[g_cliente['total'] >= volume_min_cli]
if busca_cliente:
    g_cliente = g_cliente[g_cliente['cliente'].str.contains(busca_cliente, case=False, na=False)]
g_cliente = g_cliente.sort_values('pct_concluido', ascending=False)

if g_cliente.empty:
    st.info(L("Nenhum cliente bate com esses filtros.", "没有符合筛选条件的客户。"))
    st.stop()

cc1, cc2, cc3 = st.columns(3)
with cc1:
    st.metric(L("Clientes no recorte", "客户数"), len(g_cliente))
with cc2:
    st.metric(L("Volume total", "总件量"), f"{int(g_cliente['total'].sum()):,}".replace(",", "."))
with cc3:
    sla_medio = calc_sla(int(g_cliente['No prazo'].sum()), int(g_cliente['Fora do prazo'].sum()))
    st.metric(L("SLA do recorte", "本次筛选SLA"), f"{sla_medio:.2f}%")

st.caption(L(
    "'Recorte' é o subconjunto de clientes que passou pelos filtros acima. O SLA é agregado — "
    "soma de No Prazo e Fora do Prazo de todos os clientes do recorte, não a média das % "
    "individuais — por isso clientes com mais volume pesam mais no número final. Backlog não "
    "entra na conta (só pedidos já concluídos).",
    "「筛选范围」指经过上方筛选条件后剩下的客户子集。SLA为汇总计算——将筛选范围内所有客户的"
    "准时件与超时件相加计算，而非各客户百分比的平均值——因此件量越大的客户对最终数值的影响越大。"
    "积压件不计入该计算（仅计算已完成的订单）。"
))

# ============================================================
# Top clientes por volume (gráfico) — só os maiores, senão fica ilegível
# ============================================================
TOP_N_CLIENTES = 15
g_top_volume = g_cliente.sort_values('total', ascending=False).head(TOP_N_CLIENTES)

st.markdown(f"#### {L(f'Top {TOP_N_CLIENTES} Clientes por Volume', f'按件量排名前 {TOP_N_CLIENTES} 的客户')}")
fig_cli = px.bar(
    g_top_volume, x='cliente', y='pct_concluido',
    text=g_top_volume['pct_concluido'].apply(lambda v: f"{v:.1f}%"),
    color_discrete_sequence=[VERDE],
)
fig_cli.add_hline(y=92, line_dash="dash", line_color=LARANJA,
                   annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left")
fig_cli.update_layout(xaxis=dict(categoryorder="array", categoryarray=g_top_volume['cliente'].tolist()))
estilo_barra(fig_cli, altura=380, y_titulo=L("% Concluído no Prazo", "准时完成率"))
st.plotly_chart(fig_cli, use_container_width=True)
st.caption(L(
    f"Gráfico mostra só os {TOP_N_CLIENTES} clientes de maior volume (senão fica ilegível) — "
    "a tabela abaixo tem todos os clientes do recorte.",
    f"图表仅显示件量最大的 {TOP_N_CLIENTES} 个客户（避免图表过于拥挤）——完整客户列表见下方表格。"
))

# ============================================================
# Alerta gerencial: clientes de volume relevante com SLA abaixo da meta
# ============================================================
LIMIAR_VOLUME_ALERTA = 30
abaixo_meta = g_cliente[(g_cliente['total'] >= LIMIAR_VOLUME_ALERTA) & (g_cliente['pct_concluido'] < 92)]
if not abaixo_meta.empty:
    piores = abaixo_meta.sort_values('total', ascending=False).head(3)
    lista_piores = "; ".join(
        f"<b>{r['cliente']}</b> ({r['pct_concluido']:.1f}%, {int(r['total'])} {L('pedidos', '笔')})"
        for _, r in piores.iterrows()
    )
    st.markdown(f"""
    <div class="alert-card">
        <div class="alert-title">⚠️ {L(
            f"{len(abaixo_meta)} clientes com volume ≥ {LIMIAR_VOLUME_ALERTA} abaixo da meta de 92%",
            f"{len(abaixo_meta)} 个件量 ≥ {LIMIAR_VOLUME_ALERTA} 的客户未达到 92% 目标"
        )}</div>
        <div style="color:#7F1D1D; font-size:13px; margin-top:4px;">{lista_piores}</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

# ============================================================
# Tabela completa
# ============================================================
st.markdown(f"#### {L('Todos os clientes do recorte', '本次筛选的全部客户')}")
render_html(
    montar_tabela_html(g_cliente, coluna_chave='cliente', rotulo_coluna=L('Cliente', '客户'))
)

# ============================================================
# Exportar
# ============================================================
_export_cli = g_cliente[['cliente', 'Backlog', 'Fora do prazo', 'No prazo', 'total', 'pct_concluido']].copy()
_export_cli['pct_concluido'] = _export_cli['pct_concluido'].round(2)
_export_cli = _export_cli.rename(columns={
    'cliente': L('Cliente', '客户'), 'Backlog': L('Backlog', '积压件'),
    'Fora do prazo': L('Fora do Prazo', '超时件'), 'No prazo': L('No Prazo', '准时件'),
    'total': L('Total Geral', '总计'), 'pct_concluido': L('% Concluído no Prazo', '准时完成率(%)'),
})
_csv_cli = _export_cli.to_csv(index=False, sep=';').encode('utf-8-sig')
st.download_button(
    L("⬇️ Baixar tabela de clientes (CSV)", "⬇️ 下载客户表格 (CSV)"),
    data=_csv_cli,
    file_name=f"sla_por_cliente_{st.session_state['agora'].strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)