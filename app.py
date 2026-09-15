import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# CONFIG & IDENTIDADE VISUAL (baseada no padrão DSP - Indicadores de Entrega)
# ============================================================
st.set_page_config(
    page_title="DSP - Indicadores de Entrega / 配送指标 | Anjun Express",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        background-color: rgba(255,255,255,0.07) !important;
        border: 1.5px dashed {VERDE} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] svg {{
        fill: {VERDE} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {{
        background-color: {VERDE} !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
    }}
    .sb-logo {{
        font-size: 22px; font-weight: 800; color: white; padding: 6px 0 2px 0;
    }}
    .sb-logo span {{ color: {VERDE}; }}
    .sb-tagline {{ font-size: 11px; color: #A9C9BB; margin-bottom: 18px; }}
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
    .dps-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px;
                  border-radius: 10px; overflow: hidden; }}
    .dps-table thead tr {{ background-color: {VERDE_SIDEBAR}; }}
    .dps-table thead th {{
        color: white; text-align: left; padding: 10px 14px; font-weight: 600;
    }}
    .dps-table tbody tr:nth-child(even) {{ background-color: #F2F7F4; }}
    .dps-table tbody tr:nth-child(odd) {{ background-color: white; }}
    .dps-table tbody td {{ padding: 9px 14px; color: {CINZA_TEXTO}; }}
    .dps-table tfoot tr {{ background-color: {VERDE_SIDEBAR}; font-weight: 700; }}
    .dps-table tfoot td {{ padding: 11px 14px; color: white; }}
    .sla-pill {{
        display: inline-block; padding: 3px 12px; border-radius: 20px; font-weight: 700;
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
    return zh if globals().get("lang") == "zh" else pt


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
    if globals().get("lang") == "zh":
        return STATUS_ZH.get(s, s)
    return s


def traduzir_motivo(s: str) -> str:
    if globals().get("lang") == "zh":
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


def estilo_barra(fig, altura=340, y_titulo=""):
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        font=FONTE_GRAFICO,
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(range=[0, 108], title=y_titulo, gridcolor="#EEF2EF", zeroline=False),
        xaxis=dict(title="", showgrid=False),
        height=altura, margin=dict(t=28, b=20, l=10, r=10),
        bargap=0.35,
    )
    return fig


def estilo_barra_contagem(fig, altura=340, y_titulo=""):
    """Estilo pra gráfico de barra empilhada com CONTAGEM (não %) — sem range fixo 0-108,
    com legenda no topo e barras por hora."""
    fig.update_layout(
        font=FONTE_GRAFICO,
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(title=y_titulo, gridcolor="#EEF2EF", zeroline=False),
        xaxis=dict(title="", showgrid=False),
        height=altura, margin=dict(t=40, b=20, l=10, r=10),
        barmode="stack", bargap=0.25,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def estilo_donut(fig, total_label: str, altura=320):
    fig.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}: %{value}<extra></extra>")
    fig.update_layout(
        font=FONTE_GRAFICO,
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
        height=altura, margin=dict(t=10, b=10, l=10, r=10),
        annotations=[dict(text=total_label, x=0.5, y=0.5, font=dict(size=20, color=CINZA_TEXTO, family=FONTE_GRAFICO["family"]), showarrow=False)],
    )
    return fig


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


def _carregar_fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    candidatos_zh = (
        ["msyhbd.ttc", "simhei.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
         "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if negrito else
        ["msyh.ttc", "simsun.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
         "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    candidatos_latin = (
        ["arialbd.ttf", "Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if negrito else
        ["arial.ttf", "Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    # Em zh, tenta fontes com glifos CJK primeiro (Arial não desenha caracteres chineses)
    candidatos = candidatos_zh + candidatos_latin if globals().get("lang") == "zh" else candidatos_latin + candidatos_zh
    for nome in candidatos:
        try:
            return ImageFont.truetype(nome, tamanho)
        except Exception:
            continue
    return ImageFont.load_default()


def _cor_pill_rgb(valor: float):
    if valor >= 92:
        return (223, 243, 230), (15, 122, 61)
    elif valor >= 80:
        return (253, 238, 219), (180, 83, 9)
    else:
        return (253, 226, 225), (185, 28, 28)


def _desenhar_tabela_imagem(draw: ImageDraw.ImageDraw, x: int, y: int, largura: int,
                             tabela: pd.DataFrame, coluna_chave: str, rotulo_coluna: str,
                             fonte, fonte_bold) -> int:
    verde_sidebar_rgb = (11, 61, 46)
    branco = (255, 255, 255)
    cinza_texto = (31, 41, 55)
    linha_par = (242, 247, 244)
    altura_linha = 36

    colunas = [rotulo_coluna, L("Backlog", "积压件"), L("Fora do Prazo", "超时件"),
               L("No Prazo", "准时件"), L("Total Geral", "总计"), L("SLA", "SLA")]
    larguras_pct = [0.26, 0.15, 0.17, 0.15, 0.15, 0.12]
    larguras = [int(largura * p) for p in larguras_pct]

    draw.rectangle([x, y, x + largura, y + altura_linha], fill=verde_sidebar_rgb)
    cx = x
    for c, w in zip(colunas, larguras):
        draw.text((cx + 12, y + 10), c, font=fonte_bold, fill=branco)
        cx += w
    y += altura_linha

    tabela_ordenada = tabela.sort_values('pct_concluido', ascending=False)
    for i, (_, r) in enumerate(tabela_ordenada.iterrows()):
        bg = linha_par if i % 2 == 0 else branco
        draw.rectangle([x, y, x + largura, y + altura_linha], fill=bg)
        cx = x
        valores = [
            str(r[coluna_chave]),
            f"{int(r['Backlog']):,}".replace(",", "."),
            f"{int(r['Fora do prazo']):,}".replace(",", "."),
            f"{int(r['No prazo']):,}".replace(",", "."),
            f"{int(r['total']):,}".replace(",", "."),
        ]
        for v, w in zip(valores, larguras[:5]):
            draw.text((cx + 12, y + 10), v, font=fonte, fill=cinza_texto)
            cx += w
        bg_pill, cor_pill = _cor_pill_rgb(r['pct_concluido'])
        texto_pct = f"{r['pct_concluido']:.2f}%"
        pill_w, pill_h = 72, 24
        px0, py0 = cx + 8, y + (altura_linha - pill_h) // 2
        draw.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=12, fill=bg_pill)
        draw.text((px0 + 10, py0 + 4), texto_pct, font=fonte, fill=cor_pill)
        y += altura_linha

    tot_backlog = int(tabela['Backlog'].sum())
    tot_fora = int(tabela['Fora do prazo'].sum())
    tot_no = int(tabela['No prazo'].sum())
    tot_geral = int(tabela['total'].sum())
    tot_sla = (tot_no / tot_geral * 100) if tot_geral > 0 else 0.0
    draw.rectangle([x, y, x + largura, y + altura_linha], fill=verde_sidebar_rgb)
    cx = x
    valores_tot = [L("Total Geral", "总计"), f"{tot_backlog:,}".replace(",", "."), f"{tot_fora:,}".replace(",", "."),
                   f"{tot_no:,}".replace(",", "."), f"{tot_geral:,}".replace(",", ".")]
    for v, w in zip(valores_tot, larguras[:5]):
        draw.text((cx + 12, y + 10), v, font=fonte_bold, fill=branco)
        cx += w
    pill_w, pill_h = 72, 24
    px0, py0 = cx + 8, y + (altura_linha - pill_h) // 2
    draw.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=12, fill=(255, 255, 255))
    draw.text((px0 + 10, py0 + 4), f"{tot_sla:.2f}%", font=fonte, fill=verde_sidebar_rgb)
    y += altura_linha
    return y


def gerar_imagem_relatorio(g_sup_img, g_ponto_img, tem_sup: bool, agora_label: str) -> bytes:
    largura = 1200
    fonte_titulo = _carregar_fonte(20, negrito=True)
    fonte_sub = _carregar_fonte(13)
    fonte = _carregar_fonte(14)
    fonte_bold = _carregar_fonte(14, negrito=True)

    linhas_sup = (len(g_sup_img) + 2) if tem_sup else 0
    linhas_dsp = len(g_ponto_img) + 2
    altura_total = 70 + (40 + linhas_sup * 36 + 30 if tem_sup else 0) + 40 + linhas_dsp * 36 + 30

    img = Image.new("RGB", (largura, altura_total), (247, 249, 246))
    draw = ImageDraw.Draw(img)

    y = 20
    draw.text((20, y), L("Indicador de SLA Operacional — Anjun Express", "SLA运营指标 — Anjun Express"),
               font=fonte_titulo, fill=(11, 61, 46))
    y += 26
    draw.text((20, y), L(f"Gerado a partir do arquivo processado em: {agora_label}",
                          f"数据处理时间：{agora_label}"), font=fonte_sub, fill=(107, 114, 128))
    y += 34

    if tem_sup:
        draw.text((20, y), L("Por Supervisor", "按主管"), font=fonte_bold, fill=(31, 41, 55))
        y += 26
        y = _desenhar_tabela_imagem(draw, 20, y, largura - 40, g_sup_img, 'supervisor', L("Supervisor", "主管"), fonte, fonte_bold)
        y += 30

    draw.text((20, y), L("Todos os DSPs", "全部DSP网点"), font=fonte_bold, fill=(31, 41, 55))
    y += 26
    y = _desenhar_tabela_imagem(draw, 20, y, largura - 40, g_ponto_img, 'ponto', "DSP", fonte, fonte_bold)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    _lang_escolha = st.selectbox("🌐 Idioma / 语言", ["Português", "中文"], key="lang_sel")
    lang = "zh" if _lang_escolha == "中文" else "pt"

    st.markdown('<div class="sb-logo">Anjun <span>Express</span></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sb-tagline">{L("Mais eficiência para a sua entrega.", "为您的配送提供更高效率。")}</div>',
        unsafe_allow_html=True
    )

    nav_items = [("🕐", "SLA", True)]
    for icone, nome, ativo in nav_items:
        classe = "sb-nav-item active" if ativo else "sb-nav-item"
        st.markdown(f'<div class="{classe}">{icone} &nbsp;{nome}</div>', unsafe_allow_html=True)

    st.markdown("---")
    uploaded_file = st.file_uploader(
        L("📤 Enviar base bruta (.xlsx)", "📤 上传原始数据 (.xlsx)"),
        type=["xlsx"],
        help=L(
            "Export padrão 'monitoramento_da_pontualidade_de_pedido' — nível de waybill individual.",
            "标准导出文件 'monitoramento_da_pontualidade_de_pedido' —— 运单级别数据。"
        )
    )
    mapa_file = st.file_uploader(
        L("🗂️ Mapa Ponto → Supervisor (opcional)", "🗂️ 网点→主管 对照表（可选）"),
        type=["xlsx", "csv"],
        help=L(
            "Planilha com 2 colunas: 'Ponto' e 'Supervisor'. Sem isso, a visão por supervisor fica desativada.",
            "包含两列的表格：'Ponto' 和 'Supervisor'。没有此文件，按主管查看的功能将无法使用。"
        )
    )

# ============================================================
# CONTEÚDO PRINCIPAL
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

try:
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    if st.session_state.get("file_id") != file_id:
        st.session_state["file_id"] = file_id
        st.session_state["agora_fixo"] = pd.Timestamp.now()
    agora = st.session_state["agora_fixo"]

    df = processar_base(uploaded_file)

    tem_supervisor = False
    if mapa_file is not None:
        mapa_supervisor = processar_mapa_supervisor(mapa_file)
        df = df.merge(mapa_supervisor, on='ponto', how='left')
        df['supervisor'] = df['supervisor'].fillna(L('Sem supervisor mapeado', '未匹配主管'))
        tem_supervisor = True
except ValueError as e:
    st.error(str(e))
    st.stop()

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
sla_real = calc_sla(no_prazo, fora)
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
# Gráficos
# ============================================================
g_estado = agrupar(df, 'estado_dest').sort_values('pct_concluido', ascending=False)

col_chart1, col_chart2 = st.columns([2, 1])
with col_chart1:
    st.markdown(f"#### {L('% Concluído no Prazo por Estado', '各州准时完成率')}")
    fig = px.bar(
        g_estado, x='estado_dest', y='pct_concluido',
        text=g_estado['pct_concluido'].apply(lambda v: f"{v:.1f}%"),
        color_discrete_sequence=[VERDE],
    )
    fig.add_hline(y=92, line_dash="dash", line_color=LARANJA,
                  annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left")
    fig.update_layout(xaxis=dict(categoryorder="array", categoryarray=g_estado['estado_dest'].tolist()))
    estilo_barra(fig, altura=360, y_titulo=L("% Concluído no Prazo", "准时完成率"))
    st.plotly_chart(fig, use_container_width=True)

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

    col_comp1, col_comp2 = st.columns([1, 2])
    with col_comp1:
        fig_comp = go.Figure(data=[go.Pie(
            labels=comp['status_show'], values=comp['qtd'], hole=0.6,
            marker_colors=[LARANJA, CINZA_ESCURO, VERMELHO, "#8FA89B", "#C9A227"][:len(comp)],
        )])
        rotulo_backlog = L("backlog", "积压件")
        estilo_donut(fig_comp, total_label=f"{backlog:,}".replace(",", ".") + f"<br><span style='font-size:11px;color:#6B7280'>{rotulo_backlog}</span>", altura=320)
        st.plotly_chart(fig_comp, use_container_width=True)
    with col_comp2:
        cores_status = [LARANJA, CINZA_ESCURO, VERMELHO, "#8FA89B", "#C9A227"]
        linhas_status = ""
        for pos, (_, r) in enumerate(comp.iterrows()):
            pct = r['qtd'] / backlog * 100
            cor_barra = cores_status[pos % len(cores_status)]
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

    fig_hora = go.Figure()
    fig_hora.add_bar(x=g_hora['hora_label'], y=g_hora['No prazo'],
                      name=L('No Prazo', '准时件'), marker_color=VERDE)
    fig_hora.add_bar(x=g_hora['hora_label'], y=g_hora['Fora do prazo'],
                      name=L('Fora do Prazo', '超时件'), marker_color=VERMELHO)
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

    fig_ant = px.bar(
        g_ant, x='faixa', y='qtd',
        text=g_ant['qtd'].apply(lambda v: f"{int(v):,}".replace(",", ".")),
        color_discrete_sequence=[VERDE],
    )
    fig_ant.update_layout(showlegend=False)
    estilo_barra_contagem(fig_ant, altura=340, y_titulo=L('Pedidos (qtd)', '订单数量'))
    st.plotly_chart(fig_ant, use_container_width=True)

    media_ant = no_prazo_df['diferenca_dias'].mean()
    mediana_ant = no_prazo_df['diferenca_dias'].median()
    st.caption(L(
        f"Média de {media_ant:.1f} dias de antecedência (mediana: {mediana_ant:.1f} dias), "
        f"com base nos {len(no_prazo_df):,} pedidos entregues no prazo.".replace(",", "."),
        f"平均提前 {media_ant:.1f} 天签收（中位数：{mediana_ant:.1f} 天），"
        f"基于 {len(no_prazo_df):,} 笔准时签收订单统计。"
    ))
else:
    st.info(L("Nenhum pedido no prazo neste corte ainda.", "本次数据中暂无准时签收订单。"))

# ============================================================
# Visão por Supervisor
# ============================================================
if tem_supervisor:
    st.markdown(f"#### {L('% Concluído no Prazo por Supervisor', '各主管准时完成率')}")
    g_sup = agrupar(df, 'supervisor').sort_values('pct_concluido', ascending=False)
    fig_sup = px.bar(
        g_sup, x='supervisor', y='pct_concluido',
        text=g_sup['pct_concluido'].apply(lambda v: f"{v:.1f}%"),
        color_discrete_sequence=[VERDE],
    )
    fig_sup.add_hline(y=92, line_dash="dash", line_color=LARANJA,
                       annotation_text=L("Meta 92%", "目标 92%"), annotation_position="top left")
    fig_sup.update_layout(xaxis=dict(categoryorder="array", categoryarray=g_sup['supervisor'].tolist()))
    estilo_barra(fig_sup, altura=340, y_titulo=L("% Concluído no Prazo", "准时完成率"))
    st.plotly_chart(fig_sup, use_container_width=True)

    st.markdown(
        montar_tabela_html(g_sup, coluna_chave='supervisor', rotulo_coluna=L('Supervisor', '主管')),
        unsafe_allow_html=True
    )
else:
    st.info(L(
        "Envie o mapa Ponto → Supervisor na barra lateral pra ativar a visão e o filtro por supervisor.",
        "请在侧边栏上传 网点→主管 对照表，以启用按主管查看和筛选功能。"
    ))

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
    df_drill = df[df['ponto'].isin(pontos_drill)]
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

            with tab_fora:
                df_fora_lista = df_lista[df_lista['classe'] == 'Fora do prazo'].copy()
                if df_fora_lista.empty:
                    st.info(L("Nenhum pedido fora do prazo nesse recorte.", "该范围内没有超时订单。"))
                else:
                    df_fora_lista['dias_atraso'] = (-df_fora_lista['diferenca_dias']).round(2)
                    df_fora_show = df_fora_lista[
                        ['waybill', 'entregador', 'ponto', 'deadline', 'signature_dt', 'dias_atraso']
                    ].sort_values('dias_atraso', ascending=False)
                    df_fora_show.columns = [
                        L('Waybill', '运单号'), L('Entregador', '配送员'), 'DSP',
                        L('Prazo', '时效'), L('Assinatura', '签收时间'), L('Dias de Atraso', '超时天数')
                    ]
                    st.dataframe(df_fora_show, use_container_width=True, hide_index=True)

            with tab_backlog:
                df_backlog_lista = df_lista[df_lista['classe'] == 'Backlog'].copy()
                if df_backlog_lista.empty:
                    st.info(L("Nenhum pedido em backlog nesse recorte.", "该范围内没有积压订单。"))
                else:
                    agora_ref = pd.Timestamp.now()
                    df_backlog_lista['dias_desde_vencimento'] = (
                        (agora_ref - df_backlog_lista['deadline']).dt.total_seconds() / 86400
                    ).round(2)
                    df_backlog_lista['status_show'] = df_backlog_lista['status'].apply(traduzir_status)
                    df_backlog_show = df_backlog_lista[
                        ['waybill', 'entregador', 'ponto', 'status_show', 'deadline', 'dias_desde_vencimento']
                    ].sort_values('dias_desde_vencimento', ascending=False)
                    df_backlog_show.columns = [
                        L('Waybill', '运单号'), L('Entregador', '配送员'), 'DSP', L('Status', '状态'),
                        L('Prazo', '时效'), L('Dias desde o Vencimento', '距到期天数')
                    ]
                    st.dataframe(df_backlog_show, use_container_width=True, hide_index=True)
                    st.caption(L(
                        "Valor negativo em 'Dias desde o Vencimento' = o prazo ainda não venceu.",
                        "「距到期天数」为负数表示时效尚未到期。"
                    ))

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