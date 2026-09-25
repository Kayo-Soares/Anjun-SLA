"""
Módulo compartilhado do Indicador SLA - DSP (Anjun Express).

Reúne tudo que as páginas (pages/sla.py, pages/cidade.py) e o app.py
precisam em comum: cores, CSS, idioma, leitura/processamento da base,
funções de gráfico e de tabela HTML. Nada aqui chama st.set_page_config
nem define widgets de sidebar — isso fica só no app.py (entrada única).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re
import zlib
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Pasta assets/ fica no mesmo nível deste arquivo (raiz do projeto), não no diretório
# de onde o streamlit é executado — resolver a partir de __file__ evita quebrar quando
# alguém roda "streamlit run app.py" de outro lugar.
PASTA_RAIZ = Path(__file__).parent
CAMINHO_LOGO = PASTA_RAIZ / "assets" / "anjun_logo.png"


@st.cache_data
def logo_anjun_base64():
    """Lê assets/anjun_logo.png e devolve como data URI, pra embutir num <img> no
    CSS/HTML da sidebar sem depender de servir arquivo estático à parte. Cacheado —
    só lê do disco 1x por sessão. Se o arquivo não existir (ex: alguém esqueceu de
    copiar a pasta assets/ junto), devolve None e quem chama cai no texto de volta."""
    if not CAMINHO_LOGO.exists():
        return None
    dados = CAMINHO_LOGO.read_bytes()
    return "data:image/png;base64," + base64.b64encode(dados).decode("ascii")

# ============================================================
# CORES / IDENTIDADE VISUAL
# ============================================================

VERDE_SIDEBAR = "#0B3D2E"      # verde escuro do menu lateral
VERDE_SIDEBAR_HOVER = "#124F3B"
VERDE = "#00A63E"              # verde de marca (badges, meta)
VERDE_TEXTO = "#0F7A3D"
VERDE_CLARO_BG = "#EAF6EE"     # fundo pastel do header/painel
VERDE_PILL_BG = "#DFF3E6"
LARANJA = "#F5A623"
LARANJA_TEXTO = "#B45309"
LARANJA_PILL_BG = "#FDEEDB"
VERMELHO = "#E5484D"
VERMELHO_TEXTO = "#B91C1C"
VERMELHO_PILL_BG = "#FDE2E1"
CINZA_ESCURO = "#374151"
CINZA_PILL_BG = "#E9ECEF"
FUNDO = "#F4F8F6"
CINZA_TEXTO = "#1F2937"

def aplicar_estilo_global():
    """Injeta o CSS global (sidebar, header, KPIs, tabelas). Chamar 1x,
    em app.py, logo após st.set_page_config — o app.py roda de novo a
    cada troca de página (padrão st.navigation), então o CSS continua
    valendo em qualquer página sem precisar reinjetar em cada uma."""
    st.markdown(f"""
<style>
    .stApp {{ background-color: {FUNDO}; }}

    /* ---- Sidebar (menu lateral verde escuro) ---- */
    [data-testid="stSidebar"] {{
        background-color: {VERDE_SIDEBAR};
    }}
    [data-testid="stSidebar"] * {{
        color: #E8F3ED !important;
    }}
    [data-testid="stSidebar"] .stFileUploader label,
    [data-testid="stSidebar"] .stFileUploader small {{
        color: #E8F3ED !important;
    }}
    [data-testid="stSidebar"] label p {{
        font-size: 14px !important; font-weight: 700 !important; color: white !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background-color: rgba(255,255,255,0.06) !important;
        border: 1.5px dashed rgba(0,166,62,0.55) !important;
        border-radius: 12px !important;
        padding: 10px !important;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: {VERDE} !important;
        background-color: rgba(255,255,255,0.09) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] svg {{
        fill: {VERDE} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small {{
        color: #CFE4D8 !important;
    }}
    /* ---- Chip do arquivo já enviado ---- */
    /* Sem isso, o texto herda a cor clara da regra geral da sidebar, mas o chip do
       Streamlit tem fundo claro por padrão — texto claro em fundo claro, ilegível.
       Aqui o chip vira um card escuro consistente com o resto do menu. */
    [data-testid="stSidebar"] [data-testid="stFileChips"] {{
        margin-top: 8px;
    }}
    [data-testid="stSidebar"] [data-testid="stFileChip"] {{
        background-color: rgba(255,255,255,0.10) !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        border-radius: 10px !important;
        padding: 10px 12px !important;
        align-items: center !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileChip"] svg {{
        fill: {VERDE} !important;
        opacity: 1 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileChipName"] {{
        color: #FFFFFF !important;
        font-size: 12.5px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        line-height: 1.4 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileChip"] small {{
        color: #A9C9BB !important;
        font-size: 11px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileChipDeleteBtn"] button {{
        color: #CFE4D8 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileChipDeleteBtn"] svg {{
        fill: #CFE4D8 !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {{
        background-color: {VERDE} !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }}
    /* ---- Cartão em volta de cada bloco de upload, pra separar visualmente ---- */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background-color: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px 14px 10px 14px;
        margin-bottom: 14px;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] label p {{
        font-size: 13px !important;
    }}

    /* ---- Seletor de Idioma — mesmo tratamento de "card" dos uploads acima ---- */
    /* Sem isso, o combobox usa o estilo padrão do Streamlit: uma caixa quase
       branca meio transparente, com texto de baixo contraste — destoa dos outros
       controles da sidebar, que são cards escuros translúcidos com texto branco. */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"] {{
        background-color: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        border-radius: 10px !important;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"]:hover,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="group"]:focus-within {{
        border-color: {VERDE} !important;
        background-color: rgba(255,255,255,0.10) !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] input[role="combobox"] {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
        background-color: transparent !important;
    }}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] button svg {{
        fill: {VERDE} !important;
    }}
    /* O menu suspenso (lista de opções) é renderizado pelo Streamlit fora da
       sidebar, direto no <body> — por isso não dá pra escopar com
       [data-testid="stSidebar"] aqui, precisa ser global. Como ele abre sobre
       fundo claro (o painel principal), mantém texto escuro pra legibilidade;
       só o item selecionado/em foco ganha o verde de marca. */
    div[role="listbox"] {{
        border-radius: 10px !important;
        box-shadow: 0 8px 24px rgba(11,61,46,0.18) !important;
        border: 1px solid #E5E7EB !important;
        overflow: hidden;
    }}
    div[role="listbox"] div[role="option"] {{
        color: {CINZA_TEXTO} !important;
        font-size: 13.5px !important;
    }}
    div[role="listbox"] div[role="option"][data-focused="true"],
    div[role="listbox"] div[role="option"][aria-selected="true"] {{
        background-color: {VERDE_PILL_BG} !important;
        color: {VERDE_TEXTO} !important;
        font-weight: 700 !important;
    }}
    .sb-logo {{
        font-size: 22px; font-weight: 800; color: white; padding: 6px 0 2px 0;
    }}
    .sb-logo span {{ color: {VERDE}; }}
    /* ---- Card branco com a logo oficial da Anjun ---- */
    /* A logo tem fundo branco sólido (sem transparência); em vez de jogar direto no
       verde escuro da sidebar (o que criaria uma borda dura ao redor da imagem),
       ela ganha um card branco arredondado — o mesmo tipo de "badge" que qualquer
       app usa pra logo em sidebar escura. */
    .sb-logo-card {{
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 14px 16px;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 4px;
    }}
    .sb-logo-card img {{
        max-width: 100%; height: auto; display: block;
    }}
    .sb-tagline {{ font-size: 11px; color: #A9C9BB; margin-bottom: 18px; }}
    .sb-section-label {{
        font-size: 11px; font-weight: 700; color: #7FA592; text-transform: uppercase;
        letter-spacing: 0.06em; margin: 4px 0 10px 0;
    }}
    .sb-nav-item {{
        display: flex; align-items: center; gap: 10px;
        padding: 9px 12px; border-radius: 8px; margin-bottom: 4px;
        font-size: 14px; color: #CFE4D8;
    }}
    .sb-nav-item.active {{
        background-color: {VERDE}; color: white; font-weight: 600;
    }}
    .sb-footer {{
        margin-top: 20px; padding-top: 14px; border-top: 1px solid #1D5340;
        font-size: 12px; color: #A9C9BB;
    }}
    .sb-status-dot {{
        height: 8px; width: 8px; background-color: {VERDE}; border-radius: 50%;
        display: inline-block; margin-right: 6px;
    }}
    .sb-search {{
        background-color: rgba(255,255,255,0.07);
        border: 1px solid #1D5340;
        border-radius: 8px;
        padding: 9px 12px;
        font-size: 13px;
        color: #7FA592;
        margin-bottom: 16px;
    }}

    /* ---- Painel de topo (header claro) ---- */
    .header-panel {{
        background-color: {VERDE_CLARO_BG};
        border-radius: 14px;
        padding: 18px 26px;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 22px;
    }}
    .header-title {{ font-size: 24px; font-weight: 800; color: {VERDE_SIDEBAR}; }}
    .header-period {{ font-size: 13px; color: #4B6357; margin-top: 4px; }}
    .header-tagline {{ font-size: 13px; color: #4B6357; text-align: right; line-height: 1.3; }}

    /* ---- KPI cards com badge de ícone circular (estilo gerencial) ---- */
    .kpi-card {{
        background-color: white;
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #E3EBE6;
        border-left: 4px solid var(--kpi-accent, {VERDE});
        display: flex; align-items: center; gap: 14px;
        box-shadow: 0 2px 6px rgba(15,45,30,0.06);
        transition: box-shadow 0.15s ease;
    }}
    .kpi-card:hover {{ box-shadow: 0 4px 10px rgba(15,45,30,0.1); }}
    .kpi-icon {{
        min-width: 44px; height: 44px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 19px; flex-shrink: 0;
    }}
    .kpi-label {{
        font-size: 11.5px; color: #6B7280; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.04em;
    }}
    .kpi-value {{ font-size: 28px; font-weight: 800; color: {CINZA_TEXTO}; margin-top: 2px; line-height: 1.1; }}

    /* ---- Tabela estilo DSP ---- */
    .dps-table {{ width: 100%; border-collapse: collapse; font-size: 15.5px;
                  border-radius: 10px; overflow: hidden; }}
    .dps-table thead tr {{ background-color: {VERDE_SIDEBAR}; }}
    .dps-table thead th {{
        color: white; text-align: left; padding: 12px 16px; font-weight: 600;
    }}
    .dps-table tbody tr:nth-child(even) {{ background-color: #F2F7F4; }}
    .dps-table tbody tr:nth-child(odd) {{ background-color: white; }}
    .dps-table tbody td {{ padding: 11px 16px; color: {CINZA_TEXTO}; }}
    .dps-table tfoot tr {{ background-color: {VERDE_SIDEBAR}; font-weight: 700; }}
    .dps-table tfoot td {{ padding: 13px 16px; color: white; }}
    .sla-pill {{
        display: inline-block; padding: 4px 14px; border-radius: 20px; font-weight: 700;
        font-size: 15px;
    }}

    .alert-card {{
        background-color: {VERMELHO_PILL_BG};
        border: 1px solid #FCA5A5;
        border-radius: 12px;
        padding: 16px 20px;
    }}
    .alert-title {{ color: {VERMELHO}; font-weight: 700; font-size: 14px; }}
    h1, h2, h3, h4 {{ color: {CINZA_TEXTO}; }}
</style>
    """, unsafe_allow_html=True)

# ============================================================
# IDIOMA — helper L(pt, zh): retorna o texto no idioma ativo.
# `lang` é definido no bloco da sidebar (primeira coisa renderizada), então já
# está disponível quando o resto do script (que roda depois) chama L().
# ============================================================
def L(pt: str, zh: str) -> str:
    return zh if st.session_state.get("lang") == "zh" else pt


STATUS_ZH = {
    "Em rota de entrega": "派送途中",
    "Pacote armazenado": "包裹已入库",
    "Recebido no ponto de entrega": "已到达派送网点",
    "Pedido com anomalia": "异常件",
    "Pedido entregue": "已签收",
}

MOTIVO_ZH = {
    "Perda confirmada - Aguardando indenização": "确认丢失 - 等待赔偿",
}


def traduzir_status(s: str) -> str:
    if st.session_state.get("lang") == "zh":
        return STATUS_ZH.get(s, s)
    return s


def traduzir_motivo(s: str) -> str:
    if st.session_state.get("lang") == "zh":
        return MOTIVO_ZH.get(s, s)
    return s


# ============================================================
# MAPEAMENTO DE COLUNAS (export bruto Anjun - bilíngue CN/PT)
# ============================================================
COL_MAP = {
    '运单号(Número do Waybill)': 'waybill',
    '运单状态(Status do Pacote)': 'status',
    '问题件原因(Motivo da Ocorrência)': 'motivo_ocorrencia',
    '收件人州(Estado do destinatário)': 'estado_dest',
    '收件人城市(Cidade do destinatário)': 'cidade_dest',
    '大区(Região)': 'regiao',
    '预派送网点(Ponto de Pré-entrega)': 'ponto_pre_entrega',
    '实际入库网点(Ponto de entrada)': 'ponto_entrada',
    '实际派送网点(Ponto de entrega)': 'ponto_entrega',
    '派送员(entregador)': 'entregador',
    '商户名称(Nome do Cliente Merchant)': 'merchant',
    '客户名称(Nome do cliente)': 'cliente',
    '签收时间(Tempo de Assinatura)': 'signature_dt',
    '理应送达时间(Horário em que deve ser entregue)': 'deadline',
}

REQUIRED_KEYS = ['status', 'signature_dt', 'deadline']


# O nome do arquivo bruto exportado carrega o horário em que a extração foi feita,
# no padrão: monitoramento_da_pontualidade_de_pedido-YYYYMMDDHHMMSSmmm-XXXXXX.xlsx
def extrair_datetime_do_nome(nome_arquivo: str):
    """Tenta extrair o horário de extração embutido no nome do arquivo bruto.
    Retorna um pd.Timestamp ou None se o padrão não bater."""
    if not nome_arquivo:
        return None
    m = re.search(r'-(\d{17})-', nome_arquivo)
    if not m:
        return None
    digitos = m.group(1)
    try:
        ano, mes, dia = int(digitos[0:4]), int(digitos[4:6]), int(digitos[6:8])
        hora, minuto, seg = int(digitos[8:10]), int(digitos[10:12]), int(digitos[12:14])
        ms = int(digitos[14:17])
        return pd.Timestamp(ano, mes, dia, hora, minuto, seg, ms * 1000)
    except (ValueError, OverflowError):
        return None


# Cacheado por conteúdo do arquivo: a classificação não depende mais do horário de
# processamento — "Fora do Prazo" só existe depois que o pedido é entregue (fato
# consumado). Backlog continua sendo Backlog até a entrega acontecer, mesmo que o
# prazo já tenha vencido.
@st.cache_data(show_spinner=False)
def processar_base(file_bytes) -> pd.DataFrame:
    df = pd.read_excel(file_bytes)
    df = df.rename(columns=COL_MAP)

    faltando = [c for c in ['ponto_entrada', 'ponto_pre_entrega', 'signature_dt', 'deadline']
                if c not in df.columns]
    if faltando:
        raise ValueError(
            "A planilha não tem as colunas esperadas: " + ", ".join(faltando) +
            ". Confirme se é o export padrão de monitoramento de pontualidade."
        )

    df['deadline'] = pd.to_datetime(df['deadline'], errors='coerce')
    df['signature_dt'] = pd.to_datetime(df['signature_dt'], errors='coerce')
    df['delivered'] = df['signature_dt'].notna()

    # ---- Lógica das 3 colunas (calculada do zero) ----
    df['diferenca_dias'] = (df['deadline'] - df['signature_dt']).dt.total_seconds() / 86400

    def classificar(row):
        if not row['delivered']:
            return 'Backlog'
        elif row['diferenca_dias'] < 0:
            return 'Fora do prazo'
        else:
            return 'No prazo'

    df['classe'] = df.apply(classificar, axis=1)
    df['ponto'] = df['ponto_pre_entrega']

    return df


@st.cache_data(show_spinner=False)
def processar_mapa_supervisor(mapa_bytes) -> pd.DataFrame:
    """Lê o mapa Ponto -> Supervisor. Aceita .xlsx ou .csv com colunas 'Ponto' e 'Supervisor'."""
    nome = getattr(mapa_bytes, "name", "")
    if nome.lower().endswith(".csv"):
        mapa = pd.read_csv(mapa_bytes, sep=None, engine="python")
    else:
        mapa = pd.read_excel(mapa_bytes)

    mapa.columns = [str(c).strip().lower() for c in mapa.columns]
    col_ponto = next((c for c in mapa.columns if c in ("ponto", "dsp", "ponto (dsp)")), None)
    col_sup = next((c for c in mapa.columns if c in ("supervisor", "supervisora")), None)
    if col_ponto is None or col_sup is None:
        raise ValueError(
            "O mapa precisa ter uma coluna 'Ponto' e uma coluna 'Supervisor'. "
            f"Colunas encontradas: {list(mapa.columns)}"
        )

    mapa = mapa[[col_ponto, col_sup]].copy()
    mapa.columns = ['ponto', 'supervisor']
    mapa['ponto'] = mapa['ponto'].astype(str).str.strip()
    mapa['supervisor'] = mapa['supervisor'].astype(str).str.strip()
    return mapa.drop_duplicates(subset='ponto', keep='last')


FONTE_GRAFICO = dict(family="Segoe UI, Helvetica, Arial, sans-serif", color=CINZA_TEXTO, size=13)

# Espaçador de superfície entre marcas encostadas (barras vizinhas, fatias de rosca,
# segmentos empilhados) — 2px na cor do FUNDO da página (não branco): os gráficos
# agora têm fundo transparente (herdam o verde-claro da página, sem "cartão branco"
# atrás), então o filete de separação precisa ser dessa mesma cor pra continuar
# funcionando como respiro, e não sobrar como tracinho branco destoando do fundo.
GAP_SUPERFICIE = dict(color=FUNDO, width=2)
# Grade um tom abaixo do FUNDO — contra branco puro o cinza-claro antigo (#EEF2EF)
# aparecia; contra o FUNDO verde-claro ele quase sumia, por isso um tom próprio aqui.
GRADE_GRAFICO = "#E3EBE7"


def estilo_barra(fig, altura=340, y_titulo=""):
    """Barra única por categoria (% Concluído no Prazo por Estado/Supervisor).
    Ponta arredondada, grade em hairline sólida, rótulo só na ponta da barra."""
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        marker=dict(cornerradius=6, line=GAP_SUPERFICIE),
        selector=dict(type="bar"),
    )
    fig.update_layout(
        font=FONTE_GRAFICO,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(
            range=[0, 112], title=y_titulo, gridcolor=GRADE_GRAFICO, zeroline=False,
            dtick=20, ticksuffix="%",
        ),
        xaxis=dict(title="", showgrid=False),
        height=altura, margin=dict(t=28, b=20, l=10, r=10),
        bargap=0.42,
        hoverlabel=dict(bgcolor="white", bordercolor="#E5E7EB", font=FONTE_GRAFICO),
    )
    return fig


def estilo_barra_contagem(fig, altura=340, y_titulo=""):
    """Estilo pra gráfico de barra (empilhada ou não) com CONTAGEM (não %) — sem range
    fixo 0-108, com legenda no topo e barras por hora/faixa. Cantos arredondados e
    um filete branco de 2px separa segmentos empilhados e barras vizinhas."""
    # selector=dict(type='bar') é essencial aqui: esse estilo é usado em figuras que
    # também têm um trace go.Scatter (só pro rótulo do total empilhado) — Scatter não
    # tem a propriedade marker.cornerradius, e aplicar em todos os traces quebra o gráfico.
    fig.update_traces(marker=dict(cornerradius=4, line=GAP_SUPERFICIE), selector=dict(type="bar"))
    fig.update_layout(
        font=FONTE_GRAFICO,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title=y_titulo, gridcolor=GRADE_GRAFICO, zeroline=False, rangemode="tozero"),
        xaxis=dict(title="", showgrid=False),
        height=altura, margin=dict(t=40, b=20, l=10, r=10),
        barmode="stack", bargap=0.32,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white", bordercolor="#E5E7EB", font=FONTE_GRAFICO),
    )
    return fig


def estilo_donut(fig, total_label: str, altura=320):
    """Rosca com filete de 2px na cor do fundo entre fatias (no lugar de contorno),
    hover com valor absoluto + %, número total grande no centro."""
    fig.update_traces(
        textposition="inside", textinfo="percent",
        marker=dict(line=GAP_SUPERFICIE),
        hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
    )
    fig.update_layout(
        font=FONTE_GRAFICO,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
        height=altura, margin=dict(t=10, b=10, l=10, r=10),
        annotations=[dict(text=total_label, x=0.5, y=0.5, font=dict(size=20, color=CINZA_TEXTO, family=FONTE_GRAFICO["family"]), showarrow=False)],
        hoverlabel=dict(bgcolor="white", bordercolor="#E5E7EB", font=FONTE_GRAFICO),
    )
    return fig


def cor_sla(pct: float) -> str:
    """Cor de status por faixa de performance (mesmos cortes do sla_pill: 92% / 80%).
    Usada pra colorir barras de % Concluído no Prazo por status, não por marca fixa —
    assim quem está abaixo da meta salta aos olhos sem precisar ler o número."""
    if pct >= 92:
        return VERDE
    elif pct >= 80:
        return LARANJA
    return VERMELHO


# Cor fixa por status conhecido — identidade, não ranking. Se a cor fosse escolhida
# pela posição no ranking de quantidade (como era antes), o mesmo status podia trocar
# de cor só porque outro DSP tem uma composição de backlog diferente, o que confunde
# quem acompanha o mesmo status ao longo do tempo/filtro.
STATUS_COR_FIXA = {
    "Em rota de entrega": LARANJA,
    "Recebido no ponto de entrega": "#4C6EF5",
    "Pacote armazenado": CINZA_ESCURO,
    "Pedido com anomalia": VERMELHO,
}


def cor_status(status: str) -> str:
    """Cor estável por status: usa STATUS_COR_FIXA pros 4 status conhecidos: para
    qualquer status novo/raro, deriva um índice determinístico (hash) dentro do
    resto da paleta — mesma string sempre cai na mesma cor, em qualquer filtro."""
    if status in STATUS_COR_FIXA:
        return STATUS_COR_FIXA[status]
    paleta_extra = [c for c in PALETA_STATUS if c not in STATUS_COR_FIXA.values()]
    idx = zlib.crc32(str(status).encode("utf-8")) % len(paleta_extra)
    return paleta_extra[idx]


def calc_sla(no_prazo: int, fora: int) -> float:
    denom = no_prazo + fora
    return (no_prazo / denom * 100) if denom > 0 else 0.0


def agrupar(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    g = df.groupby(coluna)['classe'].value_counts().unstack(fill_value=0)
    for c in ['No prazo', 'Fora do prazo', 'Backlog']:
        if c not in g.columns:
            g[c] = 0
    g['total'] = g[['No prazo', 'Fora do prazo', 'Backlog']].sum(axis=1)
    g['sla_real'] = g.apply(lambda r: calc_sla(r['No prazo'], r['Fora do prazo']), axis=1)
    g['pct_concluido'] = (g['No prazo'] / g['total'] * 100).fillna(0)
    g['atraso_pct'] = (g['Fora do prazo'] / g['total'] * 100).fillna(0)
    return g.reset_index()


def render_html(html: str):
    """Renderiza HTML multi-linha (tabelas, cards) de forma segura.

    O parser de Markdown do Streamlit trata qualquer linha com 4+ espaços de
    recuo (precedida de linha em branco) como BLOCO DE CÓDIGO — nesse caso ele
    escapa o HTML e mostra como texto cru em vez de renderizar, mesmo com
    unsafe_allow_html=True. Como nossas tabelas são montadas com f-strings
    indentadas (pra ficar legível no código), tiramos o recuo linha a linha
    antes de mandar pro markdown, sem mudar a estrutura das tags.
    """
    st.markdown("\n".join(linha.lstrip() for linha in html.split("\n")), unsafe_allow_html=True)


# Paleta ampliada pra "Composição do Backlog" — bases com muitos status (ex: a
# exportação completa do diretor, com 11+ categorias) esgotavam a paleta antiga
# de 5 cores e repetiam cor pra status diferentes, confundindo o gráfico.
PALETA_STATUS = [
    LARANJA, CINZA_ESCURO, VERMELHO, "#8FA89B", "#C9A227",
    "#4C6EF5", "#845EF7", "#15AABF", "#F06595", "#94D82D",
    "#FF922B", "#20C997",
]
COR_OUTROS_STATUS = "#ADB5BD"
MAX_FATIAS_DONUT_STATUS = 7  # além disso, agrupa o restante em "Outros" só no gráfico


def sla_pill(valor_exibido: float, atraso_pct: float = None) -> str:
    if valor_exibido >= 92:
        bg, cor = VERDE_PILL_BG, VERDE_TEXTO
    elif valor_exibido >= 80:
        bg, cor = LARANJA_PILL_BG, LARANJA_TEXTO
    else:
        bg, cor = VERMELHO_PILL_BG, VERMELHO_TEXTO
    return f'<span class="sla-pill" style="background-color:{bg}; color:{cor};">{valor_exibido:.2f}%</span>'


def montar_tabela_html(tabela: pd.DataFrame, coluna_chave: str = 'ponto', rotulo_coluna: str = None) -> str:
    if rotulo_coluna is None:
        rotulo_coluna = L("DSP", "DSP")
    linhas = ""
    for _, r in tabela.iterrows():
        linhas += f"""
        <tr>
            <td><b>{r[coluna_chave]}</b></td>
            <td>{int(r['Backlog'])}</td>
            <td>{int(r['Fora do prazo'])}</td>
            <td>{int(r['No prazo'])}</td>
            <td>{int(r['total'])}</td>
            <td>{sla_pill(r['pct_concluido'])}</td>
        </tr>"""
    tot_backlog = int(tabela['Backlog'].sum())
    tot_fora = int(tabela['Fora do prazo'].sum())
    tot_no = int(tabela['No prazo'].sum())
    tot_geral = int(tabela['total'].sum())
    tot_sla = (tot_no / tot_geral * 100) if tot_geral > 0 else 0.0
    col_backlog = L("Backlog", "积压件")
    col_fora = L("Fora do Prazo", "超时件")
    col_no = L("No Prazo", "准时件")
    col_total = L("Total Geral", "总计")
    col_sla = L("SLA", "SLA")
    return f"""
    <table class="dps-table">
        <thead>
            <tr>
                <th>{rotulo_coluna}</th><th>{col_backlog}</th><th>{col_fora}</th>
                <th>{col_no}</th><th>{col_total}</th><th>{col_sla}</th>
            </tr>
        </thead>
        <tbody>{linhas}
        </tbody>
        <tfoot>
            <tr>
                <td>{col_total}</td><td>{tot_backlog}</td><td>{tot_fora}</td>
                <td>{tot_no}</td><td>{tot_geral}</td>
                <td>{sla_pill(tot_sla)}</td>
            </tr>
        </tfoot>
    </table>
    """


def agrupar_cidade(df: pd.DataFrame, tem_entregador: bool, coluna: str = 'cidade_dest') -> pd.DataFrame:
    """Agrupa por cidade dentro de um recorte (normalmente já filtrado por DSP) e,
    se a base tiver a coluna de entregador, soma quantos entregadores DISTINTOS
    atenderam cada cidade nesse recorte."""
    g = agrupar(df, coluna)
    if tem_entregador:
        qtd_entreg = df.groupby(coluna)['entregador'].nunique().rename('qtd_entregadores')
        g = g.merge(qtd_entreg, on=coluna, how='left')
        g['qtd_entregadores'] = g['qtd_entregadores'].fillna(0).astype(int)
    else:
        g['qtd_entregadores'] = None
    return g


def montar_tabela_cidade_html(tabela: pd.DataFrame, mostrar_entregadores: bool = True) -> str:
    linhas = ""
    for _, r in tabela.iterrows():
        col_entreg_td = f"<td>{int(r['qtd_entregadores'])}</td>" if mostrar_entregadores else ""
        linhas += f"""
        <tr>
            <td><b>{r['cidade_dest']}</b></td>
            <td>{int(r['Backlog'])}</td>
            <td>{int(r['Fora do prazo'])}</td>
            <td>{int(r['No prazo'])}</td>
            <td>{int(r['total'])}</td>
            {col_entreg_td}
            <td>{sla_pill(r['pct_concluido'])}</td>
        </tr>"""
    tot_backlog = int(tabela['Backlog'].sum())
    tot_fora = int(tabela['Fora do prazo'].sum())
    tot_no = int(tabela['No prazo'].sum())
    tot_geral = int(tabela['total'].sum())
    tot_sla = (tot_no / tot_geral * 100) if tot_geral > 0 else 0.0
    col_cidade = L("Cidade", "城市")
    col_backlog = L("Backlog", "积压件")
    col_fora = L("Fora do Prazo", "超时件")
    col_no = L("No Prazo", "准时件")
    col_total = L("Total Geral", "总计")
    col_entreg_hdr = f"<th>{L('Entregadores', '配送员数')}</th>" if mostrar_entregadores else ""
    col_entreg_tot = "<td>—</td>" if mostrar_entregadores else ""
    col_sla = L("SLA", "SLA")
    return f"""
    <table class="dps-table">
        <thead>
            <tr>
                <th>{col_cidade}</th><th>{col_backlog}</th><th>{col_fora}</th>
                <th>{col_no}</th><th>{col_total}</th>{col_entreg_hdr}<th>{col_sla}</th>
            </tr>
        </thead>
        <tbody>{linhas}
        </tbody>
        <tfoot>
            <tr>
                <td>{col_total}</td><td>{tot_backlog}</td><td>{tot_fora}</td>
                <td>{tot_no}</td><td>{tot_geral}</td>{col_entreg_tot}
                <td>{sla_pill(tot_sla)}</td>
            </tr>
        </tfoot>
    </table>
    """


def exportar_excel_bytes(df: pd.DataFrame, nome_aba: str = "Dados") -> bytes:
    """Serializa um DataFrame pra bytes de .xlsx, prontos pro st.download_button."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=nome_aba[:31])  # Excel limita aba a 31 caracteres
    return buf.getvalue()


def _carregar_fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    import os
    windir = os.environ.get("WINDIR", "C:\\Windows")
    candidatos_zh = (
        [f"{windir}\\Fonts\\msyhbd.ttc", f"{windir}\\Fonts\\simhei.ttf", "msyhbd.ttc", "simhei.ttf",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
         "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
         "/System/Library/Fonts/Supplemental/Songti.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if negrito else
        [f"{windir}\\Fonts\\msyh.ttc", f"{windir}\\Fonts\\simsun.ttc", "msyh.ttc", "simsun.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
         "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
         "/System/Library/Fonts/Supplemental/Songti.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    candidatos_latin = (
        [f"{windir}\\Fonts\\arialbd.ttf", "arialbd.ttf", "Arial Bold.ttf",
         "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if negrito else
        [f"{windir}\\Fonts\\arial.ttf", "arial.ttf", "Arial.ttf",
         "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    # Em zh, tenta fontes com glifos CJK primeiro (Arial não desenha caracteres chineses)
    candidatos = candidatos_zh + candidatos_latin if st.session_state.get("lang") == "zh" else candidatos_latin + candidatos_zh
    for nome in candidatos:
        try:
            return ImageFont.truetype(nome, tamanho)
        except Exception:
            continue
    # Última tentativa: fonte padrão do PIL, mas escalável (Pillow >= 10.1) em vez da
    # bitmap minúscula de tamanho fixo — assim, mesmo no pior caso, o texto não fica
    # desproporcional ao resto do desenho.
    try:
        return ImageFont.load_default(size=tamanho)
    except TypeError:
        return ImageFont.load_default()


def _hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _cor_pill_rgb(valor: float):
    """(fundo pastel, cor forte) do status de SLA — mesmos cortes do dashboard."""
    if valor >= 92:
        return _hex_rgb(VERDE_PILL_BG), _hex_rgb(VERDE_TEXTO)
    elif valor >= 80:
        return _hex_rgb(LARANJA_PILL_BG), _hex_rgb(LARANJA_TEXTO)
    return _hex_rgb(VERMELHO_PILL_BG), _hex_rgb(VERMELHO_TEXTO)


def _cor_barra_rgb(valor: float):
    if valor >= 92:
        return _hex_rgb(VERDE)
    elif valor >= 80:
        return _hex_rgb(LARANJA)
    return _hex_rgb(VERMELHO)


def _fmt_int(v) -> str:
    return f"{int(v):,}".replace(",", ".")


def _fmt_pct(v: float, casas: int = 2) -> str:
    return f"{v:.{casas}f}%".replace(".", ",")


def _texto(draw, xy, texto, fonte, cor, ancora="la"):
    """Wrapper de draw.text com âncora (la = esquerda/topo, ra = direita/topo,
    lm/rm/mm = centro vertical). Âncora evita calcular largura na mão."""
    draw.text(xy, texto, font=fonte, fill=cor, anchor=ancora)


# Meta usada no relatório (mesma linha de referência dos gráficos do dashboard)
META_SLA_IMG = 92.0


def _desenhar_tabela_imagem(draw: ImageDraw.ImageDraw, x: int, y: int, largura: int,
                             tabela: pd.DataFrame, coluna_chave: str, rotulo_coluna: str,
                             fontes: dict, s: int) -> int:
    """Tabela em estilo dashboard: ranking, números alinhados à direita e uma
    barra de SLA por linha com marcador da meta. Retorna o y final."""
    VERDE_ESC = _hex_rgb(VERDE_SIDEBAR)
    BRANCO = (255, 255, 255)
    TXT = _hex_rgb(CINZA_TEXTO)
    TXT_SUAVE = (107, 114, 128)
    LINHA = (229, 236, 232)
    ZEBRA = (248, 251, 249)
    TRILHO = (234, 240, 236)

    h_cab = 40 * s
    h_lin = 42 * s
    pad = 16 * s

    # Colunas: [rótulo, fração da largura, alinhamento]
    specs = [
        ("#",                              0.05, "c"),
        (rotulo_coluna,                    0.19, "l"),
        (L("Total", "总计"),               0.10, "r"),
        (L("No Prazo", "准时件"),          0.11, "r"),
        (L("Fora do Prazo", "超时件"),     0.12, "r"),
        (L("Backlog", "积压件"),           0.10, "r"),
        (L("SLA", "SLA"),                  0.33, "sla"),
    ]
    xs, cx = [], x
    for _, frac, _a in specs:
        w = int(largura * frac)
        xs.append((cx, cx + w))
        cx += w
    xs[-1] = (xs[-1][0], x + largura)

    def escrever_celula(i, texto, yc, fonte, cor):
        x0, x1 = xs[i]
        alin = specs[i][2]
        if alin == "l":
            _texto(draw, (x0 + pad, yc), texto, fonte, cor, "lm")
        elif alin == "r":
            _texto(draw, (x1 - pad, yc), texto, fonte, cor, "rm")
        else:
            _texto(draw, ((x0 + x1) // 2, yc), texto, fonte, cor, "mm")

    def desenhar_sla(valor, yc, destaque_total=False):
        x0, x1 = xs[-1]
        largura_pct = 74 * s
        trilho_x0 = x0 + pad
        trilho_x1 = x1 - pad - largura_pct - 10 * s
        alt = 10 * s
        ty0, ty1 = yc - alt // 2, yc + alt // 2
        cor_trilho = (255, 255, 255, 60) if destaque_total else TRILHO
        draw.rounded_rectangle([trilho_x0, ty0, trilho_x1, ty1], radius=alt // 2,
                               fill=(33, 90, 72) if destaque_total else cor_trilho)
        preench = trilho_x0 + int((trilho_x1 - trilho_x0) * max(0.0, min(valor, 100.0)) / 100)
        if preench > trilho_x0 + alt:
            cor = BRANCO if destaque_total else _cor_barra_rgb(valor)
            draw.rounded_rectangle([trilho_x0, ty0, preench, ty1], radius=alt // 2, fill=cor)
        # marcador da meta (tracinho vertical)
        mx = trilho_x0 + int((trilho_x1 - trilho_x0) * META_SLA_IMG / 100)
        draw.line([mx, ty0 - 5 * s, mx, ty1 + 5 * s],
                  fill=(190, 220, 205) if destaque_total else (55, 65, 81), width=max(2, s))
        # pílula com o valor
        px1 = x1 - pad
        px0 = px1 - largura_pct
        ph = 26 * s
        if destaque_total:
            bg, fg = BRANCO, VERDE_ESC
        else:
            bg, fg = _cor_pill_rgb(valor)
        draw.rounded_rectangle([px0, yc - ph // 2, px1, yc + ph // 2], radius=ph // 2, fill=bg)
        _texto(draw, ((px0 + px1) // 2, yc), _fmt_pct(valor), fontes["bold_p"], fg, "mm")

    # ---- Cabeçalho ----
    draw.rounded_rectangle([x, y, x + largura, y + h_cab], radius=10 * s, fill=VERDE_ESC)
    draw.rectangle([x, y + h_cab // 2, x + largura, y + h_cab], fill=VERDE_ESC)  # só cantos de cima arredondados
    for i, (rot, _f, _a) in enumerate(specs):
        escrever_celula(i, rot, y + h_cab // 2, fontes["bold_p"], BRANCO)
    y += h_cab

    # ---- Linhas ----
    tabela_ordenada = tabela.sort_values('pct_concluido', ascending=False)
    for n, (_, r) in enumerate(tabela_ordenada.iterrows(), start=1):
        bg = ZEBRA if n % 2 == 0 else BRANCO
        draw.rectangle([x, y, x + largura, y + h_lin], fill=bg)
        draw.line([x, y + h_lin - 1, x + largura, y + h_lin - 1], fill=LINHA, width=max(1, s // 2))
        yc = y + h_lin // 2
        escrever_celula(0, str(n), yc, fontes["normal_p"], TXT_SUAVE)
        escrever_celula(1, str(r[coluna_chave]), yc, fontes["bold"], TXT)
        escrever_celula(2, _fmt_int(r['total']), yc, fontes["normal"], TXT)
        escrever_celula(3, _fmt_int(r['No prazo']), yc, fontes["normal"], TXT)
        fora_v = int(r['Fora do prazo'])
        escrever_celula(4, _fmt_int(fora_v), yc, fontes["normal"],
                        _hex_rgb(VERMELHO_TEXTO) if fora_v > 0 else TXT_SUAVE)
        bl_v = int(r['Backlog'])
        escrever_celula(5, _fmt_int(bl_v), yc, fontes["normal"],
                        _hex_rgb(LARANJA_TEXTO) if bl_v > 0 else TXT_SUAVE)
        desenhar_sla(float(r['pct_concluido']), yc)
        y += h_lin

    # ---- Total ----
    tot_bl = int(tabela['Backlog'].sum())
    tot_fora = int(tabela['Fora do prazo'].sum())
    tot_no = int(tabela['No prazo'].sum())
    tot = int(tabela['total'].sum())
    tot_sla = (tot_no / tot * 100) if tot > 0 else 0.0
    draw.rounded_rectangle([x, y, x + largura, y + h_lin], radius=10 * s, fill=VERDE_ESC)
    draw.rectangle([x, y, x + largura, y + h_lin // 2], fill=VERDE_ESC)  # só cantos de baixo arredondados
    yc = y + h_lin // 2
    escrever_celula(1, L("Total Geral", "总计"), yc, fontes["bold"], BRANCO)
    escrever_celula(2, _fmt_int(tot), yc, fontes["bold"], BRANCO)
    escrever_celula(3, _fmt_int(tot_no), yc, fontes["bold"], BRANCO)
    escrever_celula(4, _fmt_int(tot_fora), yc, fontes["bold"], BRANCO)
    escrever_celula(5, _fmt_int(tot_bl), yc, fontes["bold"], BRANCO)
    desenhar_sla(tot_sla, yc, destaque_total=True)
    y += h_lin
    return y


def _card_kpi(draw, x0, y0, x1, y1, rotulo, valor, detalhe, cor_acento, fontes, s,
              cor_valor=None, valor_grande=False):
    BRANCO = (255, 255, 255)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12 * s, fill=BRANCO, outline=(226, 234, 229), width=max(1, s))
    # faixa de acento à esquerda
    draw.rounded_rectangle([x0, y0, x0 + 6 * s, y1], radius=3 * s, fill=cor_acento)
    tx = x0 + 22 * s
    _texto(draw, (tx, y0 + 18 * s), rotulo.upper(), fontes["rotulo"], (107, 114, 128), "la")
    _texto(draw, (tx, y0 + 40 * s), valor, fontes["hero"] if valor_grande else fontes["kpi"],
           cor_valor or _hex_rgb(CINZA_TEXTO), "la")
    if detalhe:
        _texto(draw, (tx, y1 - 16 * s), detalhe, fontes["normal_p"], (107, 114, 128), "ls")


def gerar_imagem_relatorio(g_sup_img, g_ponto_img, tem_sup: bool, agora_label: str, extracao_label: str = None) -> bytes:
    """PNG gerencial em estilo dashboard: cabeçalho com logo, cards de KPI,
    ranking com barra de SLA por DSP (e por supervisor, se houver mapa) e
    rodapé com legenda. Largura de 1400px: legível no celular (WhatsApp) e
    cheia o bastante na tela do PC. Desenha em 2x e reduz (antialiasing)."""
    LARGURA_FINAL = 1400
    s = 2  # supersampling
    W = LARGURA_FINAL * s
    M = 32 * s  # margem lateral

    fontes = {
        "titulo": _carregar_fonte(26 * s, negrito=True),
        "sub": _carregar_fonte(14 * s),
        "secao": _carregar_fonte(18 * s, negrito=True),
        "rotulo": _carregar_fonte(12 * s, negrito=True),
        "kpi": _carregar_fonte(30 * s, negrito=True),
        "hero": _carregar_fonte(34 * s, negrito=True),
        "normal": _carregar_fonte(15 * s),
        "normal_p": _carregar_fonte(13 * s),
        "bold": _carregar_fonte(15 * s, negrito=True),
        "bold_p": _carregar_fonte(13 * s, negrito=True),
    }

    VERDE_ESC = _hex_rgb(VERDE_SIDEBAR)
    BRANCO = (255, 255, 255)
    TXT = _hex_rgb(CINZA_TEXTO)
    TXT_SUAVE = (107, 114, 128)

    # Canvas alto o suficiente; recorta no fim pela altura realmente usada
    n_linhas = len(g_ponto_img) + ((len(g_sup_img) + 4) if (tem_sup and g_sup_img is not None) else 0)
    H_MAX = (560 + n_linhas * 42 + 200) * s
    img = Image.new("RGB", (W, H_MAX), _hex_rgb(FUNDO))
    draw = ImageDraw.Draw(img)

    # ============ Cabeçalho (faixa verde) ============
    h_header = 124 * s
    draw.rectangle([0, 0, W, h_header], fill=VERDE_ESC)
    # logo num card branco
    logo_x0, logo_y0 = M, 22 * s
    logo_h = h_header - 44 * s
    logo_w = logo_h * 2  # proporção aproximada; ajusta abaixo pela imagem real
    try:
        logo = Image.open(CAMINHO_LOGO).convert("RGBA")
        alvo_h = logo_h - 16 * s
        alvo_w = int(logo.width * alvo_h / logo.height)
        logo = logo.resize((alvo_w, alvo_h), Image.LANCZOS)
        logo_w = alvo_w + 28 * s
        draw.rounded_rectangle([logo_x0, logo_y0, logo_x0 + logo_w, logo_y0 + logo_h], radius=12 * s, fill=BRANCO)
        img.paste(logo, (logo_x0 + 14 * s, logo_y0 + 8 * s), logo)
        tx = logo_x0 + logo_w + 24 * s
    except Exception:
        tx = M
    _texto(draw, (tx, 34 * s), L("Indicador de SLA Operacional", "SLA运营指标"), fontes["titulo"], BRANCO, "la")
    linha_sub = L(f"Extração: {extracao_label or '—'}   ·   Gerado em: {agora_label}",
                  f"数据提取：{extracao_label or '—'}   ·   生成时间：{agora_label}")
    _texto(draw, (tx, 76 * s), linha_sub, fontes["sub"], (178, 214, 196), "la")
    # chip da meta à direita
    chip_txt = L(f"Meta SLA: {META_SLA_IMG:.0f}%", f"SLA目标：{META_SLA_IMG:.0f}%")
    cw = int(draw.textlength(chip_txt, font=fontes["bold_p"])) + 32 * s
    ch = 34 * s
    cx1, cy0 = W - M, (h_header - ch) // 2
    draw.rounded_rectangle([cx1 - cw, cy0, cx1, cy0 + ch], radius=ch // 2, fill=(18, 79, 59), outline=(52, 120, 95), width=max(1, s))
    _texto(draw, (cx1 - cw // 2, cy0 + ch // 2), chip_txt, fontes["bold_p"], BRANCO, "mm")

    y = h_header + 28 * s

    # ============ KPIs ============
    tot = int(g_ponto_img['total'].sum())
    no_prazo = int(g_ponto_img['No prazo'].sum())
    fora = int(g_ponto_img['Fora do prazo'].sum())
    backlog = int(g_ponto_img['Backlog'].sum())
    sla = (no_prazo / tot * 100) if tot > 0 else 0.0
    dif = sla - META_SLA_IMG
    n_dsp = len(g_ponto_img)
    n_meta = int((g_ponto_img['pct_concluido'] >= META_SLA_IMG).sum())
    pct = lambda v: _fmt_pct(v / tot * 100 if tot else 0, 1)

    gap = 16 * s
    h_card = 118 * s
    larg_util = W - 2 * M
    # SLA geral ocupa um card mais largo (herói)
    fr = [1.35, 1, 1, 1, 1]
    unid = (larg_util - gap * (len(fr) - 1)) / sum(fr)
    cards = [
        (L("SLA Geral", "总体SLA"), _fmt_pct(sla),
         L(f"{dif:+.1f}".replace(".", ",") + " p.p. vs meta",
           f"与目标相差 {dif:+.1f} 个百分点"),
         _cor_barra_rgb(sla), _cor_pill_rgb(sla)[1], True),
        (L("Total de Pedidos", "订单总数"), _fmt_int(tot),
         L(f"{n_meta} de {n_dsp} DSPs na meta", f"{n_dsp} 个网点中 {n_meta} 个达标"),
         (55, 65, 81), None, False),
        (L("No Prazo", "准时件"), _fmt_int(no_prazo), L(f"{pct(no_prazo)} do total", f"占总数 {pct(no_prazo)}"),
         _hex_rgb(VERDE), None, False),
        (L("Fora do Prazo", "超时件"), _fmt_int(fora), L(f"{pct(fora)} do total", f"占总数 {pct(fora)}"),
         _hex_rgb(VERMELHO), None, False),
        (L("Backlog", "积压件"), _fmt_int(backlog), L(f"{pct(backlog)} do total", f"占总数 {pct(backlog)}"),
         _hex_rgb(LARANJA), None, False),
    ]
    cx = M
    for f, (rot, val, det, acento, cor_val, heroi) in zip(fr, cards):
        w = int(unid * f)
        _card_kpi(draw, cx, y, cx + w, y + h_card, rot, val, det, acento, fontes, s,
                  cor_valor=cor_val, valor_grande=heroi)
        cx += w + gap
    y += h_card + 34 * s

    # ============ Tabelas ============
    def titulo_secao(texto, y):
        draw.rounded_rectangle([M, y + 3 * s, M + 5 * s, y + 23 * s], radius=2 * s, fill=_hex_rgb(VERDE))
        _texto(draw, (M + 16 * s, y), texto, fontes["secao"], TXT, "la")
        return y + 36 * s

    if tem_sup and g_sup_img is not None:
        y = titulo_secao(L("SLA por Supervisor", "各主管SLA"), y)
        y = _desenhar_tabela_imagem(draw, M, y, larg_util, g_sup_img, 'supervisor',
                                    L("Supervisor", "主管"), fontes, s)
        y += 34 * s

    y = titulo_secao(L("Ranking de DSPs", "DSP网点排名"), y)
    y = _desenhar_tabela_imagem(draw, M, y, larg_util, g_ponto_img, 'ponto', "DSP", fontes, s)

    # ============ Rodapé / legenda ============
    y += 22 * s
    lx = M
    for cor, rot in [(_hex_rgb(VERDE), L("≥ 92% na meta", "≥ 92% 达标")),
                     (_hex_rgb(LARANJA), L("80 – 91,9% alerta", "80 – 91.9% 警戒")),
                     (_hex_rgb(VERMELHO), L("< 80% crítico", "< 80% 严重"))]:
        r_ = 6 * s
        draw.ellipse([lx, y + 9 * s - r_, lx + 2 * r_, y + 9 * s + r_], fill=cor)
        _texto(draw, (lx + 2 * r_ + 8 * s, y + 9 * s), rot, fontes["normal_p"], TXT_SUAVE, "lm")
        lx += int(draw.textlength(rot, font=fontes["normal_p"])) + 2 * r_ + 36 * s
    # marcador da meta explicado
    draw.line([lx, y + 1 * s, lx, y + 17 * s], fill=(55, 65, 81), width=max(2, s))
    _texto(draw, (lx + 10 * s, y + 9 * s), L("linha = meta 92%", "竖线 = 92% 目标"), fontes["normal_p"], TXT_SUAVE, "lm")
    _texto(draw, (W - M, y + 9 * s), L("SLA = No prazo ÷ Total de pedidos  ·  Anjun Express",
                                        "SLA = 准时件 ÷ 订单总数  ·  Anjun Express"),
           fontes["normal_p"], TXT_SUAVE, "rm")
    y += 44 * s

    img = img.crop((0, 0, W, min(y, H_MAX)))
    img = img.resize((W // s, img.height // s), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()