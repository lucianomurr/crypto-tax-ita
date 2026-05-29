"""Dashboard Streamlit – Dichiarazione Crypto Italia (Quadri RT e RW) – multi-anno."""
import io
import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from config import EXCHANGE_RATES_CACHE, TAX_YEAR, get_tax_params
from modules.csv_loader import load_coinbase_csv_from_buffer
from modules.exchange_rates import get_ecb_rates, refresh_ecb_rates
from modules.price_fetcher import fetch_prices_for_rw, set_api_key, TICKER_TO_ID
from modules.rw_report import compute_rw_data
from modules.rt_report import compute_rt_data
from modules.excel_report import generate_rw_excel

# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Tax IT",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    .warn-box {
        background: #422006; border-left: 4px solid #f97316;
        padding: 12px 16px; border-radius: 6px; font-size: 0.88rem;
    }
    </style>""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🪙 Crypto Tax IT")
    st.divider()

    uploaded_file = st.file_uploader(
        "📂 Carica CSV Coinbase",
        type=["csv"],
        help="Coinbase → Menu → Strumenti → Rapporti → Cronologia transazioni",
    )

    st.divider()

    # Anno d'imposta — popolato dagli anni disponibili nel CSV
    available_years = st.session_state.get("available_years", [TAX_YEAR])
    selected_year = st.selectbox(
        "📅 Anno d'imposta",
        options=available_years,
        index=0,
        help="Seleziona l'anno per cui calcolare RT e RW",
    )
    params = get_tax_params(selected_year)
    franchigia_str = f"€ {params['exemption']:,.0f}" if params['exemption'] else "abolita"
    ivaca_str = "sì" if params['ivaca_applies'] else "no"
    st.caption(
        f"Aliquota: **{params['tax_rate']*100:.0f}%** · "
        f"Franchigia: **{franchigia_str}** · "
        f"IVACA: **{ivaca_str}**"
    )

    st.divider()
    st.subheader("Prezzi storici (CoinGecko)")
    _env_key = os.getenv("COINGECKO_API_KEY", "")
    cg_key = st.text_input(
        "API Key (opzionale)",
        value=_env_key,
        type="password",
        placeholder="CG-xxxxxxxxxxxxxxxxxxxx",
        help="Caricata da .env. Demo key gratuita su coingecko.com → My API keys.",
    )
    set_api_key(cg_key or None)
    if _env_key:
        st.caption("🔑 Key caricata da `.env`")
    price_cache_key = f"market_prices_{selected_year}"
    prices_loaded = price_cache_key in st.session_state
    n_with_prices = 0
    if prices_loaded:
        mp = st.session_state[price_cache_key]
        n_with_prices = sum(1 for v in mp.values() if v.get("end") is not None)
        st.success(f"{n_with_prices} asset con prezzo reale")
    else:
        st.info("Prezzi al 01/01 e 31/12 non ancora scaricati")
    fetch_prices_btn = st.button(
        "Scarica prezzi storici", use_container_width=True,
        help=f"Recupera prezzi al 01/01/{selected_year} e 31/12/{selected_year} da CoinGecko"
    )

    st.divider()
    st.subheader("Tassi BCE EUR/USD")
    cache_exists = os.path.exists(EXCHANGE_RATES_CACHE)
    if cache_exists:
        import datetime
        dt = datetime.datetime.fromtimestamp(os.path.getmtime(EXCHANGE_RATES_CACHE)).strftime("%d/%m/%Y")
        st.success(f"Cache presente ({dt})")
    else:
        st.warning("Cache non presente")

    col_a, col_b = st.columns(2)
    with col_a:
        fetch_btn = st.button("Scarica tassi", use_container_width=True)
    with col_b:
        refresh_btn = st.button("Aggiorna", use_container_width=True, type="secondary")

    st.divider()
    st.caption("⚠️ Strumento puramente informativo. Verifica con un commercialista.")

# ──────────────────────────────────────────────────────────────────────────────
# TASSI BCE
# ──────────────────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
os.makedirs("output", exist_ok=True)

if fetch_btn or refresh_btn:
    with st.spinner("Download tassi BCE in corso..."):
        try:
            rates = refresh_ecb_rates(EXCHANGE_RATES_CACHE) if refresh_btn else get_ecb_rates(EXCHANGE_RATES_CACHE)
            st.session_state["rates"] = rates
            st.sidebar.success(f"{len(rates)} tassi scaricati")
        except Exception as e:
            st.sidebar.error(f"Errore download tassi: {e}")

if "rates" not in st.session_state and os.path.exists(EXCHANGE_RATES_CACHE):
    try:
        st.session_state["rates"] = get_ecb_rates(EXCHANGE_RATES_CACHE)
    except Exception:
        pass

rates = st.session_state.get("rates", {})

# ── Fetch prezzi CoinGecko ────────────────────────────────────────────────────
if fetch_prices_btn and "df" in st.session_state:
    tickers = [
        t for t in st.session_state["df"]["asset"].unique()
        if t != "EUR" and t in TICKER_TO_ID
    ]
    progress_bar = st.sidebar.progress(0, text="Scaricamento prezzi...")
    fetched = {}

    def _progress(ticker, i, total):
        progress_bar.progress((i + 1) / total, text=f"CoinGecko: {ticker} ({i+1}/{total})")

    fetched = fetch_prices_for_rw(tickers, selected_year, progress_callback=_progress)
    st.session_state[price_cache_key] = fetched
    progress_bar.empty()
    st.sidebar.success(f"Prezzi scaricati per {len(fetched)} asset")
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# HOMEPAGE (nessun file caricato)
# ──────────────────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.title("🪙 Dichiarazione Crypto – Italia")
    st.info(
        "**Come iniziare:**\n\n"
        "1. Scarica il tuo CSV da **Coinbase → Menu → Strumenti → Rapporti**.\n"
        "2. Carica il file CSV dalla sidebar.\n"
        "3. Seleziona l'**anno d'imposta** — l'app rileva automaticamente gli anni disponibili.\n"
        "4. Clicca **Scarica tassi** se il tuo CSV è in USD (non necessario per CSV europei in EUR).\n\n"
        "Saranno calcolati automaticamente i dati per i **Quadri RT e RW** del Modello Redditi PF."
    )
    with st.expander("📖 Parametri fiscali per anno"):
        rows = []
        for yr in range(2020, 2027):
            p = get_tax_params(yr)
            rows.append({
                "Anno": yr,
                "Aliquota": f"{p['tax_rate']*100:.0f}%",
                "Franchigia": f"€ {p['exemption']:,.0f}" if p['exemption'] else "abolita",
                "IVACA": f"{p['ivaca_rate']*100:.1f}%" if p['ivaca_applies'] else "non prevista",
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# CARICAMENTO CSV
# ──────────────────────────────────────────────────────────────────────────────
fname = uploaded_file.name
if st.session_state.get("uploaded_filename") != fname:
    with st.spinner("Caricamento CSV..."):
        try:
            df = load_coinbase_csv_from_buffer(uploaded_file)
        except Exception as e:
            st.error(f"Errore nel caricamento CSV: {e}")
            st.stop()
    st.session_state["df"] = df
    st.session_state["uploaded_filename"] = fname
    # Rileva anni disponibili e aggiorna sidebar (forza re-render)
    years = sorted(df["date"].apply(lambda d: d.year).unique(), reverse=True)
    st.session_state["available_years"] = years
    st.rerun()

df = st.session_state["df"]

# ──────────────────────────────────────────────────────────────────────────────
# CALCOLI per l'anno selezionato
# ──────────────────────────────────────────────────────────────────────────────
market_prices = st.session_state.get(price_cache_key)

with st.spinner(f"Calcolo per l'anno {selected_year}..."):
    try:
        rw_df = compute_rw_data(df, rates, tax_year=selected_year, market_prices=market_prices)
    except Exception as e:
        st.error(f"Errore nel calcolo Quadro RW: {e}")
        st.stop()
    try:
        rt = compute_rt_data(df, rates, tax_year=selected_year)
    except Exception as e:
        st.error(f"Errore nel calcolo Quadro RT: {e}")
        st.stop()

rt_df = rt["disposals"]
rt_summary = rt.get("summary", {})
rt_errors = rt.get("errors", [])
balances = rt.get("balances", {})

# ──────────────────────────────────────────────────────────────────────────────
# KPI HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.title(f"🪙 Report Fiscale Crypto – Anno {selected_year}")

buys_df_all  = df[df["tx_type"] == "BUY"]
sells_df_all = df[df["tx_type"].isin(["SELL", "CONVERT"])]
_yr = lambda d: d.year == selected_year

buys_all   = buys_df_all["total_orig"].sum()
buys_year  = buys_df_all[buys_df_all["date"].apply(_yr)]["total_orig"].sum()
sells_all  = sells_df_all["subtotal_orig"].sum()
sells_year = sells_df_all[sells_df_all["date"].apply(_yr)]["subtotal_orig"].sum()
diff_all   = sells_all - buys_all
diff_year  = sells_year - buys_year

c1, c2, c3, c4 = st.columns(4)
c1.metric("Acquistato (storico)", f"€ {buys_all:,.2f}",
          help="Totale pagato in BUY su tutta la cronologia, incluse fee")
c2.metric("Venduto (storico)",    f"€ {sells_all:,.2f}",
          help="Totale incassato in SELL/CONVERT su tutta la cronologia, al netto delle fee")
c3.metric("Differenza storica",   f"€ {diff_all:,.2f}",
          delta=f"{'▲' if diff_all >= 0 else '▼'} {'profitto' if diff_all >= 0 else 'perdita'} netto realizzato",
          delta_color="normal" if diff_all >= 0 else "inverse")
c4.metric(f"Imposta RT ({selected_year})", f"€ {rt_summary.get('Imposta_Dovuta_EUR', 0):,.2f}")

# Avvisi franchigia
if rt_summary.get("Note_Franchigia"):
    st.success(f"✅ {rt_summary['Note_Franchigia']}")

# Avvisi elaborazione
if rt_errors:
    with st.expander(f"⚠️ {len(rt_errors)} avvisi di elaborazione", expanded=False):
        for e in rt_errors:
            st.warning(e)

unclassified = df[df["tx_type"] == "OTHER"]
if not unclassified.empty:
    st.warning(
        f"{len(unclassified)} transazioni non classificate (tipo 'OTHER'). "
        "Potrebbero richiedere revisione manuale."
    )

# ──────────────────────────────────────────────────────────────────────────────
# TAB
# ──────────────────────────────────────────────────────────────────────────────
tab_ov, tab_compila, tab_rw, tab_rt, tab_lifo, tab_tx = st.tabs(
    ["📊 Overview", "📝 Compila Dichiarazione", "🏦 Quadro RW", "📈 Quadro RT", "🔢 Dettaglio LIFO", "📋 Transazioni"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_ov:
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader(f"Portfolio al 31/12/{selected_year}")
        if not rw_df.empty and rw_df["Valore_Finale_EUR"].sum() > 0:
            fig_pie = px.pie(
                rw_df[rw_df["Valore_Finale_EUR"] > 0],
                names="Asset", values="Valore_Finale_EUR",
                hole=0.4, color_discrete_sequence=px.colors.qualitative.Vivid,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(showlegend=True, margin=dict(t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nessun asset in portafoglio al 31/12.")

    with col_r:
        st.subheader("Riepilogo fiscale")
        ivaca_tot = rw_df["IVACA_Dovuta_EUR"].sum() if not rw_df.empty else 0
        plus_tot = rt_summary.get("Totale_Plusvalenze_EUR", 0)
        minus_tot = rt_summary.get("Totale_Minusvalenze_EUR", 0)
        imposta = rt_summary.get("Imposta_Dovuta_EUR", 0)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Plusvalenze", x=["Quadro RT"], y=[plus_tot], marker_color="#22c55e"))
        fig_bar.add_trace(go.Bar(name="Minusvalenze", x=["Quadro RT"], y=[-minus_tot], marker_color="#ef4444"))
        fig_bar.add_trace(go.Bar(name="Imposta", x=["Quadro RT"], y=[imposta], marker_color="#f59e0b"))
        fig_bar.add_trace(go.Bar(name="IVACA", x=["Quadro RW"], y=[ivaca_tot], marker_color="#6366f1"))
        fig_bar.update_layout(barmode="group", margin=dict(t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader(f"Volume transazioni {selected_year}")
    df_year = df[df["date"].apply(lambda d: d.year == selected_year)].copy()
    if not df_year.empty:
        df_year["mese"] = pd.to_datetime(df_year["date"]).dt.to_period("M").astype(str)
        monthly = df_year.groupby(["mese", "tx_type"]).size().reset_index(name="count")
        fig_month = px.bar(
            monthly, x="mese", y="count", color="tx_type",
            labels={"mese": "Mese", "count": "N° transazioni", "tx_type": "Tipo"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_month.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info(f"Nessuna transazione nell'anno {selected_year}.")

    # ── SEZIONE ACQUISTI ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("💸 Totale acquisti crypto")

    buys_df = df[df["tx_type"] == "BUY"].copy()
    buys_df["anno"] = buys_df["date"].apply(lambda d: d.year)

    if buys_df.empty:
        st.info("Nessun acquisto trovato nella cronologia.")
    else:
        # Metrica riepilogativa
        ma1, ma2, ma3 = st.columns(3)
        ma1.metric("Totale storico acquisti", f"€ {buys_df['total_orig'].sum():,.2f}")
        ma2.metric(f"Acquisti {selected_year}", f"€ {buys_df[buys_df['anno'] == selected_year]['total_orig'].sum():,.2f}")
        ma3.metric("N° operazioni acquisto", f"{len(buys_df):,}")

        col_buy_l, col_buy_r = st.columns(2)

        with col_buy_l:
            # Spesa per anno
            by_year = buys_df.groupby("anno")["total_orig"].sum().reset_index()
            by_year.columns = ["Anno", "Totale_EUR"]
            fig_yr = px.bar(
                by_year, x="Anno", y="Totale_EUR",
                title="Spesa per anno",
                labels={"Totale_EUR": "€", "Anno": ""},
                color="Anno",
                color_discrete_sequence=px.colors.qualitative.Vivid,
            )
            fig_yr.update_layout(showlegend=False, margin=dict(t=30, b=10))
            st.plotly_chart(fig_yr, use_container_width=True)

        with col_buy_r:
            # Spesa per asset (top 10)
            by_asset = buys_df.groupby("asset")["total_orig"].sum().reset_index()
            by_asset.columns = ["Asset", "Totale_EUR"]
            by_asset = by_asset.sort_values("Totale_EUR", ascending=False).head(10)
            fig_asset_buy = px.bar(
                by_asset, x="Asset", y="Totale_EUR",
                title="Spesa per asset (top 10)",
                labels={"Totale_EUR": "€", "Asset": ""},
                color="Asset",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_asset_buy.update_layout(showlegend=False, margin=dict(t=30, b=10))
            st.plotly_chart(fig_asset_buy, use_container_width=True)

        # Tabella dettagliata per asset con valore attuale e P&L non realizzato
        st.subheader("Costo medio di acquisto vs valore attuale")
        summary_rows = []
        for asset, grp in buys_df.groupby("asset"):
            totale_speso = grp["total_orig"].sum()
            qty_acquistata = grp["quantity"].sum()
            costo_medio = totale_speso / qty_acquistata if qty_acquistata > 0 else 0

            # Valore attuale dal Quadro RW
            rw_row = rw_df[rw_df["Asset"] == asset] if not rw_df.empty else pd.DataFrame()
            valore_attuale = float(rw_row["Valore_Finale_EUR"].iloc[0]) if not rw_row.empty else 0.0
            qty_attuale = float(rw_row["Quantita_31dic"].iloc[0]) if not rw_row.empty else 0.0

            pl = valore_attuale - (costo_medio * qty_attuale) if qty_attuale > 0 else None

            summary_rows.append({
                "Asset": asset,
                "Qty acquistata (storico)": round(qty_acquistata, 6),
                "Totale speso (€)": round(totale_speso, 2),
                "Costo medio unitario (€)": round(costo_medio, 4),
                f"Qty al 31/12/{selected_year}": round(qty_attuale, 6),
                f"Valore al 31/12/{selected_year} (€)": round(valore_attuale, 2),
                "P&L non realizzato (€)": round(pl, 2) if pl is not None else "n/d",
            })

        summary_tbl = pd.DataFrame(summary_rows).sort_values("Totale speso (€)", ascending=False)
        st.dataframe(summary_tbl, hide_index=True, use_container_width=True)
        st.caption(
            "P&L non realizzato = valore al 31/12 – (costo medio × qty attuale). "
            "Non ha rilevanza fiscale diretta, è puramente indicativo."
        )

    # ── SEZIONE VENDITE ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("💰 Totale vendite e differenza netta")

    sells_df = df[df["tx_type"].isin(["SELL", "CONVERT"])].copy()
    sells_df["anno"] = sells_df["date"].apply(lambda d: d.year)
    buys_df  = df[df["tx_type"] == "BUY"].copy()
    buys_df["anno"]  = buys_df["date"].apply(lambda d: d.year)

    if sells_df.empty:
        st.info("Nessuna vendita o conversione trovata nella cronologia.")
    else:
        ms1, ms2, ms3, ms4 = st.columns(4)
        sells_yr = sells_df[sells_df["anno"] == selected_year]["subtotal_orig"].sum()
        buys_yr  = buys_df[buys_df["anno"] == selected_year]["total_orig"].sum()
        ms1.metric(f"Venduto ({selected_year})",    f"€ {sells_yr:,.2f}")
        ms2.metric(f"Acquistato ({selected_year})", f"€ {buys_yr:,.2f}")
        ms3.metric(f"Differenza ({selected_year})", f"€ {sells_yr - buys_yr:,.2f}",
                   delta_color="normal" if sells_yr >= buys_yr else "inverse")
        ms4.metric("N° operazioni vendita", f"{len(sells_df):,}")

        col_s_l, col_s_r = st.columns(2)

        with col_s_l:
            # Confronto acquistato vs venduto per anno
            by_yr_buy  = buys_df.groupby("anno")["total_orig"].sum().rename("Acquistato")
            by_yr_sell = sells_df.groupby("anno")["subtotal_orig"].sum().rename("Venduto")
            compare_yr = pd.concat([by_yr_buy, by_yr_sell], axis=1).fillna(0).reset_index()
            compare_yr.columns = ["Anno", "Acquistato", "Venduto"]
            compare_yr["Differenza"] = compare_yr["Venduto"] - compare_yr["Acquistato"]
            fig_cmp = go.Figure()
            fig_cmp.add_trace(go.Bar(name="Acquistato", x=compare_yr["Anno"].astype(str),
                                     y=compare_yr["Acquistato"], marker_color="#6366f1"))
            fig_cmp.add_trace(go.Bar(name="Venduto",    x=compare_yr["Anno"].astype(str),
                                     y=compare_yr["Venduto"],    marker_color="#22c55e"))
            fig_cmp.update_layout(barmode="group", title="Acquistato vs Venduto per anno",
                                  margin=dict(t=30, b=10))
            st.plotly_chart(fig_cmp, use_container_width=True)

        with col_s_r:
            # Differenza (venduto - acquistato) per anno
            fig_diff = px.bar(
                compare_yr, x="Anno", y="Differenza",
                title="Differenza netta per anno (venduto − acquistato)",
                labels={"Differenza": "€", "Anno": ""},
                color="Differenza",
                color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
                color_continuous_midpoint=0,
            )
            fig_diff.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
            fig_diff.update_layout(showlegend=False, margin=dict(t=30, b=10))
            st.plotly_chart(fig_diff, use_container_width=True)

        # Tabella per anno
        st.subheader("Riepilogo per anno")
        compare_yr["Anno"] = compare_yr["Anno"].astype(str)
        compare_yr["Acquistato"] = compare_yr["Acquistato"].map("€ {:,.2f}".format)
        compare_yr["Venduto"]    = compare_yr["Venduto"].map("€ {:,.2f}".format)
        compare_yr["Differenza"] = compare_yr["Differenza"].map("€ {:,.2f}".format)
        st.dataframe(compare_yr, hide_index=True, use_container_width=True)
        st.caption(
            "Acquistato = totale pagato (incluse fee). "
            "Venduto = totale incassato al netto delle fee (subtotal). "
            "La differenza è il P&L realizzato lordo, non equivale all'imponibile fiscale LIFO."
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – COMPILA DICHIARAZIONE
# ══════════════════════════════════════════════════════════════════════════════
with tab_compila:
    st.subheader(f"Guida alla compilazione – Anno {selected_year}")

    modello = st.radio(
        "Modello dichiarativo",
        ["Modello 730 (Riquadro W + T)", "Modello Redditi PF (Quadro RW + RT)"],
        horizontal=True,
        help="Usa il 730 se sei lavoratore dipendente/pensionato senza P.IVA. "
             "Usa Redditi PF negli altri casi.",
    )
    is_730 = modello.startswith("Modello 730")
    quadro_label = "W" if is_730 else "RW"
    quadro_rt_label = "T" if is_730 else "RT"

    # ── SEZIONE RIQUADRO W / QUADRO RW ──────────────────────────────────────
    st.markdown(f"### Riquadro {quadro_label} – Monitoraggio Fiscale")

    if rw_df.empty:
        st.warning("Nessun asset da dichiarare nel Riquadro W/RW per questo anno.")
    else:
        # Calcoli aggregati per il singolo rigo
        val_inizio_tot = rw_df["Valore_Iniziale_EUR"].sum()
        val_fine_tot   = rw_df["Valore_Finale_EUR"].sum()

        # Giorni di detenzione: dal primo ingresso all'exchange all'anno corrente
        first_tx_date = df["date"].min()
        import datetime as _dt
        start_of_year = _dt.date(selected_year, 1, 1)
        end_of_year   = _dt.date(selected_year, 12, 31)
        # Se il conto è attivo prima dell'anno → 365; altrimenti dal primo acquisto
        if first_tx_date < start_of_year:
            giorni_det = 365
        else:
            giorni_det = (end_of_year - first_tx_date).days + 1

        # IVACA sul totale
        ivaca_tot_calc = val_fine_tot * params["ivaca_rate"] * (giorni_det / 365) if params["ivaca_applies"] else 0.0
        ivaca_tot_dov  = round(ivaca_tot_calc, 2) if ivaca_tot_calc >= params["ivaca_min"] else 0.0

        ql = quadro_label  # alias breve

        # ── Opzione 1: singolo rigo ───────────────────────────────────────
        st.markdown(
            "#### Opzione 1 — Compilazione semplificata (consigliata)\n"
            f"**Un solo rigo** per tutto il conto Coinbase "
            f"*(Circolare ADE n. 30/E del 27/10/2023, § 3.4)*"
        )
        st.info(
            "Il valore cumulativo di tutte le cripto-attività viene dichiarato in un unico rigo. "
            "Devi conservare il **prospetto analitico** (file Excel generato dall'app) "
            "con il dettaglio per singolo asset, da produrre in caso di verifica fiscale."
        )

        single_row = {
            f"{ql}1 – Codice titolo": "1",
            f"{ql}3 – Codice bene": "21",
            f"{ql}4 – Stato estero": "*(vuoto)*",
            f"{ql}5 – Quota possesso (%)": "100",
            f"{ql}6 – Criterio valore": "1",
            f"{ql}7 – Valore iniziale 01/01 (€)": f"{round(val_inizio_tot):,}",
            f"{ql}8 – Valore finale 31/12 (€)": f"{round(val_fine_tot):,}",
            f"{ql}10 – Giorni IC": str(giorni_det),
            f"{ql}14 – Codice quadro red.": "3",
            f"{ql}33 – IC calcolata (€)": f"{ivaca_tot_calc:,.2f}",
            f"{ql}34 – IC dovuta (€)": f"{ivaca_tot_dov:,.2f}",
        }
        st.dataframe(
            pd.DataFrame([single_row]).T.rename(columns={0: "Valore da inserire"}),
            use_container_width=True,
        )

        if ivaca_tot_dov > 0:
            st.markdown(
                f"**F24 – IVACA:** Codice tributo `1717` · Anno `{selected_year}` · Importo **€ {ivaca_tot_dov:,.2f}**  \n"
                "Scadenza saldo: **30 giugno**"
            )
        else:
            st.success(
                f"IVACA non dovuta: IC calcolata € {ivaca_tot_calc:,.2f} "
                f"(sotto la soglia minima di € {params['ivaca_min']:.0f})."
            )

        st.divider()

        # ── Opzione 2: un rigo per asset ─────────────────────────────────
        st.markdown(
            "#### Opzione 2 — Compilazione analitica\n"
            "Un rigo separato per ogni cripto-attività *(facoltativa, risposta ADE Videoconferenza 01/02/2024)*"
        )
        st.caption(
            "⚠️ I valori sono approssimati. "
            "Clicca 'Scarica prezzi storici' nella sidebar per i prezzi reali al 01/01 e 31/12."
        )

        rw_compila = []
        for _, row in rw_df[rw_df["Quantita_31dic"] > 0].iterrows():
            rw_compila.append({
                "Asset": row["Asset"],
                f"{ql}1 – Titolo": "1",
                f"{ql}3 – Codice bene": "21",
                f"{ql}4 – Stato estero": "*(vuoto)*",
                f"{ql}5 – Quota %": "100",
                f"{ql}6 – Criterio": "1",
                f"{ql}7 – Valore iniziale (€)": f"{row['Valore_Iniziale_EUR']:,.2f}",
                f"{ql}8 – Valore finale (€)": f"{row['Valore_Finale_EUR']:,.2f}",
                f"{ql}10 – Giorni IC": "365",
                f"{ql}33 – IC calcolata (€)": f"{row['IVACA_Calcolata_EUR']:,.2f}",
                f"{ql}34 – IC dovuta (€)": f"{row['IVACA_Dovuta_EUR']:,.2f}",
            })

        compila_df = pd.DataFrame(rw_compila).set_index("Asset")
        st.dataframe(compila_df, use_container_width=True)

        with st.expander("📋 Legenda campi"):
            st.markdown(f"""
| Campo | Valore | Significato |
|---|---|---|
| **{ql}1** | `1` | Proprietà diretta |
| **{ql}3** | `21` | Cripto-attività |
| **{ql}4** | *(vuoto)* | Le cripto non hanno localizzazione geografica (Circ. 30/E/2023) |
| **{ql}5** | `100` | Proprietà al 100% (altro se cointestate) |
| **{ql}6** | `1` | Valore di mercato |
| **{ql}7** | — | Valore portafoglio al 01/01 in € |
| **{ql}8** | — | Valore portafoglio al 31/12 in € (arrotondare all'euro) |
| **{ql}10** | — | Giorni di detenzione nell'anno |
| **{ql}14** | `3` | Compili Quadro RT (usa `4` se compili anche RL o RM) |
| **{ql}33** | — | IC = valore finale × 0,2% × giorni/365 |
| **{ql}34** | — | IC dovuta se ≥ € {params['ivaca_min']:.0f}, altrimenti 0 |
            """)

    # ── SEZIONE QUADRO RT / SEZIONE T ────────────────────────────────────────
    st.divider()
    st.markdown(f"### Quadro {quadro_rt_label} – Plusvalenze e Minusvalenze")

    if rt_df.empty:
        st.success(
            f"Nessuna vendita nell'anno {selected_year}: "
            f"il Quadro {quadro_rt_label} **non va compilato**."
        )
    else:
        s = rt_summary
        total_plus = s.get("Totale_Plusvalenze_EUR", 0)
        total_minus = s.get("Totale_Minusvalenze_EUR", 0)
        net = s.get("Reddito_Netto_EUR", 0)
        imposta = s.get("Imposta_Dovuta_EUR", 0)
        franchigia = s.get("Franchigia_EUR", 0)

        # Tabella riepilogativa compilazione RT
        st.markdown("**Valori da riportare nel modulo:**")

        if is_730:
            fields = {
                "T1 – Totale corrispettivi (ricavi vendite)": f"€ {total_plus + abs(total_minus):,.2f}",
                "T2 – Totale costi di acquisto (LIFO)": f"€ {total_minus:,.2f}",
                "T3 – Plusvalenze lorde": f"€ {total_plus:,.2f}",
                "T4 – Minusvalenze": f"€ {total_minus:,.2f}",
                "T5 – Reddito netto imponibile": f"€ {net:,.2f}",
                "T6 – Imposta sostitutiva dovuta (26%)": f"€ {imposta:,.2f}",
            }
        else:
            fields = {
                "RT23 – Totale corrispettivi (ricavi)": f"€ {sum(r['Ricavo_EUR'] for _, r in rt_df.iterrows()):,.2f}",
                "RT24 – Totale costi di acquisto (LIFO)": f"€ {sum(r['Costo_LIFO_EUR'] for _, r in rt_df.iterrows()):,.2f}",
                "RT25 – Plusvalenze": f"€ {total_plus:,.2f}",
                "RT26 – Minusvalenze": f"€ {total_minus:,.2f}",
                "RT27 – Reddito netto imponibile": f"€ {net:,.2f}",
                "RT29 – Imposta sostitutiva (26%)": f"€ {imposta:,.2f}",
            }

        rt_compila_df = pd.DataFrame(
            {"Campo": list(fields.keys()), "Valore da inserire": list(fields.values())}
        )
        st.dataframe(rt_compila_df, hide_index=True, use_container_width=True)

        if s.get("Note_Franchigia"):
            st.success(f"✅ {s['Note_Franchigia']} → RT29 / T6 = € 0,00")

        if imposta > 0:
            st.divider()
            st.markdown(f"#### Imposta da versare: **€ {imposta:,.2f}**")
            st.markdown(
                "Versa tramite **Modello F24** entro il **30 giugno** con:\n"
                f"- Codice tributo: **`1715`** (acconto) / **`1716`** (saldo)\n"
                f"- Anno di riferimento: **`{selected_year}`**\n"
                f"- Importo saldo: **€ {imposta:,.2f}**"
            )

        with st.expander("📋 Dettaglio operazioni per la compilazione"):
            detail_df = rt_df[["Data", "Asset", "Tipo_TX", "Quantita_Venduta",
                                "Ricavo_EUR", "Costo_LIFO_EUR", "PlusMinus_EUR", "Tipo"]].copy()
            detail_df["Ricavo_EUR"] = detail_df["Ricavo_EUR"].map("€ {:,.2f}".format)
            detail_df["Costo_LIFO_EUR"] = detail_df["Costo_LIFO_EUR"].map("€ {:,.2f}".format)
            detail_df["PlusMinus_EUR"] = detail_df["PlusMinus_EUR"].map("€ {:,.2f}".format)
            st.dataframe(detail_df, use_container_width=True)

    # ── DOWNLOAD SCHEDA COMPILAZIONE ─────────────────────────────────────────
    st.divider()
    st.markdown("### Scarica scheda compilazione")

    dc1, dc2 = st.columns(2)
    with dc1:
        buf_compila = io.BytesIO()
        with pd.ExcelWriter(buf_compila, engine="openpyxl") as writer:
            if not rw_df.empty:
                compila_df.to_excel(writer, sheet_name=f"Riquadro {quadro_label}", index=True)
            rt_compila_df.to_excel(writer, sheet_name=f"Quadro {quadro_rt_label}", index=False)
            if not rt_df.empty:
                rt_df.to_excel(writer, sheet_name="Dettaglio operazioni", index=False)
        buf_compila.seek(0)
        st.download_button(
            f"⬇️ Scheda Compilazione {selected_year}",
            data=buf_compila,
            file_name=f"scheda_compilazione_{quadro_label}_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with dc2:
        if not rw_df.empty:
            xlsx_rw_compila = generate_rw_excel(rw_df, df, tax_year=selected_year)
            st.download_button(
                f"⬇️ Report RW {selected_year} (formato standard)",
                data=xlsx_rw_compila,
                file_name=f"report_RW_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – QUADRO RW
# ══════════════════════════════════════════════════════════════════════════════
with tab_rw:
    st.subheader(f"Quadro RW – Monitoraggio Fiscale e IVACA ({selected_year})")

    if not params["ivaca_applies"]:
        st.info(f"L'IVACA non era prevista per l'anno {selected_year} (introdotta dal 2023).")

    if rw_df.empty:
        st.info("Nessun asset rilevato nel periodo.")
    else:
        cw1, cw2, cw3, cw4 = st.columns(4)
        cw1.metric("Valore portafoglio 01/01", f"€ {rw_df['Valore_Iniziale_EUR'].sum():,.2f}")
        cw2.metric("Valore portafoglio 31/12", f"€ {rw_df['Valore_Finale_EUR'].sum():,.2f}")
        cw3.metric("IVACA calcolata", f"€ {rw_df['IVACA_Calcolata_EUR'].sum():,.2f}")
        cw4.metric(
            f"IVACA dovuta (min € {params['ivaca_min']:.0f})" if params["ivaca_applies"] else "IVACA",
            f"€ {rw_df['IVACA_Dovuta_EUR'].sum():,.2f}",
        )

        st.divider()

        # Badge fonte prezzi
        n_cg = (rw_df["Fonte_Prezzo"] == "CoinGecko").sum() if "Fonte_Prezzo" in rw_df.columns else 0
        n_tot = len(rw_df[rw_df["Quantita_31dic"] > 0])
        if n_cg == n_tot:
            st.success(f"✅ Prezzi reali CoinGecko al 31/12/{selected_year} per tutti gli asset")
        elif n_cg > 0:
            st.warning(
                f"⚠️ {n_cg}/{n_tot} asset con prezzo CoinGecko reale. "
                f"I restanti usano l'ultima transazione disponibile."
            )
        else:
            st.warning(
                "⚠️ Prezzi approssimati (ultima transazione disponibile). "
                "Clicca **Scarica prezzi storici** nella sidebar per prezzi reali al 31/12."
            )

        display_rw = rw_df.copy()
        for col in ("Valore_Iniziale_EUR", "Valore_Finale_EUR", "IVACA_Calcolata_EUR", "IVACA_Dovuta_EUR"):
            display_rw[col] = display_rw[col].map("€ {:,.2f}".format)
        for col in ("Prezzo_01gen_EUR", "Prezzo_31dic_EUR"):
            if col in display_rw.columns:
                display_rw[col] = display_rw[col].map("€ {:,.4f}".format)
        st.dataframe(display_rw, use_container_width=True)

        if params["ivaca_applies"] and rw_df["IVACA_Dovuta_EUR"].apply(
            lambda x: float(str(x).replace("€","").replace(",","").strip() or 0) if isinstance(x, str) else x
        ).sum() > 0:
            fig_ivaca = px.bar(
                rw_df[rw_df["IVACA_Dovuta_EUR"] > 0],
                x="Asset", y="IVACA_Dovuta_EUR",
                title=f"IVACA dovuta per asset – {selected_year} (€)",
                color="Asset", color_discrete_sequence=px.colors.qualitative.Vivid,
            )
            st.plotly_chart(fig_ivaca, use_container_width=True)

        dl1, dl2 = st.columns(2)
        with dl1:
            csv_rw = rw_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"⬇️ Report RW {selected_year} (CSV)",
                data=csv_rw, file_name=f"report_RW_{selected_year}.csv", mime="text/csv",
                use_container_width=True,
            )
        with dl2:
            xlsx_rw = generate_rw_excel(rw_df, df, tax_year=selected_year)
            st.download_button(
                f"⬇️ Report RW {selected_year} (Excel – formato standard)",
                data=xlsx_rw,
                file_name=f"report_RW_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – QUADRO RT
# ══════════════════════════════════════════════════════════════════════════════
with tab_rt:
    st.subheader(f"Quadro RT – Plusvalenze e Minusvalenze ({selected_year})")

    if params["exemption"] > 0:
        st.info(
            f"Anno {selected_year}: franchigia **€ {params['exemption']:,.0f}**. "
            "Se il reddito netto è inferiore, l'imposta non è dovuta."
        )

    if rt_df.empty:
        st.success(
            f"Nessuna vendita o conversione rilevata nell'anno {selected_year}: "
            "il Quadro RT non è obbligatorio."
        )
    else:
        cr1, cr2, cr3, cr4 = st.columns(4)
        cr1.metric("Plusvalenze", f"€ {rt_summary['Totale_Plusvalenze_EUR']:,.2f}")
        cr2.metric("Minusvalenze", f"€ {rt_summary['Totale_Minusvalenze_EUR']:,.2f}")
        cr3.metric("Reddito netto", f"€ {rt_summary['Reddito_Netto_EUR']:,.2f}")
        cr4.metric(
            f"Imposta ({rt_summary['Aliquota']})",
            f"€ {rt_summary['Imposta_Dovuta_EUR']:,.2f}",
        )

        if rt_summary.get("Note_Franchigia"):
            st.success(f"✅ {rt_summary['Note_Franchigia']}")

        st.divider()

        rt_df_plot = rt_df.copy()
        rt_df_plot["Data"] = pd.to_datetime(rt_df_plot["Data"])
        fig_rt = px.bar(
            rt_df_plot, x="Data", y="PlusMinus_EUR", color="Asset",
            title=f"Plusvalenze/Minusvalenze per operazione – {selected_year}",
            labels={"PlusMinus_EUR": "€", "Data": "Data"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_rt.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        st.plotly_chart(fig_rt, use_container_width=True)

        display_rt = rt_df.copy()
        for col in ("Ricavo_EUR", "Costo_LIFO_EUR", "PlusMinus_EUR"):
            display_rt[col] = display_rt[col].map("€ {:,.2f}".format)
        st.dataframe(display_rt, use_container_width=True)

        csv_rt = rt_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            f"⬇️ Scarica Report RT {selected_year} (CSV)",
            data=csv_rt, file_name=f"report_RT_{selected_year}.csv", mime="text/csv",
        )

        st.divider()
        st.subheader("Riepilogo per asset")
        by_asset = rt_df.groupby("Asset")["PlusMinus_EUR"].sum().reset_index()
        by_asset["Tipo"] = by_asset["PlusMinus_EUR"].apply(
            lambda x: "Plusvalenza" if x >= 0 else "Minusvalenza"
        )
        fig_asset = px.bar(
            by_asset, x="Asset", y="PlusMinus_EUR", color="Tipo",
            color_discrete_map={"Plusvalenza": "#22c55e", "Minusvalenza": "#ef4444"},
            labels={"PlusMinus_EUR": "€"},
        )
        fig_asset.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        st.plotly_chart(fig_asset, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – DETTAGLIO LIFO
# ══════════════════════════════════════════════════════════════════════════════
with tab_lifo:
    st.subheader(f"Dettaglio calcolo LIFO – {selected_year}")

    if rt_df.empty:
        st.info("Nessuna vendita da dettagliare per questo anno.")
    else:
        st.markdown(
            "Il metodo **LIFO (Last In, First Out)** considera venduti per primi "
            "gli ultimi lotti acquistati."
        )
        if balances:
            st.subheader("Saldo inventario LIFO (fine elaborazione)")
            bal_df = pd.DataFrame(
                [{"Asset": k, "Quantità rimanente": round(v, 8)} for k, v in balances.items()]
            )
            st.dataframe(bal_df, use_container_width=True)

        st.divider()
        st.subheader("Dettaglio operazioni con costo di carico")
        st.dataframe(rt_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 – TUTTE LE TRANSAZIONI
# ══════════════════════════════════════════════════════════════════════════════
with tab_tx:
    st.subheader("Storico transazioni Coinbase")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_asset = st.multiselect("Filtra per asset", sorted(df["asset"].unique()), default=[])
    with fc2:
        filter_type = st.multiselect("Filtra per tipo", sorted(df["tx_type"].unique()), default=[])
    with fc3:
        all_years = sorted(df["date"].apply(lambda d: d.year).unique(), reverse=True)
        filter_year = st.multiselect("Anno", all_years, default=[selected_year])

    df_filtered = df.copy()
    if filter_asset:
        df_filtered = df_filtered[df_filtered["asset"].isin(filter_asset)]
    if filter_type:
        df_filtered = df_filtered[df_filtered["tx_type"].isin(filter_type)]
    if filter_year:
        df_filtered = df_filtered[df_filtered["date"].apply(lambda d: d.year).isin(filter_year)]

    st.caption(f"{len(df_filtered):,} transazioni visualizzate")
    st.dataframe(
        df_filtered[
            ["date", "tx_type", "asset", "quantity", "price_currency",
             "price_orig", "total_orig", "fees_orig", "notes"]
        ].rename(columns={
            "date": "Data", "tx_type": "Tipo", "asset": "Asset",
            "quantity": "Quantità", "price_currency": "Valuta",
            "price_orig": "Prezzo", "total_orig": "Totale",
            "fees_orig": "Fee", "notes": "Note",
        }),
        use_container_width=True,
    )

    # Download Excel completo (senza timestamp timezone-aware)
    df_excel = df[
        ["date", "tx_type", "asset", "quantity", "price_currency",
         "price_orig", "total_orig", "fees_orig", "notes"]
    ].copy()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_excel.to_excel(writer, sheet_name="Transazioni", index=False)
        if not rw_df.empty:
            rw_df.to_excel(writer, sheet_name=f"Quadro RW {selected_year}", index=False)
        if not rt_df.empty:
            rt_df.to_excel(writer, sheet_name=f"Quadro RT {selected_year}", index=False)
    buf.seek(0)
    st.download_button(
        f"⬇️ Scarica Report completo {selected_year} (Excel)",
        data=buf,
        file_name=f"crypto_tax_{selected_year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
