import html
import os

from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf

# =====================================================================
# CONFIGURACIÓN GENERAL
# =====================================================================
st.set_page_config(
    page_title="Principios Finanzas",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# API KEYS
# =====================================================================
def read_env_value(key: str, default: str = "") -> str:
    """Lee claves desde variables de entorno, Streamlit secrets o .env local."""
    value = os.getenv(key)
    if value:
        return value.strip()
    try:
        value = st.secrets.get(key, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    try:
        with open(os.path.join(os.getcwd(), ".env"), "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                env_key, env_value = line.split("=", 1)
                if env_key.strip() == key:
                    return env_value.strip().strip('"').strip("'")
    except OSError:
        pass
    return default


FINNHUB_KEY = read_env_value("FINNHUB_KEY")
GROQ_API_KEY = read_env_value("GROQ_API_KEY")
GROQ_MODEL = read_env_value("GROQ_MODEL", "llama-3.3-70b-versatile")

# =====================================================================
# CSS GLOBAL
# =====================================================================
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] { font-family: "DM Sans", sans-serif; }
.stApp { background-color: #0d1117; color: #c9d1d9; }

[data-testid="stSidebarHeader"] { display: none !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] * {
    font-size: 0.95rem !important;
}
[data-testid="stSidebar"] .section-label {
    font-size: 0.75rem !important;
}

/* ── LEGIBILIDAD GLOBAL: textos que Streamlit pone en gris claro ── */
/* Métricas — label y valor */
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] {
    color: #c9d1d9 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #f0f6fc !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    color: #8b949e !important;
}

/* Texto dentro de expanders */
.streamlit-expanderContent p,
.streamlit-expanderContent li,
.streamlit-expanderContent td,
.streamlit-expanderContent th {
    color: #c9d1d9 !important;
}

/* Dataframe / tabla del simulador */
[data-testid="stDataFrame"] {
    color: #c9d1d9 !important;
}

/* Info boxes */
[data-testid="stInfoMessage"] {
    color: #c9d1d9 !important;
}

/* Texto general de markdown dentro de tabs */
.stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
    color: #c9d1d9 !important;
}

/* Radio buttons */
[data-testid="stRadio"] label {
    color: #c9d1d9 !important;
}

/* Selectbox y number input labels */
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label {
    color: #c9d1d9 !important;
}

/* Caption */
.stCaption {
    color: #8b949e !important;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.6rem, 3vw, 2.6rem);
    font-weight: 700;
    color: #f0f6fc;
    letter-spacing: -0.01em;
    line-height: 1.15;
    text-transform: uppercase;
}
.hero-sub {
    color: #58a6ff;
    font-size: 0.82rem;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    font-family: 'DM Mono', monospace;
    margin-top: 8px;
    opacity: 0.85;
}

[data-baseweb="tab-list"] {
    background: #161b22 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #30363d !important;
    gap: 2px !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: #8b949e !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    border-radius: 7px !important;
    padding: 8px 18px !important;
    border: 1px solid transparent !important;
    transition: all 0.18s ease !important;
}
[data-baseweb="tab"]:hover {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border-color: #30363d !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #1f6feb !important;
    color: #ffffff !important;
    border-color: #388bfd !important;
    font-weight: 600 !important;
    box-shadow: 0 0 12px rgba(31,111,235,0.35) !important;
}

.fin-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    color: #1f6feb;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 8px;
}
.badge-verde { background:rgba(35,134,54,0.15); color:#3fb950; border:1px solid rgba(63,185,80,0.3); border-radius:20px; padding:3px 12px; font-size:0.78rem; font-weight:600; font-family:'DM Mono',monospace; }
.badge-rojo  { background:rgba(248,81,73,0.12);  color:#f85149; border:1px solid rgba(248,81,73,0.3);  border-radius:20px; padding:3px 12px; font-size:0.78rem; font-weight:600; font-family:'DM Mono',monospace; }
.badge-azul  { background:rgba(31,111,235,0.12); color:#58a6ff; border:1px solid rgba(88,166,255,0.3); border-radius:20px; padding:3px 12px; font-size:0.78rem; font-weight:600; font-family:'DM Mono',monospace; }
.badge-gris  { background:rgba(110,118,129,0.12);color:#8b949e; border:1px solid rgba(110,118,129,0.3);border-radius:20px; padding:3px 12px; font-size:0.78rem; font-weight:600; font-family:'DM Mono',monospace; }
.mono { font-family:'DM Mono',monospace; }

.ai-card {
    background: linear-gradient(135deg, rgba(31,111,235,0.08), rgba(88,166,255,0.04));
    border: 1px solid rgba(88,166,255,0.25);
    border-radius: 12px;
    padding: 20px 22px;
    margin-top: 16px;
}
</style>''', unsafe_allow_html=True)

# =====================================================================
# PLOTLY TEMPLATE OSCURO
# =====================================================================
PLOTLY_DARK = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#8b949e', family='DM Sans'),
    xaxis=dict(gridcolor='#21262d', linecolor='#30363d', tickcolor='#30363d'),
    yaxis=dict(gridcolor='#21262d', linecolor='#30363d', tickcolor='#30363d'),
    margin=dict(l=16, r=16, t=24, b=16),
    hovermode='x unified',
)

# =====================================================================
# DATA LAYER — FINNHUB: tiempo real, perfil, métricas y noticias
# =====================================================================
def finnhub_get(endpoint: str, params: dict | None = None) -> dict | list:
    """Llamada base a Finnhub con manejo de errores."""
    if not FINNHUB_KEY:
        return {}
    safe_params = dict(params or {})
    safe_params["token"] = FINNHUB_KEY
    try:
        r = requests.get(f"https://finnhub.io/api/v1/{endpoint}", params=safe_params, timeout=12)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        return {}
    return {}

@st.cache_data(ttl=900, show_spinner=False)          # 15 min — precio cambia seguido
def fh_quote(ticker: str) -> dict:
    """Cotización y variación intradiaria."""
    return finnhub_get("quote", {"symbol": ticker})

@st.cache_data(ttl=86400, show_spinner=False)         # 24 hs — perfil casi nunca cambia
def fh_profile(ticker: str) -> dict:
    """Perfil de la empresa."""
    return finnhub_get("stock/profile2", {"symbol": ticker})

@st.cache_data(ttl=86400, show_spinner=False)         # 24 hs — métricas se actualizan al cierre
def fh_metrics(ticker: str) -> dict:
    """Métricas fundamentales (PER, Beta, Market Cap, etc.)."""
    data = finnhub_get("stock/metric", {"symbol": ticker, "metric": "all"})
    return data.get("metric", {})

@st.cache_data(ttl=3600, show_spinner=False)          # 1 hora — noticias
def fh_news(ticker: str) -> list:
    """Noticias recientes de la empresa."""
    today = datetime.today()
    from_d = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    to_d   = today.strftime("%Y-%m-%d")
    data = finnhub_get("company-news", {"symbol": ticker, "from": from_d, "to": to_d})
    return data if isinstance(data, list) else []

@st.cache_data(ttl=86400, show_spinner=False)         # 24 hs — earnings cambian mensualmente
def fh_earnings(ticker: str) -> list:
    """Calendario de earnings próximos."""
    today = datetime.today()
    to_d = (today + timedelta(days=90)).strftime("%Y-%m-%d")
    from_d = today.strftime("%Y-%m-%d")
    data = finnhub_get("calendar/earnings", {"symbol": ticker, "from": from_d, "to": to_d})
    return data.get("earningsCalendar", []) if isinstance(data, dict) else []

@st.cache_data(ttl=86400, show_spinner=False)         # 24 hs — datos anuales
def fh_financials(ticker: str) -> dict:
    """Estados financieros anuales."""
    data = finnhub_get("financials-reported", {"symbol": ticker, "freq": "annual"})
    return data if isinstance(data, dict) else {}

# =====================================================================
# DATA LAYER — YFINANCE: históricos, series temporales y visualizaciones
# =====================================================================
def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    clean = df.copy()
    if isinstance(clean.columns, pd.MultiIndex):
        clean.columns = clean.columns.get_level_values(0)
    keep = [col for col in ["Open", "High", "Low", "Close", "Volume"] if col in clean.columns]
    clean = clean[keep].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    if "Close" in clean.columns:
        clean = clean.dropna(subset=["Close"])
    try:
        clean.index = pd.to_datetime(clean.index).tz_localize(None)
    except Exception:
        clean.index = pd.to_datetime(clean.index, errors="coerce")
    return clean[~clean.index.isna()].sort_index()


@st.cache_data(ttl=3600, show_spinner=False)          # 1 hora — histórico de precios
def yf_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        return clean_ohlcv(yf.Ticker(ticker.upper()).history(period=period, auto_adjust=False))
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)         # 24 hs — financials anuales
def yf_financials(ticker: str) -> pd.DataFrame:
    try:
        return yf.Ticker(ticker.upper()).financials
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)          # 1 hora — histórico simulador
def yf_download_close(tickers: tuple[str, ...], period: str) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()
    try:
        data = yf.download(list(tickers), period=period, auto_adjust=True, progress=False, threads=False)
        if data is None or data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            close = data["Close"] if "Close" in data.columns.get_level_values(0) else pd.DataFrame()
        else:
            close = data[["Close"]].rename(columns={"Close": tickers[0]}) if "Close" in data.columns else pd.DataFrame()
        if isinstance(close, pd.Series):
            close = close.to_frame(tickers[0])
        close = close.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        close.index = pd.to_datetime(close.index).tz_localize(None)
        return close.sort_index()
    except Exception:
        return pd.DataFrame()


# =====================================================================
# ANALYTICS LAYER
# =====================================================================
def safe_float(value, default=None):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def current_price_from_quote(quote: dict):
    return safe_float(quote.get("c")) if isinstance(quote, dict) else None


def price_change_pct(quote: dict):
    current = safe_float(quote.get("c")) if isinstance(quote, dict) else None
    previous = safe_float(quote.get("pc")) if isinstance(quote, dict) else None
    if current is None or previous in (None, 0):
        return None
    return ((current - previous) / previous) * 100


def period_return(close: pd.Series):
    close = pd.to_numeric(close, errors="coerce").dropna()
    if len(close) < 2 or close.iloc[0] == 0:
        return None
    return ((close.iloc[-1] / close.iloc[0]) - 1) * 100


def technical_snapshot(hist: pd.DataFrame) -> dict:
    if hist.empty or "Close" not in hist.columns:
        return {}
    close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
    if len(close) < 2:
        return {}
    returns = close.pct_change().dropna()
    return {
        "rendimiento_periodo": period_return(close),
        "media_50": safe_float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None,
        "media_200": safe_float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None,
        "volatilidad_anual": safe_float(returns.std() * (252 ** 0.5) * 100) if not returns.empty else None,
    }


def build_historical_figure(hist: pd.DataFrame, ticker: str, chart_type: str) -> go.Figure | None:
    if hist.empty or "Close" not in hist.columns:
        return None
    fig = go.Figure()
    if chart_type == "Velas" and {"Open", "High", "Low", "Close"}.issubset(hist.columns):
        candle_df = hist.dropna(subset=["Open", "High", "Low", "Close"])
        if candle_df.empty:
            return None
        fig.add_trace(go.Candlestick(
            x=candle_df.index, open=candle_df["Open"], high=candle_df["High"],
            low=candle_df["Low"], close=candle_df["Close"], name=ticker,
            increasing_line_color="#3fb950", decreasing_line_color="#f85149",
        ))
        fig.update_layout(xaxis_rangeslider_visible=False)
    else:
        close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if close.empty:
            return None
        fig.add_trace(go.Scatter(
            x=close.index, y=close.values, mode="lines", name=ticker,
            line=dict(color="#58a6ff", width=2.5),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.06)"
        ))
    fig.update_layout(
        height=400, yaxis_title="Precio (USD)", xaxis_title="Fecha",
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e')),
        **PLOTLY_DARK
    )
    return fig


def extract_net_margin_series(ticker: str) -> pd.Series:
    finanzas = yf_financials(ticker)
    if finanzas.empty or "Net Income" not in finanzas.index or "Total Revenue" not in finanzas.index:
        return pd.Series(dtype="float64")
    ingresos = pd.to_numeric(finanzas.loc["Total Revenue"], errors="coerce")
    beneficios = pd.to_numeric(finanzas.loc["Net Income"], errors="coerce")
    margen = (beneficios / ingresos.replace(0, pd.NA)) * 100
    return margen.dropna().sort_index().tail(4)


def portfolio_backtest(tickers: list[str], weights: list[float], capital: float, period: str) -> tuple[dict, str | None]:
    precios = yf_download_close(tuple(tickers), period)
    if precios.empty:
        return {}, "No se pudieron obtener datos históricos para los tickers ingresados."
    precios = precios.dropna(axis=1, how="all").ffill().dropna(how="any")
    tickers_ok = [ticker for ticker in tickers if ticker in precios.columns]
    if not tickers_ok:
        return {}, "Ningún ticker válido encontrado."
    pesos_ok = [weights[tickers.index(ticker)] for ticker in tickers_ok]
    suma = sum(pesos_ok)
    if suma <= 0:
        return {}, "Los pesos válidos deben ser mayores a cero."
    pesos_ok = [peso / suma for peso in pesos_ok]
    ret_diarios = precios[tickers_ok].pct_change().dropna()
    if ret_diarios.empty:
        return {}, "No hay datos suficientes para calcular rendimientos."
    ret_acum = (1 + ret_diarios).cumprod()
    valor_portafolio = capital * ret_acum.dot(pesos_ok)

    spy_hist = yf_history("SPY", period)
    if spy_hist.empty or "Close" not in spy_hist.columns:
        return {}, "No se pudo obtener SPY para la comparación del simulador."
    spy_close = pd.to_numeric(spy_hist["Close"], errors="coerce").dropna()
    spy_alineado = spy_close.reindex(valor_portafolio.index, method="ffill").dropna()
    valor_portafolio = valor_portafolio.reindex(spy_alineado.index).dropna()
    spy_alineado = spy_alineado.reindex(valor_portafolio.index).dropna()
    if valor_portafolio.empty or spy_alineado.empty or spy_alineado.iloc[0] == 0:
        return {}, "No hay datos alineados suficientes para comparar contra SPY."
    valor_spy = capital * (spy_alineado / spy_alineado.iloc[0])

    capital_final = float(valor_portafolio.iloc[-1])
    capital_spy_final = float(valor_spy.iloc[-1])
    rendimiento_total = ((capital_final - capital) / capital) * 100
    rendimiento_spy = ((capital_spy_final - capital) / capital) * 100
    rolling_max = valor_portafolio.cummax()
    drawdown = float(((valor_portafolio - rolling_max) / rolling_max).min() * 100)
    return {
        "tickers_ok": tickers_ok,
        "tickers_faltantes": [ticker for ticker in tickers if ticker not in tickers_ok],
        "pesos_ok": pesos_ok,
        "ret_acum": ret_acum,
        "valor_portafolio": valor_portafolio,
        "valor_spy": valor_spy,
        "capital_final": capital_final,
        "capital_spy_final": capital_spy_final,
        "rendimiento_total": rendimiento_total,
        "rendimiento_spy": rendimiento_spy,
        "alpha": rendimiento_total - rendimiento_spy,
        "drawdown": drawdown,
    }, None


# =====================================================================
# AI LAYER — GROQ ()
# =====================================================================
def analisis_ia(ticker: str, nombre: str, sector: str, precio: float | None,
                per, beta, market_cap_str: str, margen: float | None,
                max52: float | None, min52: float | None,
                contexto_tecnico: dict | None = None) -> str:
    """Genera un análisis educativo con Groq usando solo datos provistos por la app."""
    if not GROQ_API_KEY:
        return "⚠️ Análisis IA no disponible: configurá GROQ_API_KEY en los secrets de Streamlit."

    contexto_tecnico = contexto_tecnico or {}
    rendimiento_periodo = contexto_tecnico.get("rendimiento_periodo")
    volatilidad_anual = contexto_tecnico.get("volatilidad_anual")
    media_50 = contexto_tecnico.get("media_50")
    media_200 = contexto_tecnico.get("media_200")
    indicadores = f"""
- Empresa: {nombre} ({ticker})
- Sector: {sector}
- Cotización Finnhub: {f'${precio:.2f}' if isinstance(precio, (int, float)) else 'N/D'}
- PER: {f'{per:.1f}x' if isinstance(per, (int, float)) else 'N/D'}
- Beta: {f'{beta:.2f}' if isinstance(beta, (int, float)) else 'N/D'}
- Market Cap: {market_cap_str}
- Margen Neto: {f'{margen:.1f}%' if isinstance(margen, (int, float)) else 'N/D'}
- Máximo 52 semanas: {f'${max52:.2f}' if isinstance(max52, (int, float)) and max52 else 'N/D'}
- Mínimo 52 semanas: {f'${min52:.2f}' if isinstance(min52, (int, float)) and min52 else 'N/D'}
- Rendimiento histórico del período: {f'{rendimiento_periodo:.1f}%' if isinstance(rendimiento_periodo, (int, float)) else 'N/D'}
- Volatilidad anualizada estimada: {f'{volatilidad_anual:.1f}%' if isinstance(volatilidad_anual, (int, float)) else 'N/D'}
- Media móvil 50 ruedas: {f'${media_50:.2f}' if isinstance(media_50, (int, float)) else 'N/D'}
- Media móvil 200 ruedas: {f'${media_200:.2f}' if isinstance(media_200, (int, float)) else 'N/D'}
"""
    prompt = f"""
Actuás como un analista financiero profesional senior.

Tu objetivo es hacer UN ANÁLISIS, no repetir datos.

Analizá la acción {nombre} ({ticker}) usando estos datos:
- Precio: {precio}
- PER: {per}
- Beta: {beta}
- Capitalización: {market_cap_str}
- Margen: {margen}
- Máximo 52 semanas: {max52}
- Mínimo 52 semanas: {min52}

REGLAS IMPORTANTES:
- NO repitas los datos tal cual (precio, PER, margen ya están dados)
- NO digas “la empresa tiene margen X” si ya está en los datos
- Interpretá siempre los números (alto, bajo, caro, barato, riesgoso, estable)
- Cada bullet debe aportar información nueva
- Máximo 10–12 líneas total

FORMATO:

📊 RESUMEN GENERAL
- 2 bullets con visión global (sin repetir métricas)

💰 VALUACIÓN
- Interpretación del PER (caro/barato/justificado)
- Relación con crecimiento o expectativas del mercado

📈 RENTABILIDAD
- Qué dicen los márgenes sobre la calidad del negocio
- Si la empresa es eficiente o no (sin repetir % literal)

⚠️ RIESGO
- Qué implica la beta en términos simples
- Nivel de riesgo general (bajo/medio/alto)

📉 TENDENCIA
- Interpretación del rango 52 semanas
- Tendencia general (alcista/bajista/lateral)

🧠 CONCLUSIÓN FINAL
- 2 bullets con opinión educativa clara
- No repetir información previa
{indicadores}
"""

    import re
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "Sos un analista financiero junior educativo. No inventás información."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=35
        )
        if r.status_code == 200:
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            content = re.sub(r"\n{2,}", "\n", content)
            content = "\n".join([line for line in content.split("\n") if line.strip()])
            return content.strip()
        if r.status_code == 429:
            return "⏳ El servicio de IA está ocupado en este momento. Esperá unos segundos y volvé a intentarlo."
        return f"⚠️ Error al contactar Groq (código {r.status_code})."
    except requests.RequestException as e:
        return f"⚠️ Error al contactar Groq: {e}"


@st.cache_data(ttl=1800, show_spinner=False)          # 30 min — mismo ticker no re-llama a Groq
def analisis_ia_cached(
    ticker: str, nombre: str, sector: str,
    precio: float | None, per: float | None, beta: float | None,
    market_cap_str: str, margen: float | None,
    max52: float | None, min52: float | None,
    rendimiento_periodo: float | None, volatilidad_anual: float | None,
    media_50: float | None, media_200: float | None,
) -> str:
    """Wrapper cacheable de analisis_ia. Separa los parámetros del dict
    para que st.cache_data pueda hashearlos correctamente."""
    contexto = {
        "rendimiento_periodo": rendimiento_periodo,
        "volatilidad_anual": volatilidad_anual,
        "media_50": media_50,
        "media_200": media_200,
    }
    return analisis_ia(ticker, nombre, sector, precio, per, beta,
                       market_cap_str, margen, max52, min52, contexto)


def fmt_market_cap(mc) -> str:
    if not isinstance(mc, (int, float)) or mc == 0:
        return "N/A"
    if mc >= 1e12: return f"${mc/1e12:.2f}T"
    elif mc >= 1e9: return f"${mc/1e9:.2f}B"
    return f"${mc/1e6:.2f}M"

def risk_badge(beta) -> str:
    if not isinstance(beta, (int, float)):
        return '<span class="badge-gris">Beta N/D</span>'
    b = round(beta, 2)
    if beta < 0.9:  return f'<span class="badge-verde">🛡️ ESTABLE · β {b}</span>'
    elif beta > 1.2: return f'<span class="badge-rojo">⚡ VOLÁTIL · β {b}</span>'
    return f'<span class="badge-gris">⚖️ MODERADO · β {b}</span>'

def return_badge(pct: float) -> str:
    p = round(pct, 2)
    if pct > 10:  return f'<span class="badge-verde">▲ +{p}%</span>'
    elif pct < 0: return f'<span class="badge-rojo">▼ {p}%</span>'
    return f'<span class="badge-azul">→ +{p}%</span>'

def safe_html(value) -> str:
    return html.escape(str(value)) if value is not None else ""

# =====================================================================
# SIDEBAR
# =====================================================================
with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding:28px 12px 20px;">'
        '<svg width="72" height="72" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="display:block; margin:0 auto 14px;">'
        '<circle cx="32" cy="32" r="32" fill="#161b22"/>'
        '<circle cx="32" cy="32" r="31" fill="none" stroke="#1f6feb" stroke-width="1"/>'
        '<line x1="19" y1="14" x2="19" y2="20" stroke="#3fb950" stroke-width="1.8" stroke-linecap="round"/>'
        '<rect x="15" y="20" width="8" height="16" rx="1.5" fill="#3fb950"/>'
        '<line x1="19" y1="36" x2="19" y2="42" stroke="#3fb950" stroke-width="1.8" stroke-linecap="round"/>'
        '<line x1="32" y1="18" x2="32" y2="24" stroke="#58a6ff" stroke-width="1.8" stroke-linecap="round"/>'
        '<rect x="28" y="24" width="8" height="20" rx="1.5" fill="#58a6ff"/>'
        '<line x1="32" y1="44" x2="32" y2="50" stroke="#58a6ff" stroke-width="1.8" stroke-linecap="round"/>'
        '<line x1="45" y1="16" x2="45" y2="22" stroke="#f85149" stroke-width="1.8" stroke-linecap="round"/>'
        '<rect x="41" y="22" width="8" height="12" rx="1.5" fill="#f85149"/>'
        '<line x1="45" y1="34" x2="45" y2="40" stroke="#f85149" stroke-width="1.8" stroke-linecap="round"/>'
        '</svg>'
        '<div style="font-family:\'DM Mono\',monospace; font-size:0.80rem; font-weight:700; color:#1f6feb; letter-spacing:0.20em; text-transform:uppercase; line-height:1.1;">PRINCIPIOS</div>'
        '<div style="font-family:\'Playfair Display\',serif; font-size:1.45rem; font-weight:700; color:#f0f6fc; letter-spacing:0.04em; margin-top:3px;">Finanzas</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("""
    <div style="color:#c9d1d9; font-size:1.0rem; line-height:2.1; padding: 0 4px;">
    <b style="color:#f0f6fc; font-size:1.05rem;">Recorrido sugerido:</b><br>
    <span style="color:#1f6feb; font-size:1.1rem;">①</span> <span style="font-size:1.0rem;">Academia — aprendé los conceptos</span><br>
    <span style="color:#1f6feb; font-size:1.1rem;">②</span> <span style="font-size:1.0rem;">Guía — entendé cómo operar</span><br>
    <span style="color:#1f6feb; font-size:1.1rem;">③</span> <span style="font-size:1.0rem;">Buscador — analizá empresas</span><br>
    <span style="color:#1f6feb; font-size:1.1rem;">④</span> <span style="font-size:1.0rem;">Simulador — probá tu cartera</span><br>
    <span style="color:#1f6feb; font-size:1.1rem;">⑤</span> <span style="font-size:1.0rem;">Cierre — próximos pasos</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="color:#484f58; font-size:0.80rem; line-height:1.7; padding: 0 4px;">
    <b style="color:#8b949e;">⚠️ Disclaimer</b><br>
    Contenido con fines exclusivamente educativos. No constituye asesoramiento financiero ni recomendación de inversión.
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div style="color:#484f58; font-size:0.76rem; text-align:center;">Datos vía Finnhub + yfinance · Mercados internacionales</div>', unsafe_allow_html=True)

# =====================================================================
# HEADER
# =====================================================================
col_title, _ = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div style="padding:36px 0 28px;">
        <div style="font-family:'DM Mono',monospace; font-size:0.7rem; font-weight:700;
                    color:#1f6feb; letter-spacing:0.22em; text-transform:uppercase; margin-bottom:10px;">
            ▸ PRINCIPIOS PARA FINANZAS PERSONALES
        </div>
        <div class="hero-title">PLATAFORMA<br>FINANCIERA EDUCATIVA</div>
        <div style="width:56px; height:3px; background:linear-gradient(90deg,#1f6feb,#58a6ff); border-radius:2px; margin-top:14px;"></div>
        <div class="hero-sub" style="margin-top:12px;">Tu puente entre el ahorro y la inversión inteligente</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================================
# TABS
# =====================================================================
solapa_academia, solapa_guia, solapa_buscador, solapa_simulador, solapa_cierre = st.tabs([
    "📚 Academia Financiera",
    "🚀 Guía de Inversión",
    "📊 Buscador de Acciones",
    "🕰️ Simulador de Portafolio",
    "🎓 Fin del Recorrido"
])

# =====================================================================
# TAB 1: ACADEMIA FINANCIERA
# =====================================================================
with solapa_academia:
    st.markdown('<div class="section-label">Módulo Educativo</div>', unsafe_allow_html=True)
    st.markdown("## 📚 Academia Financiera")
    st.markdown('<p style="color:#8b949e;">Dominá los conceptos clave antes de invertir. Expandí cada categoría para explorar.</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown("#### 🟣 Análisis Técnico vs. Análisis Fundamental")
    with st.expander("Análisis Fundamental — ¿Vale lo que cuesta?"):
        st.markdown("""
        Estudia la **salud real del negocio**: balances, ganancias, deudas, ventajas competitivas, management.

        **Pregunta central:** ¿El precio de la acción refleja el valor real de la empresa?

        **Herramientas:** PER, Margen Neto, ROE, EV/EBITDA, flujo de caja libre.

        **Horizonte:** Largo plazo (meses a años). El inversor fundamental clásico es Warren Buffett.

        > *"El precio es lo que pagás. El valor es lo que recibís."* — W. Buffett
        """)
    with st.expander("Análisis Técnico — ¿Hacia dónde va el precio?"):
        st.markdown("""
        Estudia **patrones en los gráficos de precios y volumen**, asumiendo que la historia se repite y que toda la información está reflejada en el precio.

        **Pregunta central:** ¿Qué dice el comportamiento histórico del precio sobre su dirección futura?

        **Herramientas:** Medias móviles, RSI, MACD, soportes y resistencias, velas japonesas.

        **Horizonte:** Corto/mediano plazo. Muy usado por traders.

        | | Fundamental | Técnico |
        |--|------------|---------|
        | Estudia | El negocio | El precio |
        | Horizonte | Largo plazo | Corto/mediano |
        | Pregunta | ¿Vale la pena? | ¿Cuándo comprar/vender? |

        > Muchos inversores combinan ambos: usan el fundamental para **elegir** la empresa y el técnico para **decidir el momento** de entrada.
        """)


    st.markdown("#### 🔵 Renta Fija & Renta Variable")
    with st.expander("Renta Fija — El préstamo con promesa"):
        st.markdown("""
        **¿Qué es?** El emisor se compromete a devolver el capital más un interés pactado en fechas determinadas.
        El riesgo es menor porque el flujo de fondos es **predecible**. Sabés de antemano cuánto vas a cobrar y cuándo.
        > *Ejemplos: plazo fijo, bonos del Estado, obligaciones negociables.*
        """)
    with st.expander("Renta Variable — La participación en el negocio"):
        st.markdown("""
        **¿Qué es?** No hay promesas de pago ni intereses fijos. Tu ganancia depende de que el negocio crezca y sea valorado por el mercado.
        El riesgo es mayor, pero el potencial de ganancia es técnicamente **ilimitado**.
        > *Ejemplos: acciones, CEDEARs, ETFs de renta variable.*
        """)

    st.markdown("#### 🟡 Conceptos Fundamentales de Dinero")
    with st.expander("Tasa Nominal (TNA) vs. Tasa Real — La verdad de la milanesa"):
        st.markdown("""
        **Tasa Nominal:** El número de vidriera. La rentabilidad que promete un banco o bono *antes* de considerar la inflación. Si invertís $1.000 y al año te devuelven $1.500, tu tasa nominal es **50%**.

        **Tasa Real:** Mide cuánto poder de compra ganaste *realmente*, restándole la inflación a la tasa nominal.
        > Si ganaste 50% nominal pero la inflación fue 60%, tu tasa real es **negativa**: tenés más billetes, pero comprás *menos* cosas.
        """)
    with st.expander("Interés Compuesto — La bola de nieve"):
        st.markdown("""
        La magia de las finanzas a largo plazo. Ganás intereses no solo sobre tu capital original, sino también sobre los intereses ya acumulados.

        **Ejemplo concreto con $10.000 al 10% anual:**

        | Año | Interés Simple | Interés Compuesto |
        |-----|---------------|-------------------|
        | 1   | $11.000       | $11.000           |
        | 5   | $15.000       | $16.105           |
        | 10  | $20.000       | $25.937           |
        | 20  | $30.000       | $67.275           |
        | 30  | $40.000       | $174.494          |

        **¿Por qué la diferencia?**
        - **Interés simple:** cada año ganás $1.000 (siempre el 10% de los $10.000 originales).
        - **Interés compuesto:** el año 2 ganás el 10% de $11.000 = $1.100. El año 3, de $12.100 = $1.210... y así crece cada vez más rápido.

        > La clave es el **tiempo**. Cuanto antes empezás, más potente es el efecto.
        """)
    with st.expander("Liquidez — La velocidad del dinero"):
        st.markdown("""
        La velocidad a la que podés convertir tu inversión de nuevo en efectivo **sin perder valor**.
        - 🏠 **Casa:** liquidez baja — tardás meses en venderla.
        - 📊 **Acción de Apple:** liquidez alta — la vendés en segundos.
        """)
    with st.expander("Diversificación — No pongas todos los huevos en la misma canasta"):
        st.markdown("""
        Repartir tu capital en diferentes empresas, sectores o países para que si a uno le va mal, los otros **amortigüen la pérdida**.
        > Un portafolio con 20 acciones de sectores distintos es mucho más resistente que uno con una sola.
        """)

    st.markdown("#### 🟢 Instrumentos Financieros")
    with st.expander("Bonos — Deuda del Estado"):
        st.markdown("""
        Deuda emitida por un Estado. Le prestás dinero al gobierno a cambio de capital más interés fijo en fechas predeterminadas.
        > *Riesgo: si el Estado no puede pagar, hay default. Argentina tiene historia en esto.*
        """)
    with st.expander("ONs (Obligaciones Negociables) — Deuda Privada"):
        st.markdown("""
        Igual que bonos, pero emitidos por **empresas privadas** (YPF, Pampa, etc.). Mayor tasa que bonos soberanos para compensar el riesgo corporativo.
        """)
    with st.expander("Acciones — Ser dueño de una fracción"):
        st.markdown("""
        Al comprar una acción, te convertís en dueño de una fracción de la empresa. Ganás por:
        1. **Apreciación del precio** en el mercado.
        2. **Dividendos** — reparto de ganancias.
        > Ninguna de las dos está garantizada.
        """)
    with st.expander("CEDEARs — Acciones extranjeras desde Argentina"):
        st.markdown("""
        Certificados que cotizan en el mercado local (en pesos o dólares) y representan acciones de empresas extranjeras (Apple, Google, Tesla...).
        Funcionan con **ratios de conversión**: un CEDEAR puede equivaler a 1/5 o 1/10 de una acción completa.
        """)
    with st.expander("ETFs — Fondos Índice"):
        st.markdown("""
        Un fondo que agrupa muchas acciones. Comprar **SPY** equivale a comprar un pedacito de las **500 empresas más grandes de EE.UU.**
        Ventajas: diversificación instantánea, comisiones bajas, alta liquidez.
        """)

    st.markdown("#### 🔴 Métricas Financieras")
    with st.expander("PER (Price-to-Earnings) — La etiqueta del precio"):
        st.markdown("""
        Indica **cuántos años tardarías en recuperar tu inversión** si la empresa mantuviera sus ganancias constantes.

        | PER | Interpretación |
        |-----|----------------|
        | < 15 | Posiblemente barata o sector maduro |
        | 15–25 | Valuación razonable |
        | > 30 | Mercado descuenta alto crecimiento futuro |

        > Siempre compará el PER con empresas del mismo sector.
        """)
    with st.expander("Margen Neto — La prueba de la verdad"):
        st.markdown("""
        De cada **$100 que vende**, ¿cuántos le quedan limpios a la empresa después de pagar todo?
        > Un 25% en tecnología es normal. Un 5% en supermercados puede ser excelente. El sector es clave.
        """)
    with st.expander("Beta (β) — El termómetro del riesgo"):
        st.markdown("""
        Qué tanto se mueve una acción respecto al **mercado general (S&P 500)**.

        | Beta | Comportamiento |
        |------|----------------|
        | < 0.9 | Más estable que el mercado |
        | 0.9 – 1.2 | Similar al mercado |
        | > 1.2 | Más volátil que el mercado |

        > β = 1.5: sube 15% cuando el mercado sube 10%, pero también cae 15% cuando baja 10%.
        """)
    with st.expander("Market Cap — El tamaño del jugador"):
        st.markdown("""
        **Precio de la acción × cantidad de acciones emitidas** = tamaño total de la empresa valuada por el mercado.

        **¿Para qué sirve?** Te dice con qué tipo de empresa estás tratando:

        | Categoría | Market Cap | Características |
        |-----------|-----------|-----------------|
        | Mega Cap | > $200B | Estables, líderes globales (Apple, Microsoft) |
        | Large Cap | $10B – $200B | Empresas consolidadas, menor volatilidad |
        | Mid Cap | $2B – $10B | Equilibrio entre crecimiento y estabilidad |
        | Small Cap | < $2B | Mayor potencial de crecimiento, más riesgo |

        > Una empresa puede tener muchas ventas pero bajo Market Cap si el mercado desconfía de su futuro. Y viceversa.
        """)

    st.markdown("#### 🟠 Riesgo & Volatilidad")
    with st.expander("Volatilidad — El serrucho del precio"):
        st.markdown("""
        Mide la brusquedad de los saltos de precio. Un activo muy volátil puede hacerte ganar mucho rápido, pero también perderlo. Es el **costo emocional** de invertir en bolsa.
        > El S&P 500 históricamente cae más del 10% en algún momento la mayoría de los años, pero a largo plazo siempre lo recuperó.
        """)
    with st.expander("Máximos y Mínimos de 52 semanas — Techo y piso"):
        st.markdown("""
        El precio más alto (techo) y más bajo (piso) de la acción en el **último año**. Referencias clave para entender en qué posición del rango anual cotiza la empresa.
        """)

# =====================================================================
# TAB 2: GUÍA DE INVERSIÓN
# =====================================================================
with solapa_guia:
    st.markdown('<div class="section-label">Hoja de Ruta</div>', unsafe_allow_html=True)
    st.markdown("## 🚀 Guía del Inversor")
    st.markdown('<p style="color:#8b949e;">El camino hacia la inversión inteligente requiere método, paciencia y criterio.</p>', unsafe_allow_html=True)
    st.divider()

    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown("""
        <div class="fin-card">
            <div class="section-label">Paso 01</div>
            <h4 style="color:#f0f6fc; margin:0 0 10px;">El Ecosistema: Mercado Secundario</h4>
            <p style="color:#8b949e; font-size:0.9rem; line-height:1.7; margin:0;">
            Al invertir en bolsa, operás en el <b style="color:#c9d1d9;">Mercado Secundario</b>. Pensalo como el mercado automotor: cuando comprás un auto usado, el dinero no va a la fábrica, sino al dueño anterior. Al comprar acciones, no le estás inyectando fondos a la empresa, sino adquiriendo la participación de otro inversor. El precio responde exclusivamente a la oferta y demanda.
            </p>
        </div>
        <div class="fin-card">
            <div class="section-label">Paso 02</div>
            <h4 style="color:#f0f6fc; margin:0 0 10px;">El Vehículo: Broker vs. Banco</h4>
            <p style="color:#8b949e; font-size:0.9rem; line-height:1.7; margin:0 0 12px;">
            Para acceder necesitás un <b style="color:#c9d1d9;">Broker</b> (o ALyC en Argentina). Los bancos tienen como negocio principal los préstamos y tarjetas. Los Brokers son especialistas en mercados de capitales: plataformas superiores, mayor velocidad de ejecución y comisiones más bajas.
            </p>
            <div style="border-top:1px solid #21262d; padding-top:12px; margin-top:4px;">
                <div style="color:#8b949e; font-size:0.78rem; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">🇦🇷 Brokers habituales en Argentina</div>
                <div style="display:flex; flex-direction:column; gap:6px;">
                    <div style="background:rgba(31,111,235,0.07); border:1px solid rgba(88,166,255,0.15); border-radius:7px; padding:8px 12px;">
                        <span style="color:#58a6ff; font-weight:600; font-size:0.85rem;">Bull Market Brokers</span>
                        <span style="color:#8b949e; font-size:0.82rem;"> — Foco en acciones, CEDEARs y ON. Plataforma moderna.</span>
                    </div>
                    <div style="background:rgba(31,111,235,0.07); border:1px solid rgba(88,166,255,0.15); border-radius:7px; padding:8px 12px;">
                        <span style="color:#58a6ff; font-weight:600; font-size:0.85rem;">PPI (Portfolio Personal Inversiones)</span>
                        <span style="color:#8b949e; font-size:0.82rem;"> — Uno de los más usados, amplia variedad de instrumentos.</span>
                    </div>
                    <div style="background:rgba(31,111,235,0.07); border:1px solid rgba(88,166,255,0.15); border-radius:7px; padding:8px 12px;">
                        <span style="color:#58a6ff; font-weight:600; font-size:0.85rem;">InvertirOnline (IOL)</span>
                        <span style="color:#8b949e; font-size:0.82rem;"> — Popular entre principiantes, interface amigable.</span>
                    </div>
                    <div style="background:rgba(31,111,235,0.07); border:1px solid rgba(88,166,255,0.15); border-radius:7px; padding:8px 12px;">
                        <span style="color:#58a6ff; font-weight:600; font-size:0.85rem;">Ecovalores</span>
                        <span style="color:#8b949e; font-size:0.82rem;"> — ALyC con buena reputación y atención personalizada.</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_der:
        st.markdown("""
        <div class="fin-card">
            <div class="section-label">Paso 03</div>
            <h4 style="color:#f0f6fc; margin:0 0 10px;">Tu Perfil de Riesgo</h4>
            <p style="color:#8b949e; font-size:0.85rem; margin:0 0 12px;">Antes de elegir cualquier inversión, es fundamental entender cuánta volatilidad podés tolerar emocional y financieramente.</p>
            <div style="display:flex; flex-direction:column; gap:8px;">
                <div style="background:rgba(35,134,54,0.08); border:1px solid rgba(63,185,80,0.2); border-radius:8px; padding:12px 14px;">
                    <span style="color:#3fb950; font-weight:600; font-size:0.82rem;">🛡️ CONSERVADOR</span>
                    <p style="color:#8b949e; font-size:0.83rem; margin:6px 0 0; line-height:1.6;">Prioriza preservar el capital y ganarle a la inflación. Preferencia por plazos fijos, bonos y FCI de renta fija. Tolera poca variación en el valor de su cartera.</p>
                </div>
                <div style="background:rgba(31,111,235,0.08); border:1px solid rgba(88,166,255,0.2); border-radius:8px; padding:12px 14px;">
                    <span style="color:#58a6ff; font-weight:600; font-size:0.82rem;">⚖️ MODERADO</span>
                    <p style="color:#8b949e; font-size:0.83rem; margin:6px 0 0; line-height:1.6;">Equilibrio entre seguridad y crecimiento. Mezcla de renta fija y variable. Puede tolerar caídas temporales del 10–20% si el horizonte es de mediano plazo (2–5 años).</p>
                </div>
                <div style="background:rgba(248,81,73,0.08); border:1px solid rgba(248,81,73,0.2); border-radius:8px; padding:12px 14px;">
                    <span style="color:#f85149; font-weight:600; font-size:0.82rem;">⚡ AGRESIVO</span>
                    <p style="color:#8b949e; font-size:0.83rem; margin:6px 0 0; line-height:1.6;">Busca rendimientos extraordinarios a largo plazo. Alta exposición a acciones, ETFs y activos volátiles. Puede ver caer su cartera un 40–50% sin entrar en pánico, confiando en la recuperación.</p>
                </div>
            </div>
        </div>
        <div class="fin-card">
            <div class="section-label">Paso 04</div>
            <h4 style="color:#f0f6fc; margin:0 0 10px;">La Ejecución: Caja de Puntas</h4>
            <div style="font-family:'DM Mono',monospace; font-size:0.82rem; display:flex; flex-direction:column; gap:4px;">
                <div style="display:flex; justify-content:space-between; padding:8px 12px; background:rgba(63,185,80,0.08); border-radius:6px;">
                    <span style="color:#3fb950;">BID (Compra)</span>
                    <span style="color:#8b949e;">Precio máx. de compradores</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:8px 12px; background:rgba(248,81,73,0.08); border-radius:6px;">
                    <span style="color:#f85149;">ASK (Venta)</span>
                    <span style="color:#8b949e;">Precio mín. de vendedores</span>
                </div>
            </div>
        </div>
        <div class="fin-card">
            <div class="section-label">Paso 05</div>
            <h4 style="color:#f0f6fc; margin:0 0 10px;">Tipos de Órdenes</h4>
            <div style="display:flex; flex-direction:column; gap:10px; margin-top:4px;">
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#58a6ff; font-weight:600; font-size:0.85rem;">📈 A Precio de Mercado</div>
                    <div style="color:#8b949e; font-size:0.83rem; margin-top:4px;">Velocidad. Comprás al mejor precio disponible ahora. Ejecución garantizada.</div>
                </div>
                <div style="border-left:3px solid #238636; padding-left:14px;">
                    <div style="color:#3fb950; font-weight:600; font-size:0.85rem;">🎯 A Precio Límite</div>
                    <div style="color:#8b949e; font-size:0.83rem; margin-top:4px;">Control. Fijás un precio exacto. Solo se ejecuta si el mercado lo alcanza.</div>
                </div>
            </div>
        </div>
        <div class="fin-card" style="border-color:rgba(210,183,96,0.3); background:rgba(210,183,96,0.04);">
            <div style="color:#d2b760; font-size:0.7rem; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; font-family:'DM Mono',monospace; margin-bottom:8px;">💡 Regla de Oro</div>
            <p style="color:#c9d1d9; font-size:0.9rem; line-height:1.7; margin:0; font-style:italic;">
            "Nunca inviertas dinero que no podés permitirte perder. El primer objetivo es preservar el capital; el segundo, hacerlo crecer."
            </p>
        </div>
        """, unsafe_allow_html=True)

# =====================================================================
# TAB 3: BUSCADOR DE ACCIONES
# =====================================================================
with solapa_buscador:
    st.markdown('<div class="section-label">Análisis Fundamental</div>', unsafe_allow_html=True)
    st.markdown("## 📊 Buscador de Acciones")

    # Aviso educativo
    st.markdown("""
    <div style="background:rgba(31,111,235,0.07); border:1px solid rgba(88,166,255,0.2); border-radius:10px; padding:14px 18px; margin-bottom:16px;">
    <div style="color:#58a6ff; font-weight:600; font-size:0.88rem; margin-bottom:6px;">📘 Esto es un ejemplo de Análisis Fundamental</div>
    <div style="color:#8b949e; font-size:0.85rem; line-height:1.7;">
    Este buscador incluye <b style="color:#c9d1d9;">acciones de EE.UU.</b> (NYSE/NASDAQ) y, si querés probar empresas argentinas, podés usar sus <b style="color:#c9d1d9;">ADRs</b> que cotizan en Wall Street:<br>
    <span style="font-family:'DM Mono',monospace; color:#58a6ff;">YPF · GGAL · BMA · SUPV · CEPU · LOMA · PAM · TEO · TGS · MELI</span><br><br>
    Los datos y el análisis son <b style="color:#c9d1d9;">exclusivamente educativos</b> para aprender a interpretar indicadores. No constituyen recomendaciones de inversión. Te recomendamos haber leído las secciones de <b style="color:#c9d1d9;">Academia</b> y <b style="color:#c9d1d9;">Guía</b> antes de usar este buscador.
    </div>
    </div>
    """, unsafe_allow_html=True)

    col_inp, col_tip = st.columns([2, 3], gap="large")
    with col_inp:
        if "ticker_analizado" not in st.session_state:
            st.session_state.ticker_analizado = None

        if "perfil" not in st.session_state:
            st.session_state.perfil = None

        if "quote" not in st.session_state:
            st.session_state.quote = None

        if "metrics" not in st.session_state:
            st.session_state.metrics = None
        ticker_input = st.text_input(
            "Ticker",
            placeholder="AAPL, MSFT, GOOG, YPF...",
            label_visibility="collapsed"
        ).upper().strip()

        analizar = st.button("🔍 Analizar Empresa", use_container_width=True)

        if analizar and ticker_input:
            st.session_state.ticker_analizado = ticker_input

            with st.spinner(f"Consultando datos de mercado para {ticker_input}..."):
                st.session_state.perfil = fh_profile(ticker_input)
                st.session_state.quote = fh_quote(ticker_input)
                st.session_state.metrics = fh_metrics(ticker_input)

        ticker = st.session_state.ticker_analizado
    with col_tip:
        st.markdown("""
        <div style="background:rgba(31,111,235,0.08); border:1px solid rgba(88,166,255,0.15); border-radius:8px; padding:12px 16px; margin-top:4px;">
        <span style="color:#58a6ff; font-size:0.82rem;">💡 <b>¿Qué es un ticker?</b> La sigla con la que cotiza una empresa.
        Apple = <span class="mono">AAPL</span> · Google = <span class="mono">GOOG</span> · Tesla = <span class="mono">TSLA</span> · YPF = <span class="mono">YPF</span></span>
        </div>
        """, unsafe_allow_html=True)
        perfil = None
        quote = None
        metrics = None

    if ticker:
        perfil = st.session_state.perfil
        quote = st.session_state.quote
        metrics = st.session_state.metrics

        if not perfil or not perfil.get("name"):
            st.error("❌ Ticker no encontrado. Verificá la ortografía.")
        else:
            st.divider()
            nombre    = perfil.get("name", ticker)
            sector    = perfil.get("finnhubIndustry", "N/A")
            pais      = perfil.get("country", "N/A")
            mc_raw    = perfil.get("marketCapitalization", 0)
            mc        = mc_raw * 1e6 if mc_raw else None  # Finnhub da en millones
            mc_str    = fmt_market_cap(mc)

            precio_actual = quote.get("c", None)
            precio_prev   = quote.get("pc", None)
            cambio_pct    = ((precio_actual - precio_prev) / precio_prev * 100) if precio_actual and precio_prev and precio_prev != 0 else None

            per   = metrics.get("peBasicExclExtraTTM", None) or metrics.get("peTTM", None)
            beta  = metrics.get("beta", None)
            max52 = metrics.get("52WeekHigh", 0)
            min52 = metrics.get("52WeekLow", 0)
            margen_neto = metrics.get("netProfitMarginTTM", None)
            roe   = metrics.get("roeTTM", None)

            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:24px;">
                <div>
                    <h2 style="margin:0; color:#f0f6fc; font-family:'Playfair Display',serif;">{nombre}</h2>
                    <div style="color:#8b949e; font-size:0.82rem; margin-top:4px; font-family:'DM Mono',monospace;">{ticker} · {sector} · {pais}</div>
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">{risk_badge(beta)}</div>
            </div>
            """, unsafe_allow_html=True)

            # MÉTRICAS
            st.markdown('<div class="section-label">Radiografía Fundamental</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "PER",
                f"{per:.1f}x" if per else "N/A",
                help="Años para recuperar la inversión si las ganancias se mantienen constantes. PER < 15 = barato ? 15-25 = razonable ? > 30 = caro"
            )
            c2.metric(
                "Market Cap",
                mc_str,
                help="Precio ? acciones totales = tamaño de la empresa en bolsa. Mega Cap (>$200B): Apple, Google. Large Cap ($10B-$200B). Mid Cap ($2B-$10B). Small Cap (<$2B)."
            )
            c3.metric(
                "Beta",
                f"{round(beta,2)}" if isinstance(beta, (int, float)) else "N/A",
                help="Volatilidad respecto al S&P 500. ? < 0.9 = más estable ? ? 0.9-1.2 = similar ? ? > 1.2 = más volátil"
            )
            c4.metric(
                "Margen Neto",
                f"{margen_neto:.1f}%" if isinstance(margen_neto, (int, float)) else "N/A",
                help="De cada $100 vendidos, cuántos quedan como ganancia neta."
            )
            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Max 52s", f"${max52:,.2f}" if max52 else "N/A")
            c6.metric("Min 52s", f"${min52:,.2f}" if min52 else "N/A")
            c7.metric(
                "ROE",
                f"{roe:.1f}%" if isinstance(roe, (int, float)) else "N/A",
                help="Return on Equity: cuanta ganancia genera la empresa por cada peso de capital propio. ROE > 15% es generalmente bueno."
            )
            c8.metric("Sector", sector[:28] + "..." if len(str(sector)) > 28 else sector)

            st.divider()

            # GRAFICOS HISTORICOS - yfinance
            with st.spinner("Cargando historial de precios..."):
                hist_1y = yf_history(ticker, "1y")
            contexto_tecnico = technical_snapshot(hist_1y)

            st.markdown('<div class="section-label">Histórico de Mercado</div>', unsafe_allow_html=True)
            tipo_grafico = st.radio("Tipo de grafico", ["Linea", "Velas"], horizontal=True, label_visibility="collapsed")
            tab_1y, tab_5y = st.tabs(["Último año", "Últimos 5 años"])

            def render_historial(period_key: str):
                hist = hist_1y if period_key == "1y" else yf_history(ticker, period_key)
                if hist.empty:
                    st.info("Sin datos historicos suficientes para este periodo.")
                    return
                ret = period_return(hist["Close"])
                if isinstance(ret, (int, float)):
                    st.markdown(f"**{ticker}:** {return_badge(ret)}", unsafe_allow_html=True)
                fig = build_historical_figure(hist, ticker, tipo_grafico)
                if fig is None:
                    st.info("No hay datos suficientes para renderizar el grafico.")
                    return
                st.plotly_chart(fig, use_container_width=True)

            with tab_1y:
                render_historial("1y")
            with tab_5y:
                render_historial("5y")

            st.divider()

            # MARGEN NETO - grafico historico con yfinance cuando esta disponible
            st.markdown('<div class="section-label">Rentabilidad Histórica</div>', unsafe_allow_html=True)
            st.markdown("#### Margen Neto")
            margen_hist = extract_net_margin_series(ticker)
            if not margen_hist.empty:
                anios = [str(fecha.year) for fecha in margen_hist.index]
                valores = margen_hist.values.tolist()
                fig_bar = go.Figure(data=[go.Bar(
                    x=anios,
                    y=valores,
                    text=[f"{m:.1f}%" for m in valores],
                    textposition="auto",
                    textfont=dict(family="DM Mono", size=13),
                    marker_color=["#3fb950" if m > 0 else "#f85149" for m in valores],
                    marker_line_width=0,
                )])
                fig_bar.update_layout(height=280, yaxis_title="Margen Neto (%)", **PLOTLY_DARK)
                st.plotly_chart(fig_bar, use_container_width=True)
            elif isinstance(margen_neto, (int, float)):
                st.markdown(f"""
                <div class="fin-card">
                <span style="color:#8b949e; font-size:0.88rem;">Margen Neto (TTM ? Últimos 12 meses): </span>
                <span style="color:{'#3fb950' if margen_neto > 0 else '#f85149'}; font-size:1.1rem; font-family:'DM Mono',monospace; font-weight:600;">{margen_neto:.1f}%</span>
                <p style="color:#8b949e; font-size:0.82rem; margin-top:8px; line-height:1.6;">
                De cada $100 que vende la empresa, le quedan <b style="color:#c9d1d9;">${margen_neto:.1f}</b> como ganancia neta después de pagar costos, impuestos y deudas.
                {'Un margen positivo indica que la empresa es rentable.' if margen_neto > 0 else 'Un margen negativo indica que la empresa esta perdiendo dinero en este periodo.'}
                </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Sin datos de margen neto disponibles.")

            st.divider()

            # AGENDA + NOTICIAS
            col_ag, col_news = st.columns([1, 1], gap="large")
            with col_ag:
                st.markdown('<div class="section-label">Agenda Corporativa</div>', unsafe_allow_html=True)
                earnings = fh_earnings(ticker)
                fecha_balance = earnings[0].get("date", "No anunciada") if earnings else "No anunciada"
                st.markdown(f"""
                <div class="fin-card">
                    <div style="color:#8b949e; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; font-family:'DM Mono',monospace;">📅 Próximos Resultados</div>
                    <div style="color:#f0f6fc; font-size:1.1rem; font-family:'DM Mono',monospace; margin-top:8px;">{fecha_balance}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_news:
                st.markdown('<div class="section-label">Últimas Noticias</div>', unsafe_allow_html=True)
                noticias = fh_news(ticker)
                if noticias:
                    for n in noticias[:3]:
                        title = n.get("headline", "Sin título")
                        date  = str(n.get("datetime", ""))[:10]
                        url   = n.get("url", "#")
                        st.markdown(f"""
                        <div style="border-left:2px solid #21262d; padding-left:12px; margin-bottom:10px;">
                            <div style="color:#484f58; font-size:0.72rem; font-family:'DM Mono',monospace;">{date}</div>
                            <a href="{url}" target="_blank" style="color:#c9d1d9; font-size:0.85rem; text-decoration:none;">{title}</a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Sin noticias recientes.")

            st.divider()

            # IA ANÁLISIS
            st.markdown('<div class="section-label">Asistente IA — Análisis Educativo</div>', unsafe_allow_html=True)
            st.markdown("#### 🤖 Resumen con Inteligencia Artificial")
            st.markdown("""
            <div style="color:#8b949e; font-size:0.84rem; margin-bottom:12px;">
            El asistente interpreta los indicadores anteriores en términos educativos. <b style="color:#c9d1d9;">No es un consejo de inversión.</b>
            </div>
            """, unsafe_allow_html=True)

            if st.button("✨ Generar análisis con IA", use_container_width=False):
                with st.spinner("Analizando indicadores con IA..."):
                    resumen = analisis_ia_cached(
                        ticker=ticker,
                        nombre=nombre,
                        sector=sector,
                        precio=precio_actual,
                        per=safe_float(per),
                        beta=safe_float(beta),
                        market_cap_str=mc_str,
                        margen=safe_float(margen_neto),
                        max52=safe_float(max52),
                        min52=safe_float(min52),
                        rendimiento_periodo=safe_float(contexto_tecnico.get("rendimiento_periodo")),
                        volatilidad_anual=safe_float(contexto_tecnico.get("volatilidad_anual")),
                        media_50=safe_float(contexto_tecnico.get("media_50")),
                        media_200=safe_float(contexto_tecnico.get("media_200")),
                    )
                st.markdown(f"""
                <div class="ai-card">
                    <div style="color:#58a6ff; font-size:0.72rem; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:10px;">🤖 Análisis IA · {ticker}</div>
                    <div style="color:#c9d1d9; font-size:0.9rem; line-height:1.8; white-space:pre-wrap;">{resumen}</div>
                </div>
                """, unsafe_allow_html=True)

# =====================================================================
# TAB 4: SIMULADOR DE PORTAFOLIO
# =====================================================================
with solapa_simulador:
    st.markdown('<div class="section-label">Backtesting</div>', unsafe_allow_html=True)
    st.markdown("## 🕰️ Simulador Histórico de Portafolio")
    st.markdown('<p style="color:#8b949e;">Armá tu cartera con pesos personalizados y compará su rendimiento histórico contra SPY.</p>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:rgba(110,118,129,0.07); border:1px solid rgba(110,118,129,0.2); border-radius:8px; padding:12px 16px; margin-bottom:16px; font-size:0.84rem; color:#8b949e;">
    💡 <b style="color:#c9d1d9;">¿Por qué comparar contra SPY?</b> SPY replica el S&P 500, el índice más importante del mundo. 
    Es la alternativa "pasiva" de cualquier inversor: si tu cartera no le gana al SPY en el largo plazo, quizás conviene invertir directamente en el ETF. 
    Por eso es el <b style="color:#c9d1d9;">benchmark estándar de la industria</b>.
    </div>
    """, unsafe_allow_html=True)

    col_sim1, col_sim2 = st.columns([1, 1], gap="large")
    with col_sim1:
        capital_inicial = st.number_input("💰 Capital Inicial (USD)", min_value=100, value=10000, step=500)
        periodo = st.selectbox("📅 Período de simulación", ["1y", "2y", "3y", "5y"], index=2)
    with col_sim2:
        st.markdown("""
        <div style="background:rgba(31,111,235,0.07); border:1px solid rgba(88,166,255,0.15); border-radius:10px; padding:14px 18px; font-size:0.84rem; color:#8b949e; line-height:1.7;">
        <b style="color:#c9d1d9;">¿Cómo funciona?</b><br>
        Asignale un peso (%) a cada activo. Los pesos deben sumar exactamente <b style="color:#58a6ff;">100%</b>.
        El simulador calcula la evolución histórica y la compara contra <b style="color:#8b949e;">SPY</b>.
        </div>
        """, unsafe_allow_html=True)

    periodo_dias = {"1y": 365, "2y": 730, "3y": 1095, "5y": 1825}

    st.markdown("#### 📋 Composición del Portafolio")
    df_default = pd.DataFrame({"Ticker": ["GOOG", "AMZN", "NVDA"], "Peso (%)": [35, 35, 30]})
    df_cartera = st.data_editor(
        df_default, num_rows="dynamic", use_container_width=True,
        column_config={
            "Ticker":   st.column_config.TextColumn("Ticker", max_chars=10),
            "Peso (%)": st.column_config.NumberColumn("Peso (%)", min_value=0, max_value=100, step=1, format="%d%%")
        },
        hide_index=True, key="tabla_cartera"
    )

    total_pesos = df_cartera["Peso (%)"].sum()
    col_val1, _ = st.columns([1, 3])
    with col_val1:
        if total_pesos == 100:
            st.markdown('<div class="badge-verde" style="padding:6px 16px;">✓ Pesos: 100%</div>', unsafe_allow_html=True)
        elif total_pesos < 100:
            st.markdown(f'<div class="badge-azul" style="padding:6px 16px;">⚠ Faltan {100-total_pesos:.0f}%</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="badge-rojo" style="padding:6px 16px;">✗ Exceso {total_pesos-100:.0f}%</div>', unsafe_allow_html=True)

    cartera_preview = df_cartera.copy()
    cartera_preview["Ticker"] = cartera_preview["Ticker"].fillna("").astype(str).str.upper().str.strip()
    cartera_preview = cartera_preview[cartera_preview["Ticker"].str.len() > 0].drop_duplicates("Ticker")
    tickers_preview = cartera_preview["Ticker"].tolist()
    if tickers_preview:
        st.markdown('<div class="section-label">Precio actual</div>', unsafe_allow_html=True)
        cols_precio = st.columns(min(len(tickers_preview), 4))
        for idx, ticker_preview in enumerate(tickers_preview[:4]):
            quote_preview = fh_quote(ticker_preview)
            precio_preview = current_price_from_quote(quote_preview)
            delta_preview = price_change_pct(quote_preview)
            cols_precio[idx % len(cols_precio)].metric(
                ticker_preview,
                f"${precio_preview:,.2f}" if isinstance(precio_preview, (int, float)) else "N/A",
                delta=f"{delta_preview:+.2f}% hoy" if isinstance(delta_preview, (int, float)) else None,
            )
        if len(tickers_preview) > 4:
            st.caption("Se muestran las primeras 4 cotizaciones para mantener la vista compacta.")

    correr = st.button("▶️ Correr Simulación", disabled=(total_pesos != 100))

    if correr and total_pesos == 100:
        df_cartera["Ticker"] = df_cartera["Ticker"].str.upper().str.strip()
        df_cartera = df_cartera[df_cartera["Ticker"].str.len() > 0].drop_duplicates("Ticker")
        lista_tickers = df_cartera["Ticker"].tolist()
        pesos = (df_cartera["Peso (%)"] / 100).tolist()
        days  = periodo_dias[periodo]

        with st.spinner("Calculando rendimientos historicos..."):
            resultados, error = portfolio_backtest(lista_tickers, pesos, capital_inicial, periodo)

        if error:
            st.error(error)
        else:
            tickers_ok = resultados["tickers_ok"]
            pesos_ok = resultados["pesos_ok"]
            ret_acum = resultados["ret_acum"]
            valor_portafolio = resultados["valor_portafolio"]
            valor_spy = resultados["valor_spy"]

            if resultados["tickers_faltantes"]:
                st.warning(f"Tickers no encontrados: {', '.join(resultados['tickers_faltantes'])}")

            st.divider()
            st.markdown('<div class="section-label">Resultados del Backtesting</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Capital Inicial", f"${capital_inicial:,.0f}")
            c2.metric("Capital Final", f"${resultados['capital_final']:,.0f}", delta=f"{resultados['rendimiento_total']:+.1f}%")
            c3.metric("SPY Final", f"${resultados['capital_spy_final']:,.0f}", delta=f"{resultados['rendimiento_spy']:+.1f}%")
            c4.metric("Alpha vs SPY", f"{resultados['alpha']:+.1f}%",
                      delta="Superaste el indice" if resultados['alpha'] > 0 else "Bajo el indice",
                      delta_color="normal" if resultados['alpha'] > 0 else "inverse")
            c5.metric("Max Drawdown", f"{resultados['drawdown']:.1f}%")

            fig_sim = go.Figure()
            fig_sim.add_trace(go.Scatter(
                x=valor_portafolio.index, y=valor_portafolio.values,
                mode='lines', name='Mi Portafolio',
                line=dict(color='#58a6ff', width=2.5),
                fill='tozeroy', fillcolor='rgba(88,166,255,0.05)'
            ))
            fig_sim.add_trace(go.Scatter(
                x=valor_spy.index, y=valor_spy.values,
                mode='lines', name='SPY (Benchmark)',
                line=dict(color='#8b949e', width=1.5, dash='dot')
            ))
            fig_sim.add_hline(y=capital_inicial, line_dash="dash", line_color="#30363d",
                annotation_text="Capital inicial", annotation_font_color="#484f58")
            fig_sim.update_layout(
                height=460, yaxis_title="Valor (USD)", xaxis_title="Fecha",
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b949e')),
                **PLOTLY_DARK
            )
            st.plotly_chart(fig_sim, use_container_width=True)

            st.markdown("#### Contribucion Individual por Activo")
            filas = []
            for t, p in zip(tickers_ok, pesos_ok):
                serie = ret_acum[t].dropna() if t in ret_acum.columns else pd.Series(dtype="float64")
                r_ind = (serie.iloc[-1] - 1) * 100 if not serie.empty else 0
                contrib = r_ind * p
                filas.append({"Ticker": t, "Peso": f"{p*100:.0f}%",
                              "Rendimiento": f"{r_ind:+.1f}%",
                              "Contribucion al Portafolio": f"{contrib:+.1f}%"})
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

# =====================================================================
# TAB 5: FIN DEL RECORRIDO
# =====================================================================
with solapa_cierre:
    st.markdown('<div class="section-label">Próximos Pasos</div>', unsafe_allow_html=True)
    st.markdown("## 🎓 Fin del Recorrido")
    st.markdown('<p style="color:#8b949e;">Completaste el recorrido educativo. Esto es solo el comienzo.</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown("""
    <div class="fin-card" style="border-color:rgba(210,183,96,0.3); background:rgba(210,183,96,0.04); margin-bottom:24px;">
        <div style="color:#d2b760; font-size:0.72rem; font-weight:600; letter-spacing:0.14em; text-transform:uppercase; font-family:'DM Mono',monospace; margin-bottom:10px;">⚠️ Antes de invertir, recordá siempre</div>
        <div style="color:#c9d1d9; font-size:0.92rem; line-height:1.9;">
        ① <b>Nunca inviertas dinero que no podés permitirte perder.</b><br>
        ② Los rendimientos pasados no garantizan rendimientos futuros.<br>
        ③ El análisis fundamental y técnico son herramientas, no bolas de cristal.<br>
        ④ La diversificación reduce el riesgo, pero no lo elimina.<br>
        ⑤ Consultá siempre con un asesor financiero certificado antes de tomar decisiones importantes.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown("""
        <div class="fin-card">
            <div class="section-label">Para seguir aprendiendo</div>
            <h4 style="color:#f0f6fc; margin:0 0 14px;">📺 Canales de YouTube recomendados</h4>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#58a6ff; font-weight:600; font-size:0.88rem;">Joven Inversor</div>
                    <div style="color:#c9d1d9; font-size:0.82rem; margin-top:3px;">Inversiones en español desde cero. Muy didáctico para principiantes.</div>
                </div>
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#58a6ff; font-weight:600; font-size:0.88rem;">InverArg</div>
                    <div style="color:#c9d1d9; font-size:0.82rem; margin-top:3px;">Educación financiera e inversiones con foco en el mercado argentino.</div>
                </div>
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#58a6ff; font-weight:600; font-size:0.88rem;">Clave Bursátil</div>
                    <div style="color:#c9d1d9; font-size:0.82rem; margin-top:3px;">Análisis bursátil en español, técnico y fundamental.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="fin-card">
            <div class="section-label">Libros fundamentales</div>
            <h4 style="color:#f0f6fc; margin:0 0 14px;">📚 Lecturas recomendadas</h4>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#c9d1d9; font-size:0.88rem; font-weight:600;">El Inversor Inteligente</div>
                    <div style="color:#8b949e; font-size:0.82rem;">Benjamin Graham — La biblia del value investing. Atemporal.</div>
                </div>
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#c9d1d9; font-size:0.88rem; font-weight:600;">Un Paso por Delante de Wall Street</div>
                    <div style="color:#8b949e; font-size:0.82rem;">Peter Lynch — Cómo encontrar empresas ganadoras antes que los analistas.</div>
                </div>
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#c9d1d9; font-size:0.88rem; font-weight:600;">The Psychology of Money</div>
                    <div style="color:#8b949e; font-size:0.82rem;">Morgan Housel — El lado emocional del dinero. Muy accesible.</div>
                </div>
                <div style="border-left:3px solid #1f6feb; padding-left:14px;">
                    <div style="color:#c9d1d9; font-size:0.88rem; font-weight:600;">El Hombre más Rico de Babilonia</div>
                    <div style="color:#8b949e; font-size:0.82rem;">George S. Clason — Principios básicos de ahorro e inversión, muy fácil de leer.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.markdown("""
        <div class="fin-card">
            <div class="section-label">Mensaje final</div>
            <h4 style="color:#f0f6fc; margin:0 0 14px;">🧭 El camino es largo — y eso es bueno</h4>
            <p style="color:#c9d1d9; font-size:0.9rem; line-height:1.8; margin:0 0 14px;">
            Aprender a invertir es un proceso que lleva años. Los mejores inversores del mundo siguen estudiando, cometiendo errores y ajustando sus estrategias.
            </p>
            <p style="color:#c9d1d9; font-size:0.9rem; line-height:1.8; margin:0 0 14px;">
            Lo más importante que aprendiste en esta plataforma no son las fórmulas ni los indicadores — es que <b style="color:#f0f6fc;">el mercado es complejo, requiere humildad y paciencia</b>, y que tomar decisiones sin información o en base a emociones es la receta más segura para perder dinero.
            </p>
            <p style="color:#c9d1d9; font-size:0.9rem; line-height:1.8; margin:0;">
            Seguí estudiando. Leé, escuchá podcasts, practicá con simuladores antes de poner dinero real. Y cuando llegue el momento, <b style="color:#f0f6fc;">empezá con poco, diversificá y pensá en el largo plazo</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

# =====================================================================
# HIDE STREAMLIT BRANDING
# =====================================================================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.viewerBadge_container__1QSob {display: none !important;}
</style>
""", unsafe_allow_html=True)