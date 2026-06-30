"""Central dictionary of financial-metric explanations (Hebrew).
Used to render ℹ️ tooltips next to metric labels."""

GLOSSARY = {
    # Valuation multiples
    "pe":             "P/E (Price-to-Earnings): כמה משקיעים מוכנים לשלם על כל $1 של רווח. נמוך = זול יחסית לרווחים.",
    "forward_pe":     "Forward P/E: P/E מבוסס על תחזית הרווח לשנה הבאה במקום הרווח בפועל.",
    "peg":            "PEG: יחס P/E חלקי קצב צמיחת הרווחים. PEG מתחת ל-1 נחשב אטרקטיבי.",
    "ps":             "P/S (Price-to-Sales): שווי שוק חלקי הכנסות שנתיות. שימושי לחברות בלי רווחים.",
    "pb":             "P/B (Price-to-Book): שווי שוק חלקי ההון העצמי החשבונאי. מתחת ל-1 = נסחר מתחת להון.",
    "ev_ebitda":      "EV/EBITDA: שווי החברה (כולל חוב) חלקי הרווח התפעולי לפני פחת. נמוך יותר = זול יותר.",
    "ev_revenue":     "EV/Revenue: שווי החברה חלקי הכנסות. מדד שווי שלא תלוי במבנה הון.",

    # Profitability
    "gross_margin":   "Gross Margin: רווח גולמי כאחוז מהמכירות. ככל שגבוה יותר – החברה רווחית יותר בליבה.",
    "op_margin":      "Operating Margin: רווח תפעולי חלקי הכנסות. מודד יעילות תפעולית.",
    "net_margin":     "Net Margin: רווח נקי חלקי הכנסות. הרווח הסופי שנשאר אחרי הכל.",
    "roe":            "ROE (Return on Equity): רווח נקי חלקי הון עצמי. כמה החברה מייצרת לבעלי המניות.",
    "roa":            "ROA (Return on Assets): רווח נקי חלקי סך הנכסים. יעילות שימוש בנכסים.",

    # Growth
    "rev_growth":     "Revenue Growth: קצב צמיחה שנתי של הכנסות.",
    "earn_growth":    "Earnings Growth: קצב צמיחה שנתי של רווח נקי.",

    # Solvency & liquidity
    "de":             "D/E (Debt/Assets): סך התחייבויות חלקי סך הנכסים. גבוה יותר = ממונף יותר.",
    "current_ratio":  "יחס שוטף (Current Ratio): נכסים שוטפים חלקי התחייבויות שוטפות. מעל 1 = יכולת לכסות חובות לטווח קצר.",

    # Per-share metrics
    "eps":            "EPS (Earnings Per Share): רווח למניה (TTM – 12 חודשים אחרונים).",
    "forward_eps":    "Forward EPS: רווח למניה צפוי לשנה הבאה.",
    "book_value":     "Book Value/Share: הון עצמי למניה.",
    "div_share":      "Div/Share: דיבידנד שנתי למניה.",
    "div_yield":      "Div Yield: דיבידנד שנתי כאחוז ממחיר המניה.",
    "payout":         "Payout Ratio: אחוז הרווח שהחברה מחלקת כדיבידנד.",

    # Enterprise
    "ev":             "Enterprise Value: שווי שוק + חוב − מזומן. מייצג את המחיר ה'אמיתי' של החברה.",
    "market_cap":     "Market Cap: סך שווי המניות בשוק (מחיר × כמות מניות).",
    "revenue":        "Total Revenue: הכנסות שנתיות.",
    "fcf":            "Free Cash Flow: תזרים מזומנים חופשי – מזומן שנשאר אחרי השקעות הוניות.",
    "beta":           "Beta: מדד תנודתיות מול השוק. 1 = כמו השוק, >1 תנודתי יותר.",
    "shares_out":     "Shares Outstanding: כמות מניות בהנפקה כוללת.",

    # Holders
    "inst_pct":       "% בעלות מוסדית: אחוז המניות בידי קרנות וגופים מוסדיים.",
    "insider_pct":    "% בעלות פנימית: אחוז המניות בידי מנהלים ובעלי שליטה.",
    "short_pct":      "Short % of Float: אחוז המניות שהושאלו לצורך שורט.",
    "short_ratio":    "Short Ratio: כמות הימים שייקח לסגור את כל פוזיציות השורט בנפח ממוצע.",

    # KPI row
    "vol":            "נפח יומי: כמות המניות שנסחרו היום.",
    "avg_vol":        "נפח ממוצע: נפח מסחר ממוצע בתקופה האחרונה.",
    "w52h":           "52W גבוה: השיא של המניה ב-52 השבועות האחרונים.",
    "w52l":           "52W נמוך: התחתית של המניה ב-52 השבועות האחרונים.",

    # Analyst
    "rec":            "המלצת אנליסטים ממוצעת: BUY / HOLD / SELL.",
    "rec_mean":       "ציון ממוצע של אנליסטים. 1=Strong Buy, 5=Strong Sell.",
    "target_mean":    "מחיר יעד ממוצע של אנליסטים.",
    "target_high":    "המחיר יעד הגבוה ביותר בקרב האנליסטים.",
    "target_low":     "המחיר יעד הנמוך ביותר בקרב האנליסטים.",
    "upside":         "Upside / Downside: ההפרש (באחוזים) בין המחיר הנוכחי למחיר היעד הממוצע.",
}


def info_icon(key, color="#7c83fd"):
    """Return an inline ℹ️ span with a CSS-based tooltip (hover or click)."""
    text = GLOSSARY.get(key, "")
    if not text:
        return ""
    safe = text.replace('"', '&quot;').replace("'", "&#39;")
    return (
        f'<span class="info-tip" tabindex="0" style="color:{color};'
        f'margin-inline-start:4px">ℹ️'
        f'<span class="info-tip-text">{safe}</span></span>'
    )


def label_with_info(label, key, color="#7c83fd"):
    return f"{label}{info_icon(key, color)}"
