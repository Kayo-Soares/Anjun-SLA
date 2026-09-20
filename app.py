"""
Ponto de entrada do Indicador SLA - DSP (Anjun Express).

Roda de novo a cada troca de página (é assim que o st.navigation funciona:
o app.py sempre executa primeiro, e só depois a página escolhida). Por isso
tudo que é comum às duas páginas — idioma, upload dos arquivos, config da
página, CSS — fica aqui, e o resultado processado vai pro st.session_state
pras páginas (pages/sla.py, pages/cidade.py) lerem.
"""
import streamlit as st
import pandas as pd
from shared import (
    aplicar_estilo_global, L, processar_base, processar_mapa_supervisor,
)

st.set_page_config(
    page_title="DSP - Indicadores de Entrega / 配送指标 | Anjun Express",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilo_global()

# ============================================================
# SIDEBAR — comum às duas páginas
# ============================================================
with st.sidebar:
    _lang_escolha = st.selectbox("🌐 Idioma / 语言", ["Português", "中文"], key="lang_sel")
    st.session_state["lang"] = "zh" if _lang_escolha == "中文" else "pt"

    st.markdown('<div class="sb-logo">Anjun <span>Express</span></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sb-tagline">{L("Mais eficiência para a sua entrega.", "为您的配送提供更高效率。")}</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    uploaded_file = st.file_uploader(
        L("📤 Enviar base bruta (.xlsx)", "📤 上传原始数据 (.xlsx)"),
        type=["xlsx"],
        key="uploader_base",
        help=L(
            "Export padrão 'monitoramento_da_pontualidade_de_pedido' — nível de waybill individual.",
            "标准导出文件 'monitoramento_da_pontualidade_de_pedido' —— 运单级别数据。"
        )
    )
    mapa_file = st.file_uploader(
        L("🗂️ Mapa Ponto → Supervisor (opcional)", "🗂️ 网点→主管 对照表（可选）"),
        type=["xlsx", "csv"],
        key="uploader_mapa",
        help=L(
            "Planilha com 2 colunas: 'Ponto' e 'Supervisor'. Sem isso, a visão por supervisor fica desativada.",
            "包含两列的表格：'Ponto' 和 'Supervisor'。没有此文件，按主管查看的功能将无法使用。"
        )
    )

# ============================================================
# SEM ARQUIVO AINDA — mostra prompt e para (nenhuma página é acessível)
# ============================================================
if uploaded_file is None:
    st.markdown(f"""
    <div class="header-panel">
        <div>
            <div class="header-title">📊 {L("DSP — Indicadores de Entrega", "DSP — 配送指标")}</div>
            <div class="header-period">📅 {L("Envie a base pela barra lateral para calcular", "请在侧边栏上传数据以计算")}</div>
        </div>
        <div class="header-tagline">{L("Mais eficiência<br>para a sua entrega. 🚚", "为您的配送<br>提供更高效率。🚚")}</div>
    </div>
    """, unsafe_allow_html=True)
    st.info(L(
        "Nenhum arquivo enviado ainda. Use o campo na barra lateral esquerda.",
        "尚未上传文件。请使用左侧边栏的上传框。"
    ))
    st.stop()

# ============================================================
# PROCESSAMENTO — roda 1x por arquivo (cacheado), guarda em session_state
# ============================================================
try:
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    if st.session_state.get("file_id") != file_id:
        st.session_state["file_id"] = file_id
        st.session_state["agora_fixo"] = pd.Timestamp.now()
    agora = st.session_state["agora_fixo"]

    df = processar_base(uploaded_file)
    tem_entregador = 'entregador' in df.columns

    tem_supervisor = False
    mapa_supervisor = None
    if mapa_file is not None:
        mapa_supervisor = processar_mapa_supervisor(mapa_file)
        df = df.merge(mapa_supervisor, on='ponto', how='left')
        df['supervisor'] = df['supervisor'].fillna(L('Sem supervisor mapeado', '未匹配主管'))
        tem_supervisor = True
except ValueError as e:
    st.error(str(e))
    st.stop()

st.session_state["df"] = df
st.session_state["tem_entregador"] = tem_entregador
st.session_state["tem_supervisor"] = tem_supervisor
st.session_state["mapa_supervisor"] = mapa_supervisor
st.session_state["agora"] = agora

# ============================================================
# NAVEGAÇÃO — o seletor de páginas (equivalente ao antigo botão "SLA" fixo,
# agora com uma segunda opção real: "Análise por Cidade")
# ============================================================
pagina_resumo = st.Page("pages/resumo.py", title="Resumo Geral / 总体概览", icon="🏠", default=True)
pagina_sla = st.Page("pages/sla.py", title="SLA", icon="🕐")
pagina_cidade = st.Page("pages/cidade.py", title="Análise por Cidade / 按城市分析", icon="📍")
pagina_cliente = st.Page("pages/cliente.py", title="SLA por Cliente / 客户SLA", icon="👤")

pg = st.navigation([pagina_resumo, pagina_sla, pagina_cidade, pagina_cliente])
pg.run()