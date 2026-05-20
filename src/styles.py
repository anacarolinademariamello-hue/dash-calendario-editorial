from __future__ import annotations


def get_sidebar_css() -> str:
    return """
[data-testid="stSidebar"] { background: #0d2137 !important; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #fff !important; }
div[data-testid="stSidebarNav"] { display: none; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea {
    background-color: #1a3a5c !important;
    color: #fff !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #f8b940, #d99a20) !important;
    color: #003f7c !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px !important;
    font-size: 1rem !important;
    width: 100% !important;
    margin-top: 6px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #ffc94d, #e8aa30) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #1a3a5c !important;
    color: #fff !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
}
"""


def get_main_css() -> str:
    return """
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
    background: #f0f3f8;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Header */
.cal-header-box {
    background: linear-gradient(135deg, #003f7c 0%, #1a5a9a 60%, #0d4080 100%);
    border-radius: 16px;
    padding: 26px 32px;
    color: #fff;
    margin-bottom: 24px;
}
.cal-header-title { font-size: 1.45rem; font-weight: 700; margin-bottom: 4px; }
.cal-header-sub   { font-size: .88rem; opacity: .65; }

/* Stats bar */
.stat-bar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-pill {
    background: #fff;
    border: 1px solid #dde3ed;
    border-radius: 20px;
    padding: 5px 16px;
    font-size: .82rem;
    color: #003f7c;
    font-weight: 600;
}

/* Calendário grid */
.cal-grid {
    background: #fff;
    border-radius: 14px;
    border: 1px solid #dde3ed;
    overflow: hidden;
    margin-bottom: 20px;
}
.cal-weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    background: #003f7c;
}
.cal-weekday {
    padding: 10px 6px;
    text-align: center;
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: rgba(255,255,255,.8);
}
.cal-days {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 1px;
    background: #e5e9f0;
}
.cal-cell {
    background: #fff;
    min-height: 100px;
    padding: 6px;
    vertical-align: top;
}
.cal-cell.empty { background: #f8fafc; }
.cal-cell.today { background: #eff6ff; }
.cal-day-num {
    font-size: .78rem;
    font-weight: 700;
    color: #374151;
    margin-bottom: 4px;
}
.cal-cell.today .cal-day-num { color: #003f7c; }
.cal-post {
    border-radius: 6px;
    padding: 4px 7px;
    margin-bottom: 3px;
    font-size: .72rem;
    line-height: 1.35;
    border-left: 3px solid;
    cursor: default;
}
.cal-post-format { font-weight: 700; }
.cal-post-tema {
    display: block;
    color: #374151;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
    font-size: .68rem;
}
.status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-left: 4px;
    vertical-align: middle;
}

/* Post cards na lista */
.post-card {
    background: #fff;
    border: 1px solid #dde3ed;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
}

/* Legenda */
.legend-bar { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 16px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: .78rem; color: #374151; }
.legend-dot { width: 12px; height: 12px; border-radius: 3px; }
"""


def get_page_header_html(client_name: str = "", mes_label: str = "") -> str:
    sub = f"{client_name}  ·  {mes_label}" if client_name and mes_label else (
        client_name or mes_label or "Selecione um cliente na barra lateral"
    )
    return f"""
<div class="cal-header-box">
  <div class="cal-header-title">📅 Calendário Editorial</div>
  <div class="cal-header-sub">{sub}</div>
</div>
"""


def get_sidebar_brand_html() -> str:
    return """
<div style="padding:12px 0 4px; display:flex; align-items:center; gap:10px;">
  <span style="font-size:1.5rem;">📅</span>
  <div>
    <div style="font-size:1rem;font-weight:700;color:#fff;">Calendário Editorial</div>
    <div style="font-size:.72rem;color:rgba(255,255,255,.5);">Conteúdo Orgânico · Dash Digital</div>
  </div>
</div>
<hr style="border:none;border-top:1px solid rgba(255,255,255,.12);margin:10px 0;">
"""
