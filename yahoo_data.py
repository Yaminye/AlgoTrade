"""
Yahoo Finance Data Collector
Usage: python yahoo_data.py [TICKER]
"""

import sys
import yfinance as yf
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text
from rich.rule import Rule

console = Console()


def fmt(val, suffix="", prefix="", decimals=2):
    if val is None:
        return "[dim]N/A[/dim]"
    try:
        v = float(val)
        if abs(v) >= 1e12: return f"{prefix}{v/1e12:.{decimals}f}T{suffix}"
        if abs(v) >= 1e9:  return f"{prefix}{v/1e9:.{decimals}f}B{suffix}"
        if abs(v) >= 1e6:  return f"{prefix}{v/1e6:.{decimals}f}M{suffix}"
        if abs(v) >= 1e3:  return f"{prefix}{v/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{v:.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        return str(val)


def fmt_pct(val):
    if val is None:
        return "[dim]N/A[/dim]"
    try:
        return f"{float(val)*100:.2f}%"
    except (TypeError, ValueError):
        return str(val)


def color_change(val):
    if val is None:
        return "[dim]N/A[/dim]"
    try:
        v = float(val)
        sign = "+" if v > 0 else ""
        color = "green" if v > 0 else "red" if v < 0 else "white"
        return f"[{color}]{sign}{v:.2f}[/{color}]"
    except (TypeError, ValueError):
        return str(val)


def section_rule(title):
    console.print()
    console.print(Rule(f"[bold yellow]{title}[/bold yellow]", style="yellow"))


# ── 1. PRICE & MARKET DATA ──────────────────────────────────────────────────

def show_price(info, hist):
    section_rule("מחיר ונתוני שוק")

    price        = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close   = info.get("previousClose")
    open_        = info.get("open") or info.get("regularMarketOpen")
    day_high     = info.get("dayHigh") or info.get("regularMarketDayHigh")
    day_low      = info.get("dayLow") or info.get("regularMarketDayLow")
    volume       = info.get("volume") or info.get("regularMarketVolume")
    avg_vol      = info.get("averageVolume")
    mkt_cap      = info.get("marketCap")
    week52_high  = info.get("fiftyTwoWeekHigh")
    week52_low   = info.get("fiftyTwoWeekLow")
    currency     = info.get("currency", "")

    change       = (price - prev_close) if price and prev_close else None
    change_pct   = (change / prev_close * 100) if change and prev_close else None

    t = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t.add_column("פרמטר", style="bold")
    t.add_column("ערך", justify="right")

    def add(label, val): t.add_row(label, str(val))

    price_str = f"[bold white]{fmt(price, prefix=currency+' ')}[/bold white]"
    if change is not None:
        sign = "+" if change > 0 else ""
        col  = "green" if change > 0 else "red"
        price_str += f"  [{col}]{sign}{change:.2f} ({sign}{change_pct:.2f}%)[/{col}]"

    add("מחיר נוכחי",       price_str)
    add("סגירה קודמת",      fmt(prev_close, prefix=currency+" "))
    add("פתיחה",            fmt(open_,      prefix=currency+" "))
    add("גבוה יומי",        fmt(day_high,   prefix=currency+" "))
    add("נמוך יומי",        fmt(day_low,    prefix=currency+" "))
    add("52W גבוה",         fmt(week52_high, prefix=currency+" "))
    add("52W נמוך",         fmt(week52_low,  prefix=currency+" "))
    add("נפח מסחר",         fmt(volume))
    add("נפח ממוצע",        fmt(avg_vol))
    add("שווי שוק",         fmt(mkt_cap, prefix=currency+" "))

    console.print(t)

    # Last 10 days history
    if not hist.empty:
        console.print()
        h = Table(title="[bold]10 ימים אחרונים[/bold]", box=box.SIMPLE_HEAVY,
                  show_header=True, header_style="bold magenta")
        h.add_column("תאריך")
        h.add_column("פתיחה",   justify="right")
        h.add_column("גבוה",    justify="right")
        h.add_column("נמוך",    justify="right")
        h.add_column("סגירה",   justify="right")
        h.add_column("Adj Close", justify="right")
        h.add_column("נפח",     justify="right")

        tail = hist.tail(10)
        for date, row in tail.iterrows():
            adj = row.get("Adj Close") if "Adj Close" in row else row.get("Close")
            h.add_row(
                str(date.date()),
                f"{row['Open']:.2f}",
                f"{row['High']:.2f}",
                f"{row['Low']:.2f}",
                f"{row['Close']:.2f}",
                f"{adj:.2f}" if adj else "N/A",
                fmt(row["Volume"]),
            )
        console.print(h)


# ── 2. CORPORATE EVENTS (DIVIDENDS & SPLITS) ────────────────────────────────

def show_events(ticker_obj):
    section_rule("אירועי תאגיד – דיבידנדים ופיצולים")

    divs   = ticker_obj.dividends
    splits = ticker_obj.splits

    cols = []

    if not divs.empty:
        dt = Table(title="[bold]דיבידנדים אחרונים[/bold]", box=box.SIMPLE)
        dt.add_column("תאריך")
        dt.add_column("סכום", justify="right")
        for date, amount in divs.tail(10).items():
            dt.add_row(str(date.date()), f"{amount:.4f}")
        cols.append(dt)
    else:
        cols.append(Panel("[dim]אין נתוני דיבידנד[/dim]", title="דיבידנדים"))

    if not splits.empty:
        st = Table(title="[bold]פיצולי מניות[/bold]", box=box.SIMPLE)
        st.add_column("תאריך")
        st.add_column("יחס", justify="right")
        for date, ratio in splits.tail(10).items():
            st.add_row(str(date.date()), f"{ratio:.2f}:1")
        cols.append(st)
    else:
        cols.append(Panel("[dim]אין פיצולי מניות[/dim]", title="פיצולים"))

    console.print(Columns(cols, equal=True))


# ── 3. FINANCIALS ────────────────────────────────────────────────────────────

def show_financials(ticker_obj):
    section_rule("דוחות כספיים")

    def render_df(df, title):
        if df is None or df.empty:
            console.print(Panel(f"[dim]אין נתונים[/dim]", title=title))
            return
        t = Table(title=f"[bold]{title}[/bold]", box=box.SIMPLE_HEAVY,
                  show_header=True, header_style="bold green")
        t.add_column("שורה", style="bold", min_width=30)
        for col in df.columns:
            t.add_column(str(col.date()) if hasattr(col, 'date') else str(col),
                         justify="right")
        for row_name, row_data in df.iterrows():
            vals = [fmt(v) for v in row_data]
            t.add_row(str(row_name), *vals)
        console.print(t)
        console.print()

    render_df(ticker_obj.income_stmt,  "דוח רווח והפסד (שנתי)")
    render_df(ticker_obj.quarterly_income_stmt, "דוח רווח והפסד (רבעוני)")
    render_df(ticker_obj.balance_sheet, "מאזן (שנתי)")
    render_df(ticker_obj.cash_flow,    "תזרים מזומנים (שנתי)")


# ── 4. VALUATION & STATISTICS ────────────────────────────────────────────────

def show_valuation(info):
    section_rule("מכפילים והערכת שווי")

    t = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t.add_column("מדד", style="bold")
    t.add_column("ערך", justify="right")

    rows = [
        ("P/E Ratio (TTM)",        fmt(info.get("trailingPE"),  decimals=2)),
        ("Forward P/E",            fmt(info.get("forwardPE"),   decimals=2)),
        ("PEG Ratio",              fmt(info.get("pegRatio"),    decimals=2)),
        ("P/S Ratio (TTM)",        fmt(info.get("priceToSalesTrailing12Months"), decimals=2)),
        ("P/B Ratio",              fmt(info.get("priceToBook"), decimals=2)),
        ("EV/EBITDA",              fmt(info.get("enterpriseToEbitda"), decimals=2)),
        ("EV/Revenue",             fmt(info.get("enterpriseToRevenue"), decimals=2)),
        ("Enterprise Value",       fmt(info.get("enterpriseValue"))),
        ("שווי שוק",               fmt(info.get("marketCap"))),
        ("Beta (5Y Monthly)",      fmt(info.get("beta"),        decimals=3)),
        ("Book Value/Share",       fmt(info.get("bookValue"),   decimals=2)),
        ("EPS (TTM)",              fmt(info.get("trailingEps"), decimals=2)),
        ("Forward EPS",            fmt(info.get("forwardEps"),  decimals=2)),
    ]

    for label, val in rows:
        t.add_row(label, val)

    console.print(t)

    # Profitability
    p = Table(title="[bold]רווחיות[/bold]", box=box.ROUNDED,
              show_header=True, header_style="bold cyan")
    p.add_column("מדד", style="bold")
    p.add_column("ערך", justify="right")

    prof_rows = [
        ("שיעור רווח גולמי",    fmt_pct(info.get("grossMargins"))),
        ("שיעור רווח תפעולי",   fmt_pct(info.get("operatingMargins"))),
        ("שיעור רווח נקי",      fmt_pct(info.get("profitMargins"))),
        ("ROE",                  fmt_pct(info.get("returnOnEquity"))),
        ("ROA",                  fmt_pct(info.get("returnOnAssets"))),
        ("Revenue (TTM)",        fmt(info.get("totalRevenue"))),
        ("Gross Profit",         fmt(info.get("grossProfits"))),
        ("Free Cash Flow",       fmt(info.get("freeCashflow"))),
        ("Operating Cash Flow",  fmt(info.get("operatingCashflow"))),
    ]

    for label, val in prof_rows:
        p.add_row(label, val)

    console.print(p)


# ── 5. ANALYST RECOMMENDATIONS ───────────────────────────────────────────────

def show_analysts(info, ticker_obj):
    section_rule("המלצות ותחזיות אנליסטים")

    t = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t.add_column("מדד", style="bold")
    t.add_column("ערך", justify="right")

    rec_mean = info.get("recommendationMean")
    rec_key  = info.get("recommendationKey", "")
    target   = info.get("targetMeanPrice")
    t_high   = info.get("targetHighPrice")
    t_low    = info.get("targetLowPrice")
    t_median = info.get("targetMedianPrice")
    num_anal = info.get("numberOfAnalystOpinions")

    rec_color = {"strongbuy": "green", "buy": "green", "hold": "yellow",
                 "sell": "red", "strongsell": "red"}.get(
        (rec_key or "").lower().replace(" ", ""), "white")

    t.add_row("המלצה",         f"[{rec_color}]{rec_key.upper()}[/{rec_color}]" if rec_key else "[dim]N/A[/dim]")
    t.add_row("ציון ממוצע",    fmt(rec_mean, decimals=1) + " [dim](1=Buy, 5=Sell)[/dim]" if rec_mean else "[dim]N/A[/dim]")
    t.add_row("מחיר יעד ממוצע", fmt(target,  prefix=info.get("currency","")+" "))
    t.add_row("מחיר יעד גבוה", fmt(t_high,  prefix=info.get("currency","")+" "))
    t.add_row("מחיר יעד נמוך", fmt(t_low,   prefix=info.get("currency","")+" "))
    t.add_row("מחיר יעד חציוני", fmt(t_median, prefix=info.get("currency","")+" "))
    t.add_row("מספר אנליסטים", str(num_anal) if num_anal else "[dim]N/A[/dim]")

    console.print(t)

    # Earnings estimates
    try:
        earnings = ticker_obj.earnings_estimate
        if earnings is not None and not earnings.empty:
            ee = Table(title="[bold]תחזיות EPS[/bold]", box=box.SIMPLE_HEAVY,
                       show_header=True, header_style="bold magenta")
            ee.add_column("תקופה")
            for col in earnings.columns:
                ee.add_column(str(col), justify="right")
            for idx, row in earnings.iterrows():
                ee.add_row(str(idx), *[fmt(v) for v in row])
            console.print(ee)
    except Exception:
        pass

    # Recent recommendations history
    try:
        recs = ticker_obj.recommendations
        if recs is not None and not recs.empty:
            rt = Table(title="[bold]היסטוריית המלצות (10 אחרונות)[/bold]",
                       box=box.SIMPLE, show_header=True, header_style="bold magenta")
            rt.add_column("תאריך")
            for col in recs.columns:
                rt.add_column(str(col), justify="right")
            for date, row in recs.tail(10).iterrows():
                rt.add_row(str(date.date()) if hasattr(date, 'date') else str(date),
                           *[str(v) for v in row])
            console.print(rt)
    except Exception:
        pass


# ── 6. COMPANY PROFILE ───────────────────────────────────────────────────────

def show_profile(info):
    section_rule("פרופיל החברה")

    name     = info.get("longName") or info.get("shortName", "")
    sector   = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    country  = info.get("country", "N/A")
    website  = info.get("website", "N/A")
    employees = info.get("fullTimeEmployees")
    summary  = info.get("longBusinessSummary", "")

    console.print(Panel(
        f"[bold white]{name}[/bold white]\n"
        f"[cyan]מגזר:[/cyan] {sector}  |  [cyan]תעשייה:[/cyan] {industry}  |  "
        f"[cyan]מדינה:[/cyan] {country}\n"
        f"[cyan]אתר:[/cyan] {website}  |  [cyan]עובדים:[/cyan] {fmt(employees) if employees else 'N/A'}",
        box=box.ROUNDED, border_style="cyan"
    ))

    if summary:
        console.print(Panel(
            summary[:800] + ("..." if len(summary) > 800 else ""),
            title="[bold]תיאור[/bold]", border_style="dim"
        ))

    # Officers
    officers = info.get("companyOfficers", [])
    if officers:
        ot = Table(title="[bold]מנהלים בכירים[/bold]", box=box.SIMPLE)
        ot.add_column("שם")
        ot.add_column("תפקיד")
        ot.add_column("שכר", justify="right")
        for o in officers[:8]:
            salary = o.get("totalPay") or o.get("exercisedValue")
            ot.add_row(
                o.get("name", ""),
                o.get("title", ""),
                fmt(salary, prefix="$") if salary else "[dim]N/A[/dim]"
            )
        console.print(ot)


# ── 7. HOLDERS ───────────────────────────────────────────────────────────────

def show_holders(ticker_obj, info):
    section_rule("בעלי עניין")

    # Institutional
    try:
        inst = ticker_obj.institutional_holders
        if inst is not None and not inst.empty:
            it = Table(title="[bold]מחזיקים מוסדיים[/bold]", box=box.SIMPLE_HEAVY,
                       show_header=True, header_style="bold green")
            it.add_column("גוף")
            it.add_column("מניות", justify="right")
            it.add_column("שווי", justify="right")
            it.add_column("% מהחזקה", justify="right")
            for _, row in inst.head(10).iterrows():
                it.add_row(
                    str(row.get("Holder", row.iloc[0])),
                    fmt(row.get("Shares", row.iloc[1])),
                    fmt(row.get("Value", row.iloc[2] if len(row) > 2 else None)),
                    fmt_pct(row.get("pctHeld", row.get("% Out"))),
                )
            console.print(it)
    except Exception:
        pass

    # Mutual fund holders
    try:
        mf = ticker_obj.mutualfund_holders
        if mf is not None and not mf.empty:
            mt = Table(title="[bold]קרנות נאמנות[/bold]", box=box.SIMPLE_HEAVY,
                       show_header=True, header_style="bold green")
            mt.add_column("קרן")
            mt.add_column("מניות", justify="right")
            mt.add_column("שווי", justify="right")
            mt.add_column("% מהחזקה", justify="right")
            for _, row in mf.head(10).iterrows():
                mt.add_row(
                    str(row.get("Holder", row.iloc[0])),
                    fmt(row.get("Shares", row.iloc[1])),
                    fmt(row.get("Value", row.iloc[2] if len(row) > 2 else None)),
                    fmt_pct(row.get("pctHeld", row.get("% Out"))),
                )
            console.print(mt)
    except Exception:
        pass

    # Insider ownership from info
    insider_pct  = info.get("heldPercentInsiders")
    inst_pct     = info.get("heldPercentInstitutions")
    short_ratio  = info.get("shortRatio")
    short_pct    = info.get("shortPercentOfFloat")

    ot = Table(title="[bold]סיכום בעלות[/bold]", box=box.ROUNDED)
    ot.add_column("מדד", style="bold")
    ot.add_column("ערך", justify="right")
    ot.add_row("% בעלות פנימית",     fmt_pct(insider_pct))
    ot.add_row("% בעלות מוסדית",     fmt_pct(inst_pct))
    ot.add_row("Short % of Float",   fmt_pct(short_pct))
    ot.add_row("Short Ratio",        fmt(short_ratio, decimals=2))
    console.print(ot)


# ── 8. ESG ────────────────────────────────────────────────────────────────────

def show_esg(ticker_obj):
    try:
        esg = ticker_obj.sustainability
        if esg is None or esg.empty:
            return
        section_rule("דירוגי ESG")
        t = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        t.add_column("קטגוריה", style="bold")
        t.add_column("ערך", justify="right")
        for idx, row in esg.iterrows():
            t.add_row(str(idx), str(row.iloc[0]))
        console.print(t)
    except Exception:
        pass


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    ticker_sym = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    ticker_sym = ticker_sym.upper()

    console.print(Panel(
        f"[bold yellow]Yahoo Finance Data Collector[/bold yellow]\n"
        f"[white]Ticker: [bold cyan]{ticker_sym}[/bold cyan][/white]",
        box=box.DOUBLE_EDGE, border_style="yellow"
    ))

    with console.status(f"[bold green]שולף נתונים עבור {ticker_sym}...[/bold green]"):
        tk   = yf.Ticker(ticker_sym)
        info = tk.info
        hist = tk.history(period="1mo")

    if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
        console.print(f"[bold red]לא נמצאו נתונים עבור {ticker_sym}[/bold red]")
        sys.exit(1)

    show_profile(info)
    show_price(info, hist)
    show_events(tk)
    show_financials(tk)
    show_valuation(info)
    show_analysts(info, tk)
    show_holders(tk, info)
    show_esg(tk)

    console.print()
    console.print(Rule("[dim]סיום[/dim]", style="dim"))


if __name__ == "__main__":
    main()
