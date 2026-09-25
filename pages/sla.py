"""
Página: SLA — visão detalhada (Anjun Express).

Tudo que é comum (idioma, CSS, upload, processamento da base) já vem pronto
do app.py via st.session_state e do shared.py via `from shared import *`.
Esta página só cuida do que é dela: o toggle Dashboard/SLA Detalhado, os
gráficos, as tabelas com filtro (DSP/Supervisor/Entregador) e as exportações.
"""
import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go
from shared import *

# ============================================================
# DADOS — já processados pelo app.py, lidos do session_state
# ============================================================
df = st.session_state["df"]
agora = st.session_state["agora"]
extracao_dt = st.session_state.get("extracao")
tem_supervisor = st.session_state["tem_supervisor"]
mapa_supervisor = st.session_state["mapa_supervisor"]

# ============================================================
# Toggle Dashboard / SLA Detalhado — o widget em si é renderizado pelo
# app.py (pra aparecer logo abaixo do menu de navegação, acima da logo);
# aqui só lemos o valor que ele já deixou no session_state.
# ============================================================
nav_pagina = st.session_state.get("pagina_nav_sla", "dashboard")

# ============================================================
# Cabeçalho / período / avisos de contexto
# ============================================================
deadline_min, deadline_max = df['deadline'].min(), df['deadline'].max()
periodo_label = (
    deadline_min.strftime('%d/%m/%Y') if deadline_min.date() == deadline_max.date()
    else f"{deadline_min.strftime('%d/%m/%Y')} a {deadline_max.strftime('%d/%m/%Y')}"
)
fechado = deadline_max < agora

st.markdown(f"""
<div class="header-panel">
    <div>
        <div class="header-title">📊 {L("DSP — Indicadores de Entrega", "DSP — 配送指标")}</div>
        <div class="header-period">📅 {L("Período", "周期")}: {periodo_label}</div>
    </div>
    <div class="header-tagline">{L("Mais eficiência<br>para a sua entrega. 🚚", "为您的配送<br>提供更高效率。🚚")}</div>
</div>
""", unsafe_allow_html=True)

if not fechado:
    st.caption(L(
        "⚠️ Corte de dia em curso — parte dos vencimentos ainda não chegou. Backlog aqui pode ser normal.",
        "⚠️ 当前为进行中的一天 —— 部分时效尚未到期，此时的积压件属于正常情况。"
    ))
else:
    st.caption(L(
        "✅ Corte de fechamento — todos os vencimentos já passaram. Pedidos ainda em Backlog venceram "
        "sem confirmação de entrega — vale atenção, mesmo que só apareçam como Fora do Prazo quando "
        "forem de fato entregues.",
        "✅ 当前为已结束的一天 —— 全部时效均已到期。仍处于积压件状态的订单已超时但未签收确认 —— 需要"
        "关注，即使它们只有在实际签收后才会被计为超时件。"
    ))
st.caption(L(
    "Fora do Prazo é um fato consumado: só existe depois que o pedido é entregue (assinatura depois "
    "do prazo). Enquanto não é entregue, continua Backlog — mesmo que o prazo já tenha vencido. "
    "Reenviar o arquivo mais tarde só muda a classificação de pedidos que foram entregues nesse meio-tempo.",
    "超时件是已发生的事实：只有在订单签收之后（签收时间晚于时效）才会被计为超时件。在签收之前，订单始终"
    "属于积压件 —— 即使时效已经到期。稍后重新上传文件，只会改变这段时间内新签收订单的分类。"
))

# ============================================================
# KPIs
# ============================================================
total = len(df)
no_prazo = int((df['classe'] == 'No prazo').sum())
fora = int((df['classe'] == 'Fora do prazo').sum())
backlog = int((df['classe'] == 'Backlog').sum())
pct_concluido = (no_prazo / total * 100) if total > 0 else 0.0

kpis = [
    ("📦", VERMELHO_PILL_BG, VERMELHO, L("Backlog", "积压件"), f"{backlog:,}".replace(",", ".")),
    ("🕐", LARANJA_PILL_BG, LARANJA, L("Fora do Prazo", "超时件"), f"{fora:,}".replace(",", ".")),
    ("✔", VERDE_PILL_BG, VERDE, L("No Prazo", "准时件"), f"{no_prazo:,}".replace(",", ".")),
    ("📦", CINZA_PILL_BG, CINZA_ESCURO, L("Total Geral", "总计"), f"{total:,}".replace(",", ".")),
    ("📊", VERDE_PILL_BG, VERDE, L("% Concluído no Prazo (do total)", "准时完成率（占总量）"), f"{pct_concluido:.2f}%"),
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
# Alerta de perdas confirmadas
# ============================================================
perdas_confirmadas = int((df['motivo_ocorrencia'] == 'Perda confirmada - Aguardando indenização').sum()) \
    if 'motivo_ocorrencia' in df.columns else 0

if perdas_confirmadas > 0:
    top_perda_ponto = df[df['motivo_ocorrencia'] == 'Perda confirmada - Aguardando indenização']['ponto'] \
        .value_counts()
    concentracao = top_perda_ponto.index[0]
    pct_concentracao = top_perda_ponto.iloc[0] / perdas_confirmadas * 100
    titulo_alerta = L(
        f"⚠️ {perdas_confirmadas} perdas confirmadas (aguardando indenização)",
        f"⚠️ {perdas_confirmadas} 笔确认丢失（等待赔偿）"
    )
    corpo_alerta = L(
        f"{pct_concentracao:.0f}% concentrado em um único ponto: <b>{concentracao}</b> "
        f"({top_perda_ponto.iloc[0]} de {perdas_confirmadas}). Trate separado do plano de SLA.",
        f"{pct_concentracao:.0f}% 集中在单一网点：<b>{concentracao}</b>"
        f"（{perdas_confirmadas}笔中的{top_perda_ponto.iloc[0]}笔）。请与SLA改善计划分开处理。"
    )
    st.markdown(f"""
    <div class="alert-card">
        <div class="alert-title">{titulo_alerta}</div>
        <div style="color:#7F1D1D; font-size:13px; margin-top:4px;">{corpo_alerta}</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

# ============================================================
# Gráficos (só na tela Dashboard)
# ============================================================
if nav_pagina == "dashboard":
    g_estado = agrupar(df, 'estado_dest').sort_values('pct_concluido', ascending=False)

    col_chart1, col_chart2 = st.columns([2, 1])
    with col_chart1:
        st.markdown(f"#### {L('% Concluído no Prazo por Estado', '各州准时完成率')}")
        # Cor por status de performance (verde/laranja/vermelho), não uma cor de marca fixa —
        # assim dá pra ver quem está abaixo da meta sem precisar ler cada rótulo.
        cores_estado = g_estado['pct_concluido'].apply(cor_sla)
        fig = px.bar(
            g_estado, x='estado_dest', y='pct_concluido',
            text=g_estado['pct_concluido'].apply(lambda v: f"{v:.1f}%"),
        )
        fig.update_traces(
            marker_color=cores_estado,
            hovertemplate="<b>%{x}</b><br>" + L("Concluído no prazo", "准时完成率") + ": %{y:.1f}%<extra></extra>",
        )
        fig.add_hline(y=92, line_width=1, line_color=CINZA_ESCURO,
                      annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left",
                      annotation_font=dict(size=11, color=CINZA_ESCURO))
        fig.update_layout(xaxis=dict(categoryorder="array", categoryarray=g_estado['estado_dest'].tolist()))
        estilo_barra(fig, altura=360, y_titulo=L("% Concluído no Prazo", "准时完成率"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(L(
            "🟢 dentro da meta (≥92%) · 🟠 alerta (80-91,9%) · 🔴 crítico (<80%).",
            "🟢 达标 (≥92%) · 🟠 警戒 (80-91.9%) · 🔴 严重 (<80%)。"
        ))

    with col_chart2:
        st.markdown(f"#### {L('Distribuição de Waybills', '运单分布')}")
        fig2 = go.Figure(data=[go.Pie(
            labels=[L('No Prazo', '准时件'), L('Fora do Prazo', '超时件'), L('Backlog', '积压件')],
            values=[no_prazo, fora, backlog],
            hole=0.6,
            marker_colors=[VERDE, VERMELHO, LARANJA],
        )])
        rotulo_total = L("total", "总计")
        estilo_donut(fig2, total_label=f"{total:,}".replace(",", ".") + f"<br><span style='font-size:11px;color:#6B7280'>{rotulo_total}</span>", altura=360)
        st.plotly_chart(fig2, use_container_width=True)

    # ============================================================
    # Composição do Backlog
    # ============================================================
    if backlog > 0:
        st.markdown(f"#### {L('Composição do Backlog', '积压件构成')}")
        backlog_df = df[df['classe'] == 'Backlog']
        comp = backlog_df['status'].value_counts().reset_index()
        comp.columns = ['status', 'qtd']
        comp = comp.sort_values('qtd', ascending=False)
        comp['status_show'] = comp['status'].apply(traduzir_status)

        # Além de MAX_FATIAS_DONUT_STATUS status distintos, agrupa a cauda em "Outros"
        # só na rosca (a tabela ao lado continua listando cada status individualmente) —
        # evita mais de ~7 cores carregando significado, que ficam indistinguíveis.
        if len(comp) > MAX_FATIAS_DONUT_STATUS:
            comp_topo = comp.iloc[:MAX_FATIAS_DONUT_STATUS - 1].copy()
            qtd_outros = int(comp.iloc[MAX_FATIAS_DONUT_STATUS - 1:]['qtd'].sum())
            comp_donut = pd.concat([
                comp_topo,
                pd.DataFrame([{'status': '__outros__', 'qtd': qtd_outros, 'status_show': L('Outros', '其他')}]),
            ], ignore_index=True)
        else:
            comp_donut = comp

        cores_donut = [
            COR_OUTROS_STATUS if r['status'] == '__outros__' else cor_status(r['status'])
            for _, r in comp_donut.iterrows()
        ]

        col_comp1, col_comp2 = st.columns([1, 2])
        with col_comp1:
            fig_comp = go.Figure(data=[go.Pie(
                labels=comp_donut['status_show'], values=comp_donut['qtd'], hole=0.6,
                marker_colors=cores_donut,
            )])
            rotulo_backlog = L("backlog", "积压件")
            estilo_donut(fig_comp, total_label=f"{backlog:,}".replace(",", ".") + f"<br><span style='font-size:11px;color:#6B7280'>{rotulo_backlog}</span>", altura=320)
            st.plotly_chart(fig_comp, use_container_width=True)
        with col_comp2:
            linhas_status = ""
            for _, r in comp.iterrows():
                pct = r['qtd'] / backlog * 100
                cor_barra = cor_status(r['status'])
                linhas_status += f"""
                <tr>
                    <td><b>{r['status_show']}</b></td>
                    <td>{int(r['qtd']):,}</td>
                    <td style="width:220px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="flex:1; background:#EEF2EF; border-radius:6px; height:10px; overflow:hidden;">
                                <div style="width:{pct:.1f}%; background:{cor_barra}; height:100%;"></div>
                            </div>
                            <span style="font-weight:700; font-size:12.5px; min-width:42px; text-align:right;">{pct:.1f}%</span>
                        </div>
                    </td>
                </tr>"""
            col_status = L("Status", "状态")
            col_qtd = L("Qtd", "数量")
            col_pctbl = L("% do Backlog", "占积压件比例")
            st.markdown(f"""
            <table class="dps-table">
                <thead><tr><th>{col_status}</th><th>{col_qtd}</th><th>{col_pctbl}</th></tr></thead>
                <tbody>{linhas_status}</tbody>
            </table>
            """, unsafe_allow_html=True)
            st.caption(L(
                "Cada status pede uma ação diferente: 'Em rota' é rota lenta, 'Pacote armazenado' é "
                "pacote parado fisicamente, 'Pedido com anomalia' já tem ocorrência registrada — "
                "'Recebido no ponto de entrega' está na última milha, quase saindo.",
                "每种状态需要不同的处理方式：「派送途中」是配送速度慢；「包裹已入库」是包裹实际停滞；"
                "「异常件」已登记问题记录；「已到达派送网点」处于最后一公里，即将出库。"
            ))

    # ============================================================
    # Baixas por Hora (entregas confirmadas ao longo do dia)
    # ============================================================
    st.markdown(f"#### {L('Baixas por Hora', '每小时签收量')}")

    modo_baixa = st.radio(
        L("Tipo de análise", "分析类型"),
        options=["mesmo_dia", "todas"],
        format_func=lambda v: L("Somente baixas no dia do vencimento", "仅显示当日到期且当日签收")
            if v == "mesmo_dia" else L("Todas as baixas (qualquer dia)", "全部签收（不限日期）"),
        horizontal=True,
        key="modo_baixa_hora",
    )

    df_entregues_todas = df[df['classe'].isin(['No prazo', 'Fora do prazo'])].copy()
    # Só conta baixa que aconteceu no MESMO dia do vencimento do pacote — exclui entregas
    # que "vazaram" pra antes ou depois do dia de referência, pra não misturar dias.
    df_entregues_mesmo_dia = df_entregues_todas[
        df_entregues_todas['signature_dt'].dt.date == df_entregues_todas['deadline'].dt.date
    ].copy()
    qtd_fora_do_dia = len(df_entregues_todas) - len(df_entregues_mesmo_dia)

    df_entregues = df_entregues_mesmo_dia if modo_baixa == "mesmo_dia" else df_entregues_todas

    if not df_entregues.empty:
        df_entregues['hora'] = df_entregues['signature_dt'].dt.hour
        g_hora = df_entregues.groupby(['hora', 'classe']).size().unstack(fill_value=0)
        for c in ['No prazo', 'Fora do prazo']:
            if c not in g_hora.columns:
                g_hora[c] = 0
        g_hora = g_hora.reindex(range(24), fill_value=0).reset_index()
        g_hora['hora_label'] = g_hora['hora'].apply(lambda h: f"{h:02d}h")
        g_hora['total_hora'] = g_hora['No prazo'] + g_hora['Fora do prazo']

        g_hora['pct_no_prazo'] = (g_hora['No prazo'] / g_hora['total_hora'] * 100).fillna(0)

        fig_hora = go.Figure()
        fig_hora.add_bar(
            x=g_hora['hora_label'], y=g_hora['No prazo'],
            name=L('No Prazo', '准时件'), marker_color=VERDE,
            customdata=g_hora['pct_no_prazo'],
            hovertemplate="<b>%{x}</b><br>" + L("No prazo", "准时") + ": %{y}<extra></extra>",
        )
        fig_hora.add_bar(
            x=g_hora['hora_label'], y=g_hora['Fora do prazo'],
            name=L('Fora do Prazo', '超时件'), marker_color=VERMELHO,
            hovertemplate="<b>%{x}</b><br>" + L("Fora do prazo", "超时") + ": %{y}<extra></extra>",
        )
        # Só 1 rótulo por barra: o total empilhado, acima de cada coluna (não um rótulo
        # por segmento, que ficaria poluído com duas séries empilhadas).
        fig_hora.add_trace(go.Scatter(
            x=g_hora['hora_label'], y=g_hora['total_hora'],
            mode='text',
            text=g_hora['total_hora'].apply(lambda v: f"{int(v):,}".replace(",", ".") if v > 0 else ""),
            textposition='top center', textfont=dict(size=11, color=CINZA_TEXTO),
            showlegend=False, hoverinfo='skip',
        ))
        estilo_barra_contagem(fig_hora, altura=340, y_titulo=L('Baixas (qtd)', '签收量'))
        maior_total = g_hora['total_hora'].max()
        fig_hora.update_layout(yaxis=dict(range=[0, maior_total * 1.18 if maior_total > 0 else 1]))
        st.plotly_chart(fig_hora, use_container_width=True)

        total_baixas = int(g_hora['No prazo'].sum() + g_hora['Fora do prazo'].sum())
        pico = g_hora.loc[g_hora['total_hora'].idxmax()]

        if modo_baixa == "mesmo_dia":
            nota_exclusao = L(
                f" ({qtd_fora_do_dia:,} baixas de outro dia foram excluídas.)".replace(",", ".") if qtd_fora_do_dia > 0 else "",
                f"（另有 {qtd_fora_do_dia:,} 笔非当日签收已被排除。）" if qtd_fora_do_dia > 0 else ""
            )
            legenda_periodo = L("no dia do vencimento", "当日到期且当日签收")
        else:
            nota_exclusao = ""
            legenda_periodo = L("no período (qualquer dia)", "本期间（不限日期）")

        st.caption(L(
            f"Total de {total_baixas:,} baixas {legenda_periodo}. Horário de pico: {pico['hora_label']} "
            f"({int(pico['total_hora']):,} baixas).".replace(",", ".") + nota_exclusao,
            f"{legenda_periodo}共 {total_baixas:,} 笔签收。高峰时段：{pico['hora_label']}"
            f"（{int(pico['total_hora']):,} 笔）。" + nota_exclusao
        ))

        # ============================================================
        # % No Prazo por Hora — segundo gráfico, mesmo eixo x, eixo Y próprio (0-100%).
        # Ideia: em vez de forçar volume + % na mesma escala (eixo duplo, que distorce
        # a leitura), colocar os dois empilhados um embaixo do outro deixa fácil ver se
        # o horário de maior volume é também o de pior SLA — sem inventar correlação.
        # ============================================================
        g_hora_com_baixa = g_hora[g_hora['total_hora'] > 0]
        if len(g_hora_com_baixa) >= 2:
            pior_hora = g_hora_com_baixa.loc[g_hora_com_baixa['pct_no_prazo'].idxmin()]
            fig_pct_hora = go.Figure()
            fig_pct_hora.add_trace(go.Scatter(
                x=g_hora_com_baixa['hora_label'], y=g_hora_com_baixa['pct_no_prazo'],
                mode='lines+markers',
                line=dict(color=VERDE, width=2, shape='spline', smoothing=0.3),
                marker=dict(size=8, color=VERDE, line=dict(color="#FFFFFF", width=2)),
                fill='tozeroy', fillcolor="rgba(0,166,62,0.10)",
                hovertemplate="<b>%{x}</b><br>" + L("No prazo", "准时率") + ": %{y:.1f}%<extra></extra>",
                showlegend=False,
            ))
            fig_pct_hora.add_hline(y=92, line_width=1, line_color=CINZA_ESCURO,
                                    annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left",
                                    annotation_font=dict(size=11, color=CINZA_ESCURO))
            fig_pct_hora.update_layout(
                font=FONTE_GRAFICO, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 108], title=L('% No Prazo', '准时率'), gridcolor=GRADE_GRAFICO,
                           zeroline=False, dtick=20, ticksuffix="%"),
                xaxis=dict(title="", showgrid=False),
                height=200, margin=dict(t=20, b=20, l=10, r=10),
                hoverlabel=dict(bgcolor="white", bordercolor="#E5E7EB", font=FONTE_GRAFICO),
            )
            st.markdown(f"##### {L('% No Prazo por Hora', '每小时准时率')}")
            st.plotly_chart(fig_pct_hora, use_container_width=True)
            if pior_hora['hora_label'] == pico['hora_label']:
                st.caption(L(
                    f"⚠️ O horário de maior volume ({pico['hora_label']}) é também o de pior % no prazo "
                    f"({pior_hora['pct_no_prazo']:.1f}%) — indício de gargalo por volume nesse horário.",
                    f"⚠️ 签收量最高的时段（{pico['hora_label']}）也是准时率最低的时段"
                    f"（{pior_hora['pct_no_prazo']:.1f}%）—— 可能存在该时段的处理瓶颈。"
                ))
            else:
                st.caption(L(
                    f"Pior % no prazo às {pior_hora['hora_label']} ({pior_hora['pct_no_prazo']:.1f}%) — "
                    f"não coincide com o horário de maior volume, então não parece ser gargalo de capacidade.",
                    f"准时率最低的时段是 {pior_hora['hora_label']}（{pior_hora['pct_no_prazo']:.1f}%）—— "
                    f"与最高签收量时段不一致，看起来不是处理能力瓶颈。"
                ))
    else:
        st.info(L("Nenhuma entrega confirmada neste corte ainda.", "本次数据中尚无已签收订单。"))

    # ============================================================
    # Antecedência de Entrega (quantos dias antes do prazo o pedido foi baixado)
    # ============================================================
    st.markdown(f"#### {L('Antecedência de Entrega', '提前签收天数分布')}")

    no_prazo_df = df[df['classe'] == 'No prazo'].copy()
    if not no_prazo_df.empty:
        bins_ant = [-0.001, 2, 5, 10, 15, 20, 25, 9999]
        labels_ant = [
            L("0-2 dias", "0-2天"), L("3-5 dias", "3-5天"), L("6-10 dias", "6-10天"),
            L("11-15 dias", "11-15天"), L("16-20 dias", "16-20天"), L("21-25 dias", "21-25天"),
            L("26+ dias", "26天以上"),
        ]
        no_prazo_df['faixa_antecedencia'] = pd.cut(no_prazo_df['diferenca_dias'], bins=bins_ant, labels=labels_ant)
        g_ant = no_prazo_df['faixa_antecedencia'].value_counts().reindex(labels_ant).fillna(0).reset_index()
        g_ant.columns = ['faixa', 'qtd']

        # A faixa "0-2 dias" é quem quase perdeu o prazo — mesmo contando como "No Prazo",
        # é o grupo com menor margem de segurança. Destacar em laranja (sem ser status
        # oficial do pedido, é um sinal de risco operacional) chama atenção pra esse volume
        # sem misturar com os pedidos que têm folga confortável.
        cores_ant = [LARANJA if faixa == labels_ant[0] else VERDE for faixa in g_ant['faixa']]
        pct_risco = (g_ant.iloc[0]['qtd'] / g_ant['qtd'].sum() * 100) if g_ant['qtd'].sum() > 0 else 0

        fig_ant = px.bar(
            g_ant, x='faixa', y='qtd',
            text=g_ant['qtd'].apply(lambda v: f"{int(v):,}".replace(",", ".")),
        )
        fig_ant.update_traces(
            marker_color=cores_ant,
            hovertemplate="<b>%{x}</b><br>" + L("Pedidos", "订单数") + ": %{y}<extra></extra>",
        )
        fig_ant.update_layout(showlegend=False)
        estilo_barra_contagem(fig_ant, altura=340, y_titulo=L('Pedidos (qtd)', '订单数量'))
        st.plotly_chart(fig_ant, use_container_width=True)

        media_ant = no_prazo_df['diferenca_dias'].mean()
        mediana_ant = no_prazo_df['diferenca_dias'].median()
        st.caption(L(
            f"Média de {media_ant:.1f} dias de antecedência (mediana: {mediana_ant:.1f} dias), "
            f"com base nos {len(no_prazo_df):,} pedidos entregues no prazo. 🟠 {pct_risco:.1f}% entregou "
            f"com 0-2 dias de folga — margem apertada, risco de virar Fora do Prazo num pequeno atraso.".replace(",", "."),
            f"平均提前 {media_ant:.1f} 天签收（中位数：{mediana_ant:.1f} 天），"
            f"基于 {len(no_prazo_df):,} 笔准时签收订单统计。🟠 其中 {pct_risco:.1f}% 的订单仅提前 0-2 天签收 —— "
            f"缓冲时间较短，稍有延误即可能变为超时件。"
        ))
    else:
        st.info(L("Nenhum pedido no prazo neste corte ainda.", "本次数据中暂无准时签收订单。"))

# ============================================================
# Cálculo do Supervisor — feito uma vez só, reaproveitado no gráfico (Dashboard)
# e na tabela + relatório de print (SLA Detalhado)
# ============================================================
if tem_supervisor:
    g_sup = agrupar(df, 'supervisor').sort_values('pct_concluido', ascending=False)

if nav_pagina == "dashboard":
    if tem_supervisor:
        st.markdown(f"#### {L('% Concluído no Prazo por Supervisor', '各主管准时完成率')}")
        cores_sup = g_sup['pct_concluido'].apply(cor_sla)
        fig_sup = px.bar(
            g_sup, x='supervisor', y='pct_concluido',
            text=g_sup['pct_concluido'].apply(lambda v: f"{v:.1f}%"),
        )
        fig_sup.update_traces(
            marker_color=cores_sup,
            hovertemplate="<b>%{x}</b><br>" + L("Concluído no prazo", "准时完成率") + ": %{y:.1f}%<extra></extra>",
        )
        fig_sup.add_hline(y=92, line_width=1, line_color=CINZA_ESCURO,
                           annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left",
                           annotation_font=dict(size=11, color=CINZA_ESCURO))
        fig_sup.update_layout(xaxis=dict(categoryorder="array", categoryarray=g_sup['supervisor'].tolist()))
        estilo_barra(fig_sup, altura=340, y_titulo=L("% Concluído no Prazo", "准时完成率"))
        st.plotly_chart(fig_sup, use_container_width=True)
    else:
        st.info(L(
            "Envie o mapa Ponto → Supervisor na barra lateral pra ativar a visão e o filtro por supervisor.",
            "请在侧边栏上传 网点→主管 对照表，以启用按主管查看和筛选功能。"
        ))

if nav_pagina == "sla":
    if tem_supervisor:
        st.markdown(f"#### {L('Tabela por Supervisor', '按主管汇总表')}")
        st.markdown(
            montar_tabela_html(g_sup, coluna_chave='supervisor', rotulo_coluna=L('Supervisor', '主管')),
            unsafe_allow_html=True
        )

    # ============================================================
    # Tabela estilo DSP (cabeçalho verde + pílulas de SLA)
    # ============================================================
    st.markdown("#### DSP")

    g_ponto = agrupar(df, 'ponto').merge(
        df.groupby('ponto')['estado_dest'].first().reset_index(), on='ponto', how='left'
    )
    if tem_supervisor:
        g_ponto = g_ponto.merge(mapa_supervisor, on='ponto', how='left')
        g_ponto['supervisor'] = g_ponto['supervisor'].fillna(L('Sem supervisor mapeado', '未匹配主管'))

    if tem_supervisor:
        fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
        with fcol4:
            supervisores_sel = st.multiselect(L("Supervisor", "主管"), sorted(g_ponto['supervisor'].dropna().unique()))
    else:
        fcol1, fcol2, fcol3, fcol5 = st.columns(4)
        supervisores_sel = []
    with fcol1:
        estados_sel = st.multiselect(L("Estado", "州"), sorted(df['estado_dest'].dropna().unique()))
    with fcol2:
        pontos_sel = st.multiselect(L("Ponto (DSP)", "网点 (DSP)"), sorted(g_ponto['ponto'].dropna().unique()))
    with fcol3:
        faixa_sla = st.slider(L("Faixa de % Concluído no Prazo (%)", "准时完成率区间 (%)"), 0, 100, (0, 100))
    with fcol5:
        volume_min_dsp = st.number_input(L("Volume mínimo", "最小件量"), min_value=0, value=0, step=10, key="vol_min_dsp")

    tabela = g_ponto.copy()
    if estados_sel:
        tabela = tabela[tabela['estado_dest'].isin(estados_sel)]
    if pontos_sel:
        tabela = tabela[tabela['ponto'].isin(pontos_sel)]
    if supervisores_sel:
        tabela = tabela[tabela['supervisor'].isin(supervisores_sel)]
    tabela = tabela[(tabela['pct_concluido'] >= faixa_sla[0]) & (tabela['pct_concluido'] <= faixa_sla[1])]
    tabela = tabela[tabela['total'] >= volume_min_dsp]
    tabela = tabela.sort_values('pct_concluido', ascending=False)

    st.markdown(montar_tabela_html(tabela), unsafe_allow_html=True)

    # ============================================================
    # Exportar tabela filtrada (Excel / CSV)
    # ============================================================
    _cols_export = ['ponto', 'estado_dest']
    if 'supervisor' in tabela.columns:
        _cols_export.append('supervisor')
    _cols_export += ['Backlog', 'Fora do prazo', 'No prazo', 'total', 'pct_concluido']

    _export_df = tabela[_cols_export].copy()
    _export_df['pct_concluido'] = _export_df['pct_concluido'].round(2)
    _rename_export = {
        'ponto': 'DSP', 'estado_dest': L('Estado', '州'), 'supervisor': L('Supervisor', '主管'),
        'Backlog': L('Backlog', '积压件'), 'Fora do prazo': L('Fora do Prazo', '超时件'),
        'No prazo': L('No Prazo', '准时件'), 'total': L('Total Geral', '总计'),
        'pct_concluido': L('% Concluído no Prazo', '准时完成率(%)'),
    }
    _export_df = _export_df.rename(columns=_rename_export)

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        # sep=';' + utf-8-sig: formato que o Excel em português abre direto, sem
        # bagunçar acento nem juntar tudo numa coluna só (mesmo problema que já vimos
        # ao carregar o mapa Ponto->Supervisor).
        _csv_bytes = _export_df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            L("⬇️ Baixar tabela filtrada (CSV)", "⬇️ 下载筛选表格 (CSV)"),
            data=_csv_bytes,
            file_name=f"dsp_filtrado_{agora.strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_exp2:
        _buf_xlsx = io.BytesIO()
        with pd.ExcelWriter(_buf_xlsx, engine='openpyxl') as _writer:
            _export_df.to_excel(_writer, index=False, sheet_name='DSP')
        st.download_button(
            L("⬇️ Baixar tabela filtrada (Excel)", "⬇️ 下载筛选表格 (Excel)"),
            data=_buf_xlsx.getvalue(),
            file_name=f"dsp_filtrado_{agora.strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.caption(L(
        "Cor da pílula SLA (pelo próprio valor de % Concluído no Prazo): verde ≥ 92% · "
        "amarelo 80–91,99% · vermelho < 80%. Ajustável, avise se quiser outro corte. "
        "Classificação por waybill: Fora do Prazo só existe após entrega (prazo − assinatura negativo); "
        "sem entrega, o pedido é sempre Backlog.",
        "SLA徽章颜色（基于准时完成率数值本身）：绿色 ≥ 92% · 黄色 80–91.99% · 红色 < 80%。"
        "可调整，如需更改区间请告知。分类逻辑：只有在签收之后（时效−签收时间为负）才会被计为超时件；"
        "未签收的订单始终为积压件。"
    ))

    # ============================================================
    # Visão para impressão/print
    # ============================================================
    with st.expander(f"🖨️ {L('Abrir visão completa pra print (Supervisores + todos os DSPs)', '打开完整视图以便打印（主管 + 全部DSP）')}"):
        if tem_supervisor:
            st.markdown(f"**{L('Por Supervisor', '按主管')}**")
            st.markdown(
                montar_tabela_html(g_sup, coluna_chave='supervisor', rotulo_coluna=L('Supervisor', '主管')),
                unsafe_allow_html=True
            )
            st.write("")
        st.markdown(f"**{L('Todos os DSPs', '全部DSP网点')}**")
        g_ponto_completo = g_ponto.sort_values('pct_concluido', ascending=False)
        st.markdown(
            montar_tabela_html(g_ponto_completo, coluna_chave='ponto', rotulo_coluna="DSP"),
            unsafe_allow_html=True
        )

        st.write("")
        imagem_png = gerar_imagem_relatorio(
            g_sup if tem_supervisor else None,
            g_ponto_completo,
            tem_supervisor,
            agora.strftime('%d/%m/%Y %H:%M'),
            extracao_dt.strftime('%d/%m/%Y %H:%M:%S') if extracao_dt is not None else None,
        )
        st.download_button(
            L("⬇️ Baixar como imagem (PNG)", "⬇️ 下载为图片 (PNG)"),
            data=imagem_png,
            file_name=f"sla_supervisores_dsp_{agora.strftime('%Y%m%d_%H%M')}.png",
            mime="image/png",
        )

    # ============================================================
    # Drill-down por entregador dentro de um DSP
    # ============================================================
    st.markdown(f"#### {L('Detalhe por Entregador', '配送员明细')}")

    pontos_disponiveis = sorted(df['ponto'].dropna().unique())

    if tem_supervisor:
        ecol1, ecol2 = st.columns(2)
        with ecol2:
            sup_drill_sel = st.multiselect(
                L("Filtrar DSPs por Supervisor", "按主管筛选DSP网点"),
                sorted(df['supervisor'].dropna().unique()), key="sup_drill"
            )
        pontos_disponiveis_filtrados = (
            sorted(df[df['supervisor'].isin(sup_drill_sel)]['ponto'].dropna().unique())
            if sup_drill_sel else pontos_disponiveis
        )
    else:
        ecol1 = st.container()
        pontos_disponiveis_filtrados = pontos_disponiveis

    with ecol1:
        pontos_drill = st.multiselect(
            L("Escolha um ou mais DSPs", "选择一个或多个DSP网点"), pontos_disponiveis_filtrados,
            default=pontos_disponiveis_filtrados[:1] if pontos_disponiveis_filtrados else [],
        )

    ecol3, ecol4, ecol5 = st.columns(3)
    with ecol3:
        faixa_entreg = st.slider(L("Faixa de % Concluído no Prazo", "准时完成率区间"), 0, 100, (0, 100), key="faixa_entreg")
    with ecol4:
        volume_min_entreg = st.number_input(L("Volume mínimo", "最小件量"), min_value=0, value=0, step=5, key="vol_min_entreg")
    with ecol5:
        busca_entreg = st.text_input(L("Buscar entregador", "搜索配送员"), placeholder=L("parte do nome...", "输入部分姓名..."))

    if pontos_drill:
        df_drill = df[df['ponto'].isin(pontos_drill)].copy()
        # Pedidos "Recebido no ponto de entrega" / "Pacote armazenado" ainda não têm entregador
        # atribuído (chegaram no ponto, mas ninguém pegou pra rota ainda). Sem isso, o groupby
        # descarta essas linhas por completo — e elas somem da visão por entregador, do filtro
        # de status e da contagem de Backlog/Fora do Prazo aqui embaixo.
        df_drill['entregador'] = df_drill['entregador'].fillna(L('Sem entregador atribuído', '未分配配送员'))
        g_entreg = agrupar(df_drill, 'entregador').sort_values('pct_concluido', ascending=False)
        g_entreg = g_entreg[
            (g_entreg['pct_concluido'] >= faixa_entreg[0]) & (g_entreg['pct_concluido'] <= faixa_entreg[1])
        ]
        g_entreg = g_entreg[g_entreg['total'] >= volume_min_entreg]
        if busca_entreg:
            g_entreg = g_entreg[g_entreg['entregador'].str.contains(busca_entreg, case=False, na=False)]

        if g_entreg.empty:
            st.info(L("Nenhum entregador bate com esses filtros.", "没有符合筛选条件的配送员。"))
        else:
            st.markdown(
                montar_tabela_html(g_entreg, coluna_chave='entregador', rotulo_coluna=L('Entregador', '配送员')),
                unsafe_allow_html=True
            )

            # ============================================================
            # Lista de pedidos individuais: Fora do Prazo e Backlog
            # ============================================================
            entregadores_no_recorte = sorted(g_entreg['entregador'].dropna().unique())
            opcao_todos = L("Todos", "全部")
            with st.expander(f"🔍 {L('Ver pedidos Fora do Prazo e Backlog', '查看超时件和积压件明细')}"):
                entregador_foco = st.selectbox(
                    L("Focar em um entregador (opcional)", "聚焦某位配送员（可选）"),
                    [opcao_todos] + entregadores_no_recorte,
                    key="entregador_foco"
                )

                df_lista = df_drill[df_drill['entregador'].isin(entregadores_no_recorte)].copy()
                if entregador_foco != opcao_todos:
                    df_lista = df_lista[df_lista['entregador'] == entregador_foco]

                qtd_fora_lista = int((df_lista['classe'] == 'Fora do prazo').sum())
                qtd_backlog_lista = int((df_lista['classe'] == 'Backlog').sum())
                tab_fora, tab_backlog = st.tabs([
                    f"{L('Fora do Prazo', '超时件')} ({qtd_fora_lista})",
                    f"{L('Backlog', '积压件')} ({qtd_backlog_lista})",
                ])

                # Formata uma duração em dias decimais como "Xd Yh" — mais fácil de ler de
                # relance do que um número de dias corridos com casas decimais.
                def _formatar_duracao(dias_decimais: float) -> str:
                    total_horas = abs(dias_decimais) * 24
                    dias = int(total_horas // 24)
                    horas = int(total_horas % 24)
                    return f"{dias}d {horas}h" if dias > 0 else f"{horas}h"

                STATUS_EMOJI = {
                    'Em rota de entrega': '🚚',
                    'Recebido no ponto de entrega': '📥',
                    'Pacote armazenado': '🗄️',
                    'Pedido com anomalia': '⚠️',
                }

                def _altura_tabela(n_linhas: int) -> int:
                    # Cabeçalho + linhas, com teto de 480px (o resto rola dentro do quadro).
                    return min(38 + 35 * max(n_linhas, 1), 480)

                def _botoes_exportar_lista(df_show: pd.DataFrame, nome_base: str, key_prefix: str):
                    # Mesmo padrão de exportação da tabela de DSP (CSV ; + utf-8-sig, e Excel),
                    # aplicado aqui pra lista individual de pedidos (Fora do Prazo / Backlog).
                    col_a, col_b = st.columns(2)
                    with col_a:
                        _csv = df_show.to_csv(index=False, sep=';').encode('utf-8-sig')
                        st.download_button(
                            L("⬇️ Baixar lista (CSV)", "⬇️ 下载列表 (CSV)"),
                            data=_csv,
                            file_name=f"{nome_base}_{agora.strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key=f"csv_{key_prefix}",
                        )
                    with col_b:
                        _buf = io.BytesIO()
                        with pd.ExcelWriter(_buf, engine='openpyxl') as _writer:
                            df_show.to_excel(_writer, index=False, sheet_name=nome_base[:31])
                        st.download_button(
                            L("⬇️ Baixar lista (Excel)", "⬇️ 下载列表 (Excel)"),
                            data=_buf.getvalue(),
                            file_name=f"{nome_base}_{agora.strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"xlsx_{key_prefix}",
                        )

                with tab_fora:
                    df_fora_lista = df_lista[df_lista['classe'] == 'Fora do prazo'].copy()
                    if df_fora_lista.empty:
                        st.info(L("Nenhum pedido fora do prazo nesse recorte.", "该范围内没有超时订单。"))
                    else:
                        df_fora_lista['dias_atraso'] = (-df_fora_lista['diferenca_dias'])

                        def _atraso_com_severidade(dias):
                            emoji = "🔴" if dias >= 3 else "🟠" if dias >= 1 else "🟡"
                            return f"{emoji} {_formatar_duracao(dias)}"

                        df_fora_lista['atraso_show'] = df_fora_lista['dias_atraso'].apply(_atraso_com_severidade)
                        df_fora_show = df_fora_lista[
                            ['waybill', 'entregador', 'ponto', 'deadline', 'signature_dt', 'atraso_show', 'dias_atraso']
                        ].sort_values('dias_atraso', ascending=False).drop(columns='dias_atraso')
                        df_fora_show.columns = [
                            L('Waybill', '运单号'), L('Entregador', '配送员'), 'DSP',
                            L('Prazo', '时效'), L('Assinatura', '签收时间'), L('Atraso', '超时时长')
                        ]
                        st.dataframe(
                            df_fora_show, use_container_width=True, hide_index=True,
                            height=_altura_tabela(len(df_fora_show)),
                            column_config={
                                L('Prazo', '时效'): st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                                L('Assinatura', '签收时间'): st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                            },
                        )
                        st.caption(L(
                            "🔴 3+ dias de atraso · 🟠 1–3 dias · 🟡 menos de 1 dia.",
                            "🔴 超时3天以上 · 🟠 超时1–3天 · 🟡 超时不到1天。"
                        ))
                        _botoes_exportar_lista(df_fora_show, "fora_do_prazo", "fora")

                with tab_backlog:
                    df_backlog_lista = df_lista[df_lista['classe'] == 'Backlog'].copy()
                    if df_backlog_lista.empty:
                        st.info(L("Nenhum pedido em backlog nesse recorte.", "该范围内没有积压订单。"))
                    else:
                        df_backlog_lista['status_show'] = df_backlog_lista['status'].apply(traduzir_status)

                        # Filtro por status — permite isolar, por exemplo, só os pedidos
                        # "Recebido no ponto de entrega" (já na última milha) dentro do backlog.
                        status_disponiveis_backlog = sorted(df_backlog_lista['status_show'].dropna().unique())
                        status_sel_backlog = st.multiselect(
                            L("Filtrar por status", "按状态筛选"),
                            status_disponiveis_backlog, key="status_sel_backlog"
                        )
                        if status_sel_backlog:
                            df_backlog_lista = df_backlog_lista[df_backlog_lista['status_show'].isin(status_sel_backlog)]

                        if df_backlog_lista.empty:
                            st.info(L("Nenhum pedido bate com esse filtro de status.", "没有符合该状态筛选的订单。"))
                        else:
                            agora_ref = pd.Timestamp.now()
                            df_backlog_lista['delta_vencimento'] = df_backlog_lista['deadline'] - agora_ref
                            df_backlog_lista['dias_desde_vencimento'] = (
                                -df_backlog_lista['delta_vencimento'].dt.total_seconds() / 86400
                            )

                            def _tempo_vencimento_com_icone(delta):
                                dias_decimais = -delta.total_seconds() / 86400
                                duracao = _formatar_duracao(dias_decimais)
                                if dias_decimais <= 0:
                                    return L(f"🟢 Faltam {duracao}", f"🟢 还剩 {duracao}")
                                return L(f"🔴 Atrasado há {duracao}", f"🔴 已超时 {duracao}")

                            df_backlog_lista['status_icone'] = df_backlog_lista['status'].map(STATUS_EMOJI).fillna('•')
                            df_backlog_lista['status_show'] = df_backlog_lista['status_icone'] + ' ' + df_backlog_lista['status_show']
                            df_backlog_lista['tempo_vencimento'] = df_backlog_lista['delta_vencimento'].apply(
                                _tempo_vencimento_com_icone
                            )

                            df_backlog_show = df_backlog_lista[
                                ['waybill', 'entregador', 'ponto', 'status_show', 'deadline',
                                 'tempo_vencimento', 'dias_desde_vencimento']
                            ].sort_values('dias_desde_vencimento', ascending=False).drop(columns='dias_desde_vencimento')
                            df_backlog_show.columns = [
                                L('Waybill', '运单号'), L('Entregador', '配送员'), 'DSP', L('Status', '状态'),
                                L('Prazo', '时效'), L('Tempo até o Vencimento', '距到期时间'),
                            ]
                            st.dataframe(
                                df_backlog_show, use_container_width=True, hide_index=True,
                                height=_altura_tabela(len(df_backlog_show)),
                                column_config={
                                    L('Prazo', '时效'): st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                                },
                            )
                            st.caption(L(
                                "🟢 ainda dentro do prazo · 🔴 já venceu sem entrega. "
                                "🚚 em rota · 📥 recebido no ponto (ainda sem entregador) · "
                                "🗄️ pacote armazenado · ⚠️ com anomalia.",
                                "🟢 仍在时效内 · 🔴 已超期未签收。"
                                "🚚 派送途中 · 📥 已到达网点（尚未分配配送员） · 🗄️ 包裹已入库 · ⚠️ 异常件。"
                            ))
                            _botoes_exportar_lista(df_backlog_show, "backlog", "backlog")

            if len(g_entreg) > 1:
                pior = g_entreg.iloc[-1]
                melhor = g_entreg.iloc[0]
                if pior['total'] >= 5 and (pior['pct_concluido'] < melhor['pct_concluido'] - 15):
                    st.caption(L(
                        f"⚠️ Maior diferença no recorte: **{pior['entregador']}** está {melhor['pct_concluido'] - pior['pct_concluido']:.1f} "
                        f"p.p. abaixo de **{melhor['entregador']}** ({pior['total']:.0f} pedidos) — pode ser caso "
                        f"pontual, não necessariamente problema do ponto inteiro.",
                        f"⚠️ 本次筛选中差距最大：**{pior['entregador']}** 比 **{melhor['entregador']}** 低 "
                        f"{melhor['pct_concluido'] - pior['pct_concluido']:.1f} 个百分点（{pior['total']:.0f}笔订单）—— "
                        f"可能是个别情况，不一定是整个网点的问题。"
                    ))
    else:
        st.info(L("Escolha ao menos um DSP pra ver o detalhe por entregador.", "请至少选择一个DSP网点以查看配送员明细。"))