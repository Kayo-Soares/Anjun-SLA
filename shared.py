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
from PIL import Image, ImageDraw, ImageFont

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


def _cor_pill_rgb(valor: float):
    if valor >= 92:
        return (223, 243, 230), (15, 122, 61)
    elif valor >= 80:
        return (253, 238, 219), (180, 83, 9)
    else:
        return (253, 226, 225), (185, 28, 28)


def _desenhar_tabela_imagem(draw: ImageDraw.ImageDraw, x: int, y: int, largura: int,
                             tabela: pd.DataFrame, coluna_chave: str, rotulo_coluna: str,
                             fonte, fonte_bold, escala: int = 1) -> int:
    verde_sidebar_rgb = (11, 61, 46)
    branco = (255, 255, 255)
    cinza_texto = (31, 41, 55)
    linha_par = (242, 247, 244)
    altura_linha = 36 * escala
    pad = 12 * escala

    colunas = [rotulo_coluna, L("Backlog", "积压件"), L("Fora do Prazo", "超时件"),
               L("No Prazo", "准时件"), L("Total Geral", "总计"), L("SLA", "SLA")]
    larguras_pct = [0.26, 0.15, 0.17, 0.15, 0.15, 0.12]
    larguras = [int(largura * p) for p in larguras_pct]

    draw.rectangle([x, y, x + largura, y + altura_linha], fill=verde_sidebar_rgb)
    cx = x
    for c, w in zip(colunas, larguras):
        draw.text((cx + pad, y + 10 * escala), c, font=fonte_bold, fill=branco)
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
            draw.text((cx + pad, y + 10 * escala), v, font=fonte, fill=cinza_texto)
            cx += w
        bg_pill, cor_pill = _cor_pill_rgb(r['pct_concluido'])
        texto_pct = f"{r['pct_concluido']:.2f}%"
        pill_w, pill_h = 72 * escala, 24 * escala
        px0, py0 = cx + 8 * escala, y + (altura_linha - pill_h) // 2
        draw.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=12 * escala, fill=bg_pill)
        draw.text((px0 + 10 * escala, py0 + 4 * escala), texto_pct, font=fonte, fill=cor_pill)
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
        draw.text((cx + pad, y + 10 * escala), v, font=fonte_bold, fill=branco)
        cx += w
    pill_w, pill_h = 72 * escala, 24 * escala
    px0, py0 = cx + 8 * escala, y + (altura_linha - pill_h) // 2
    draw.rounded_rectangle([px0, py0, px0 + pill_w, py0 + pill_h], radius=12 * escala, fill=(255, 255, 255))
    draw.text((px0 + 10 * escala, py0 + 4 * escala), f"{tot_sla:.2f}%", font=fonte, fill=verde_sidebar_rgb)
    y += altura_linha
    return y


def gerar_imagem_relatorio(g_sup_img, g_ponto_img, tem_sup: bool, agora_label: str) -> bytes:
    # Renderiza em 2x e reduz no final (supersampling) — deixa o texto nítido e
    # anti-aliasado em vez de serrilhado, principalmente perceptível em telas de alta densidade.
    ESCALA = 2
    largura = 1200 * ESCALA
    fonte_titulo = _carregar_fonte(20 * ESCALA, negrito=True)
    fonte_sub = _carregar_fonte(13 * ESCALA)
    fonte = _carregar_fonte(14 * ESCALA)
    fonte_bold = _carregar_fonte(14 * ESCALA, negrito=True)

    linhas_sup = (len(g_sup_img) + 2) if tem_sup else 0
    linhas_dsp = len(g_ponto_img) + 2
    altura_total = (70 + (40 + linhas_sup * 36 + 30 if tem_sup else 0) + 40 + linhas_dsp * 36 + 30) * ESCALA

    img = Image.new("RGB", (largura, altura_total), (247, 249, 246))
    draw = ImageDraw.Draw(img)

    y = 20 * ESCALA
    # "-" simples em vez de travessão "—": mais compatível entre fontes/sistemas,
    # evita o glifo "tofu" (quadrado) quando a fonte carregada não tem esse caractere.
    draw.text((20 * ESCALA, y), L("Indicador de SLA Operacional - Anjun Express", "SLA运营指标 - Anjun Express"),
               font=fonte_titulo, fill=(11, 61, 46))
    y += 26 * ESCALA
    draw.text((20 * ESCALA, y), L(f"Gerado a partir do arquivo processado em: {agora_label}",
                          f"数据处理时间：{agora_label}"), font=fonte_sub, fill=(107, 114, 128))
    y += 34 * ESCALA

    if tem_sup:
        draw.text((20 * ESCALA, y), L("Por Supervisor", "按主管"), font=fonte_bold, fill=(31, 41, 55))
        y += 26 * ESCALA
        y = _desenhar_tabela_imagem(draw, 20 * ESCALA, y, largura - 40 * ESCALA, g_sup_img, 'supervisor',
                                     L("Supervisor", "主管"), fonte, fonte_bold, escala=ESCALA)
        y += 30 * ESCALA

    draw.text((20 * ESCALA, y), L("Todos os DSPs", "全部DSP网点"), font=fonte_bold, fill=(31, 41, 55))
    y += 26 * ESCALA
    y = _desenhar_tabela_imagem(draw, 20 * ESCALA, y, largura - 40 * ESCALA, g_ponto_img, 'ponto', "DSP",
                                 fonte, fonte_bold, escala=ESCALA)

    # Reduz de volta pro tamanho final com LANCZOS (reamostragem de alta qualidade) —
    # é isso que faz o supersampling funcionar: desenhar grande e encolher com suavização
    # produz anti-aliasing melhor do que desenhar direto no tamanho final.
    img = img.resize((largura // ESCALA, altura_total // ESCALA), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()