"""
Genera il PDF della scheda di compilazione per la dichiarazione fiscale crypto.
Dipendenza: fpdf2>=2.7.0
"""
import datetime

import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Palette colori
_BLUE_HDR  = (30, 58, 138)
_BLUE_SUB  = (67, 97, 180)
_ROW_ALT   = (245, 247, 252)
_GREEN_BG  = (220, 252, 231)
_AMBER_BG  = (254, 243, 199)
_GRAY_LINE = (200, 200, 200)

_PAGE_W = 180.0  # larghezza utile A4 (210 - 15 - 15)


class _PDF(FPDF):
    _year: int = 0

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(160, 160, 160)
        self.cell(
            0, 5,
            f"Crypto Tax IT - Dichiarazione {self._year}",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="R",
        )
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(160, 160, 160)
        self.cell(
            0, 5,
            f"Pag. {self.page_no()}  |  Strumento informativo - verificare con un professionista fiscale abilitato.",
            align="C",
        )
        self.set_text_color(0, 0, 0)


def _section(pdf: _PDF, title: str) -> None:
    pdf.set_fill_color(*_BLUE_HDR)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 9, f"  {title}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def _subsection(pdf: _PDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*_BLUE_SUB)
    pdf.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)


def _kv_table(pdf: _PDF, data: dict, w1: float = 120.0, w2: float = 60.0) -> None:
    """Tabella chiave/valore a due colonne."""
    for i, (k, v) in enumerate(data.items()):
        pdf.set_fill_color(*(_ROW_ALT if i % 2 == 0 else (255, 255, 255)))
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(w1, 7, str(k), border=1, fill=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(w2, 7, str(v), border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)


def _df_table(pdf: _PDF, df: pd.DataFrame, col_widths: list) -> None:
    """Tabella da DataFrame con header ripetuto su nuove pagine."""

    def _print_header():
        pdf.set_fill_color(*_BLUE_HDR)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        for col, w in zip(df.columns, col_widths):
            pdf.cell(w, 7, str(col), border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

    _print_header()

    for i, (_, row) in enumerate(df.iterrows()):
        if pdf.get_y() > pdf.h - pdf.b_margin - 14:
            pdf.add_page()
            _print_header()

        pdf.set_fill_color(*(_ROW_ALT if i % 2 == 0 else (255, 255, 255)))
        pdf.set_font("Helvetica", "", 8)
        for val, w in zip(row, col_widths):
            text = str(val) if val is not None else ""
            max_ch = max(1, int(w / 2.1))
            pdf.cell(w, 6, text[:max_ch], border=1, fill=True)
        pdf.ln()
    pdf.ln(3)


def _notice(pdf: _PDF, text: str, bg: tuple) -> None:
    pdf.set_fill_color(*bg)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 9, f"  {text}", fill=True, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)


def generate_compilation_pdf(
    selected_year: int,
    is_730: bool,
    rw_df: pd.DataFrame,
    rt_df: pd.DataFrame,
    rt_summary: dict,
    params: dict,
    first_tx_date: datetime.date,
) -> bytes:
    """
    Genera il PDF della scheda di compilazione 730 / Redditi PF.
    Ritorna i byte del PDF.
    """
    ql     = "W"  if is_730 else "RW"
    ql_rt  = "T"  if is_730 else "RT"
    modello = "730" if is_730 else "Redditi PF"
    today  = datetime.date.today()

    # Calcola valori RW
    val_inizio = rw_df["Valore_Iniziale_EUR"].sum() if not rw_df.empty else 0.0
    val_fine   = rw_df["Valore_Finale_EUR"].sum()   if not rw_df.empty else 0.0

    start_of_year = datetime.date(selected_year, 1, 1)
    end_of_year   = datetime.date(selected_year, 12, 31)
    if first_tx_date < start_of_year:
        giorni_det = 365
    else:
        giorni_det = (end_of_year - first_tx_date).days + 1

    ivaca_calc = val_fine * params["ivaca_rate"] * (giorni_det / 365) if params["ivaca_applies"] else 0.0
    ivaca_dov  = round(ivaca_calc, 2) if ivaca_calc >= params["ivaca_min"] else 0.0

    s = rt_summary
    total_plus  = s.get("Totale_Plusvalenze_EUR", 0)
    total_minus = s.get("Totale_Minusvalenze_EUR", 0)
    net         = s.get("Reddito_Netto_EUR", 0)
    imposta     = s.get("Imposta_Dovuta_EUR", 0)

    # ── Costruzione PDF ────────────────────────────────────────────────────────
    pdf = _PDF()
    pdf._year = selected_year
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    # Titolo
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(
        0, 14, f"Dichiarazione Crypto - Anno {selected_year}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C",
    )
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 7, f"Modello {modello}  |  Generato il {today.strftime('%d/%m/%Y')}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C",
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # ── Riepilogo ──────────────────────────────────────────────────────────────
    _section(pdf, "Riepilogo fiscale")
    riepilogo = {
        "Anno d'imposta": str(selected_year),
        "Modello dichiarativo": modello,
        f"Aliquota imposta sostitutiva": f"{params['tax_rate']*100:.0f}%",
        "Valore portafoglio al 01/01 (EUR)": f"{round(val_inizio):,}",
        "Valore portafoglio al 31/12 (EUR)": f"{round(val_fine):,}",
        "Plusvalenze (EUR)": f"{total_plus:,.2f}",
        "Minusvalenze (EUR)": f"{total_minus:,.2f}",
        "Reddito netto imponibile (EUR)": f"{net:,.2f}",
        f"Imposta sostitutiva {params['tax_rate']*100:.0f}% (EUR)": f"{imposta:,.2f}",
        "IVACA dovuta (EUR)": f"{ivaca_dov:,.2f}",
    }
    _kv_table(pdf, riepilogo)
    pdf.ln(3)

    # ── Sezione 1: Riquadro W / Quadro RW ─────────────────────────────────────
    _section(pdf, f"Riquadro {ql} - Monitoraggio Fiscale (IVACA)")

    if rw_df.empty:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 8, "Nessun asset da dichiarare per questo anno.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)
    else:
        # Opzione 1 – semplificata
        _subsection(pdf, f"Opzione 1 - Compilazione semplificata (un solo rigo - consigliata)")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            0, 5,
            f"Rif. Circolare ADE n. 30/E del 27/10/2023, paragrafo 3.4. "
            f"Conservare il prospetto analitico per asset (file Excel) in caso di verifica fiscale.",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        single_row = {
            f"{ql}1 - Codice titolo": "1",
            f"{ql}3 - Codice bene": "21",
            f"{ql}4 - Stato estero": "(vuoto - cripto-attivita')",
            f"{ql}5 - Quota possesso (%)": "100",
            f"{ql}6 - Criterio valore": "1",
            f"{ql}7 - Valore iniziale 01/01 (EUR)": f"{round(val_inizio):,}",
            f"{ql}8 - Valore finale 31/12 (EUR)": f"{round(val_fine):,}",
            f"{ql}10 - Giorni IC": str(giorni_det),
            f"{ql}14 - Codice quadro red.": "3",
            f"{ql}33 - IC calcolata (EUR)": f"{ivaca_calc:,.2f}",
            f"{ql}34 - IC dovuta (EUR)": f"{ivaca_dov:,.2f}",
        }
        _kv_table(pdf, single_row)

        if ivaca_dov > 0:
            _notice(
                pdf,
                f"F24 - IVACA: Codice tributo 1717 | Anno {selected_year} "
                f"| EUR {ivaca_dov:,.2f} | Scadenza: 30 giugno",
                _AMBER_BG,
            )
        else:
            _notice(
                pdf,
                f"IVACA non dovuta: EUR {ivaca_calc:,.2f} < soglia minima EUR {params['ivaca_min']:.0f}",
                _GREEN_BG,
            )

        # Opzione 2 – per asset
        _subsection(pdf, "Opzione 2 - Compilazione analitica (un rigo per asset)")
        rw_assets = rw_df[rw_df["Quantita_31dic"] > 0].copy()
        if not rw_assets.empty:
            rw_tbl = pd.DataFrame([
                {
                    "Asset":              row["Asset"],
                    f"{ql}7 Inizio":      f"{row['Valore_Iniziale_EUR']:,.2f}",
                    f"{ql}8 Fine":        f"{row['Valore_Finale_EUR']:,.2f}",
                    f"{ql}10 Gg IC":      "365",
                    f"{ql}33 IC calc.":   f"{row['IVACA_Calcolata_EUR']:,.2f}",
                    f"{ql}34 IC dov.":    f"{row['IVACA_Dovuta_EUR']:,.2f}",
                }
                for _, row in rw_assets.iterrows()
            ])
            n_extra = len(rw_tbl.columns) - 1
            w_rest  = (_PAGE_W - 20.0) / n_extra
            _df_table(pdf, rw_tbl, [20.0] + [w_rest] * n_extra)
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 7, "Nessun asset con saldo al 31/12.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    # ── Sezione 2: Quadro T / RT ───────────────────────────────────────────────
    _section(pdf, f"Quadro {ql_rt} - Plusvalenze e Minusvalenze")

    if rt_df.empty:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(
            0, 8,
            f"Nessuna vendita/conversione nel {selected_year}: il Quadro {ql_rt} non va compilato.",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        pdf.ln(3)
    else:
        _subsection(pdf, "Valori da riportare nel modulo")

        if is_730:
            fields = {
                "T1 - Totale corrispettivi (ricavi vendite) (EUR)":    f"{total_plus + abs(total_minus):,.2f}",
                "T2 - Totale costi di acquisto LIFO (EUR)":            f"{total_minus:,.2f}",
                "T3 - Plusvalenze lorde (EUR)":                        f"{total_plus:,.2f}",
                "T4 - Minusvalenze (EUR)":                             f"{total_minus:,.2f}",
                "T5 - Reddito netto imponibile (EUR)":                 f"{net:,.2f}",
                "T6 - Imposta sostitutiva 26% (EUR)":                  f"{imposta:,.2f}",
            }
        else:
            total_ricavi = rt_df["Ricavo_EUR"].sum()
            total_costi  = rt_df["Costo_LIFO_EUR"].sum()
            fields = {
                "RT23 - Totale corrispettivi (ricavi) (EUR)":          f"{total_ricavi:,.2f}",
                "RT24 - Totale costi di acquisto LIFO (EUR)":          f"{total_costi:,.2f}",
                "RT25 - Plusvalenze (EUR)":                            f"{total_plus:,.2f}",
                "RT26 - Minusvalenze (EUR)":                           f"{total_minus:,.2f}",
                "RT27 - Reddito netto imponibile (EUR)":               f"{net:,.2f}",
                "RT29 - Imposta sostitutiva 26% (EUR)":                f"{imposta:,.2f}",
            }
        _kv_table(pdf, fields)

        if s.get("Note_Franchigia"):
            note = str(s["Note_Franchigia"]).replace("€", "EUR ")
            _notice(pdf, note, _GREEN_BG)

        if imposta > 0:
            _notice(
                pdf,
                f"F24: Codice 1715 (acconto) / 1716 (saldo) | Anno {selected_year} "
                f"| EUR {imposta:,.2f} | Scadenza: 30 giugno",
                _AMBER_BG,
            )

        # Dettaglio operazioni
        pdf.ln(2)
        _subsection(pdf, "Dettaglio operazioni (calcolo LIFO)")
        detail = rt_df[
            ["Data", "Asset", "Tipo_TX", "Quantita_Venduta", "Ricavo_EUR", "Costo_LIFO_EUR", "PlusMinus_EUR"]
        ].copy()
        detail.columns = ["Data", "Asset", "Tipo", "Qty", "Ricavo EUR", "Costo EUR", "+/- EUR"]
        detail["Ricavo EUR"] = detail["Ricavo EUR"].map("{:,.2f}".format)
        detail["Costo EUR"]  = detail["Costo EUR"].map("{:,.2f}".format)
        detail["+/- EUR"]    = detail["+/- EUR"].map("{:+,.2f}".format)
        detail["Qty"]        = detail["Qty"].map("{:.6f}".format)
        _df_table(pdf, detail, col_widths=[22.0, 15.0, 16.0, 26.0, 34.0, 33.0, 34.0])

    # ── Disclaimer ────────────────────────────────────────────────────────────
    pdf.ln(4)
    pdf.set_draw_color(*_GRAY_LINE)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_draw_color(0)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(
        0, 4,
        "AVVERTENZA: Documento generato automaticamente a scopo puramente informativo. "
        "I valori sono calcolati sulla base dei dati CSV Coinbase forniti dall'utente. "
        "L'utente e' responsabile della verifica dell'accuratezza dei dati e della conformita' "
        "della dichiarazione con la normativa vigente. "
        "Si raccomanda di consultare un professionista fiscale abilitato prima di presentare "
        "qualsiasi dichiarazione tributaria.",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())
