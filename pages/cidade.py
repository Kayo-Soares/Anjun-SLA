"""
Página: Análise por Cidade — SLA por cidade dentro de um DSP escolhido, e
quantos entregadores distintos atendem cada cidade. Página própria (não mais
um bloco espremido na sidebar) para caber gráfico + tabela completos.
"""
import streamlit as st
import plotly.express as px
from shared import *

df = st.session_state["df"]
tem_entregador = st.session_state["tem_entregador"]

st.markdown(f"""
<div class="header-panel">
    <div>
        <div class="header-title">📍 {L("Análise por Cidade", "按城市分析")}</div>
        <div class="header-period">{L("SLA e cobertura de entregadores por cidade, dentro de um DSP", "各DSP网点内，按城市查看SLA与配送员覆盖情况")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

if 'cidade_dest' not in df.columns:
    st.info(L(
        "Esta base não traz a coluna de cidade do destinatário — não é possível abrir por cidade.",
        "本次数据不包含收件人城市字段——无法按城市查看。"
    ))
    st.stop()

ponto_cidade_sel = st.selectbox(
    L("Escolha um DSP para abrir por cidade", "选择一个DSP网点以按城市查看"),
    sorted(df['ponto'].dropna().unique()),
    key="ponto_cidade_sel"
)

df_cidade_base = df[df['ponto'] == ponto_cidade_sel]
g_cidade = agrupar_cidade(df_cidade_base, tem_entregador).sort_values('pct_concluido', ascending=False)

cc1, cc2, cc3 = st.columns(3)
with cc1:
    st.metric(L("Cidades atendidas", "覆盖城市数"), len(g_cidade))
with cc2:
    st.metric(
        L("Entregadores no DSP", "网点配送员数"),
        df_cidade_base['entregador'].nunique() if tem_entregador else "—"
    )
with cc3:
    st.metric(L("Volume total", "总件量"), f"{int(g_cidade['total'].sum()):,}".replace(",", "."))

if not tem_entregador:
    st.caption(L(
        "Esta base não traz a coluna de entregador individual — a contagem de "
        "entregadores por cidade não está disponível para esta exportação.",
        "本次数据不包含配送员字段——该导出报表无法显示各城市的配送员数量。"
    ))

fig_cidade = px.bar(
    g_cidade, x='cidade_dest', y='pct_concluido',
    text=g_cidade['pct_concluido'].apply(lambda v: f"{v:.1f}%"),
    color_discrete_sequence=[VERDE],
)
fig_cidade.add_hline(y=92, line_dash="dash", line_color=LARANJA,
                      annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left")
fig_cidade.update_layout(xaxis=dict(categoryorder="array", categoryarray=g_cidade['cidade_dest'].tolist()))
estilo_barra(fig_cidade, altura=380, y_titulo=L("% Concluído no Prazo", "准时完成率"))
st.plotly_chart(fig_cidade, use_container_width=True)

render_html(
    montar_tabela_cidade_html(g_cidade, mostrar_entregadores=tem_entregador)
)