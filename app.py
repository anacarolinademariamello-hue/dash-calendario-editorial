import calendar
import datetime
import streamlit as st

from src.styles import get_sidebar_css, get_main_css, get_page_header_html, get_sidebar_brand_html
from src.clients import load_clients, load_latest_organic_metrics, load_approved_scripts_themes
from src.calendar_db import (
    load_calendar, save_calendar, update_post, update_status,
    delete_post, calendar_exists,
)
from src.calendar_gen import (
    generate_calendar, FORMATO_CONFIG, STATUS_CONFIG, MESES_PT, PILARES,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Calendário Editorial · Dash Digital",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"<style>{get_sidebar_css()}{get_main_css()}</style>", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
_TODAY = datetime.date.today()

MESES_OPCOES = {MESES_PT[i]: i for i in range(1, 13)}
ANOS_OPCOES  = [_TODAY.year - 1, _TODAY.year, _TODAY.year + 1]

OBJETIVOS = [
    "Educar", "Entreter", "Inspirar", "Engajar",
    "Construir Autoridade", "Vendas Orgânicas", "Viralizar",
]


def _formato_icon(fmt: str) -> str:
    return FORMATO_CONFIG.get(fmt, {}).get("icon", "📌")


def _formato_cor(fmt: str) -> str:
    return FORMATO_CONFIG.get(fmt, {}).get("cor", "#9ca3af")


def _formato_cor_bg(fmt: str) -> str:
    return FORMATO_CONFIG.get(fmt, {}).get("cor_bg", "#f3f4f6")


def _status_cfg(s: str) -> dict:
    return STATUS_CONFIG.get(s, STATUS_CONFIG["ideia"])


def _mes_ano_str(mes: int, ano: int) -> str:
    return f"{ano}-{mes:02d}"


def _periodo_dates(mes: int, ano: int, periodo: str) -> tuple[str, str]:
    """Retorna (date_from, date_to) no formato YYYY-MM-DD para o período."""
    import calendar as _cal
    _, last = _cal.monthrange(ano, mes)
    m = f"{mes:02d}"
    if periodo == "Mês completo":
        return f"{ano}-{m}-01", f"{ano}-{m}-{last:02d}"
    elif periodo == "1ª Quinzena (1–15)":
        return f"{ano}-{m}-01", f"{ano}-{m}-15"
    elif periodo == "2ª Quinzena (16–fim)":
        return f"{ano}-{m}-16", f"{ano}-{m}-{last:02d}"
    elif periodo == "Semana 1 (1–7)":
        return f"{ano}-{m}-01", f"{ano}-{m}-07"
    elif periodo == "Semana 2 (8–14)":
        return f"{ano}-{m}-08", f"{ano}-{m}-14"
    elif periodo == "Semana 3 (15–21)":
        return f"{ano}-{m}-15", f"{ano}-{m}-21"
    elif periodo == "Semana 4 (22–fim)":
        return f"{ano}-{m}-22", f"{ano}-{m}-{last:02d}"
    return f"{ano}-{m}-01", f"{ano}-{m}-{last:02d}"


def _build_calendar_html(posts: list[dict], mes: int, ano: int) -> str:
    """Monta o HTML do grid de calendário."""
    _, n_days = calendar.monthrange(ano, mes)
    first_weekday = calendar.monthrange(ano, mes)[0]  # 0=Seg ... 6=Dom

    # Agrupa posts por data
    posts_by_date: dict[str, list[dict]] = {}
    for p in posts:
        d = str(p.get("data_publicacao", ""))[:10]
        posts_by_date.setdefault(d, []).append(p)

    weekdays_html = "".join(
        f'<div class="cal-weekday">{d}</div>'
        for d in ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    )

    cells = []
    # Células vazias antes do dia 1
    for _ in range(first_weekday):
        cells.append('<div class="cal-cell empty"></div>')

    today_str = _TODAY.strftime("%Y-%m-%d")

    for day in range(1, n_days + 1):
        date_str = f"{ano}-{mes:02d}-{day:02d}"
        is_today = date_str == today_str
        cell_class = "cal-cell today" if is_today else "cal-cell"

        day_posts = posts_by_date.get(date_str, [])
        posts_html = ""
        for p in day_posts:
            fmt    = p.get("formato", "")
            tema   = p.get("tema", "")[:35]
            status = p.get("status", "ideia")
            cor    = _formato_cor(fmt)
            cor_bg = _formato_cor_bg(fmt)
            status_cor = _status_cfg(status)["cor"]
            icon   = _formato_icon(fmt)
            posts_html += (
                f'<div class="cal-post" '
                f'style="background:{cor_bg};border-left-color:{cor};">'
                f'<span class="cal-post-format" style="color:{cor};">{icon} {fmt}</span>'
                f'<span class="cal-post-tema">{tema}</span>'
                f'<span class="status-dot" style="background:{status_cor};"></span>'
                f'</div>'
            )

        cells.append(
            f'<div class="{cell_class}">'
            f'<div class="cal-day-num">{day}</div>'
            f'{posts_html}'
            f'</div>'
        )

    # Completa última linha com células vazias
    total_cells = len(cells)
    remainder = total_cells % 7
    if remainder:
        for _ in range(7 - remainder):
            cells.append('<div class="cal-cell empty"></div>')

    days_html = "".join(cells)

    return f"""
<div class="cal-grid">
  <div class="cal-weekdays">{weekdays_html}</div>
  <div class="cal-days">{days_html}</div>
</div>
"""


def _build_legend_html() -> str:
    items = "".join(
        f'<div class="legend-item">'
        f'<div class="legend-dot" style="background:{cfg["cor"]};"></div>'
        f'{fmt}'
        f'</div>'
        for fmt, cfg in FORMATO_CONFIG.items()
    )
    status_items = "".join(
        f'<div class="legend-item">'
        f'<div class="legend-dot" style="background:{cfg["cor"]};border-radius:50%;"></div>'
        f'{cfg["label"]}'
        f'</div>'
        for status, cfg in STATUS_CONFIG.items()
    )
    return f"""
<div style="margin-bottom:8px;">
  <div style="font-size:.7rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
    color:#9ca3af;margin-bottom:6px;">Formatos</div>
  <div class="legend-bar">{items}</div>
</div>
<div style="margin-bottom:16px;">
  <div style="font-size:.7rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
    color:#9ca3af;margin-bottom:6px;">Status (ponto colorido)</div>
  <div class="legend-bar">{status_items}</div>
</div>
"""


def _build_download_html(posts: list[dict], client: dict, mes: int, ano: int) -> str:
    mes_label = MESES_PT[mes]
    rows_html = ""
    for p in posts:
        fmt    = p.get("formato", "")
        status = p.get("status", "ideia")
        st_cfg = _status_cfg(status)
        fmt_cor = _formato_cor(fmt)
        rows_html += f"""
<tr>
  <td>{str(p.get("data_publicacao",""))[:10]}</td>
  <td style="color:{fmt_cor};font-weight:700;">{_formato_icon(fmt)} {fmt}</td>
  <td>{p.get("plataforma","")}</td>
  <td>{p.get("pilar","")}</td>
  <td>{p.get("tema","")}</td>
  <td>{p.get("objetivo","")}</td>
  <td style="font-style:italic;color:#6b7280;font-size:.85em;">{p.get("hook_sugerido","")}</td>
  <td><span style="background:{st_cfg["cor_bg"]};color:{st_cfg["cor"]};
    padding:2px 10px;border-radius:10px;font-size:.8em;font-weight:700;">
    {st_cfg["label"]}</span></td>
  <td>{p.get("observacoes","")}</td>
</tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Calendário Editorial — {client['name']} — {mes_label}/{ano}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f0f3f8;padding:32px 16px;color:#1a1a2e}}
  .container{{max-width:1100px;margin:0 auto}}
  .ph{{background:linear-gradient(135deg,#003f7c,#1a5a9a);border-radius:16px;padding:28px 32px;
    color:#fff;margin-bottom:24px}}
  .ph-title{{font-size:1.4rem;font-weight:700}}
  .ph-sub{{font-size:.85rem;opacity:.65;margin-top:4px}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;
    overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
  th{{background:#003f7c;color:#fff;padding:10px 14px;text-align:left;font-size:.78rem;
    font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
  td{{padding:10px 14px;border-bottom:1px solid #e5e9f0;font-size:.88rem;vertical-align:top}}
  tr:last-child td{{border-bottom:none}}
  tr:hover td{{background:#f8fafc}}
  .footer{{text-align:center;margin-top:24px;font-size:.75rem;color:#9ca3af}}
</style>
</head>
<body>
<div class="container">
  <div class="ph">
    <div class="ph-title">📅 Calendário Editorial — {mes_label} {ano}</div>
    <div class="ph-sub">{client['name']} · {client.get('handle','')} · {len(posts)} posts planejados</div>
  </div>
  <table>
    <thead><tr>
      <th>Data</th><th>Formato</th><th>Plataforma</th><th>Pilar</th>
      <th>Tema</th><th>Objetivo</th><th>Hook sugerido</th><th>Status</th><th>Observações</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="footer">Calendário Editorial · {client['name']} · Dash Digital · @dashdgt</div>
</div>
</body>
</html>"""


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [
    ("selected_client_key", None),
    ("cal_mes", _TODAY.month),
    ("cal_ano", _TODAY.year),
    ("editing_post_id", None),
    ("confirm_regen", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(get_sidebar_brand_html(), unsafe_allow_html=True)

    # Seleção de cliente
    all_clients = load_clients()
    if not all_clients:
        st.warning("Nenhum cliente cadastrado.")
    else:
        names = [c["name"] for c in all_clients]
        chosen_name = st.selectbox(
            "Cliente",
            names,
            label_visibility="visible",
            key="sb_client",
        )
        selected_client = next((c for c in all_clients if c["name"] == chosen_name), None)
        if selected_client:
            st.session_state.selected_client_key = selected_client["key"]

    # Seleção de mês/ano
    st.markdown("---")
    col_m, col_a = st.columns(2)
    with col_m:
        mes_nome = st.selectbox(
            "Mês",
            list(MESES_OPCOES.keys()),
            index=st.session_state.cal_mes - 1,
            key="sb_mes",
        )
        st.session_state.cal_mes = MESES_OPCOES[mes_nome]
    with col_a:
        ano_idx = ANOS_OPCOES.index(st.session_state.cal_ano) if st.session_state.cal_ano in ANOS_OPCOES else 1
        ano = st.selectbox(
            "Ano",
            ANOS_OPCOES,
            index=ano_idx,
            key="sb_ano",
        )
        st.session_state.cal_ano = ano

    mes = st.session_state.cal_mes
    ano = st.session_state.cal_ano
    mes_ano_str = _mes_ano_str(mes, ano)

    # Período
    st.markdown("**Período**")
    periodo_opcoes = [
        "Mês completo",
        "1ª Quinzena (1–15)",
        "2ª Quinzena (16–fim)",
        "Semana 1 (1–7)",
        "Semana 2 (8–14)",
        "Semana 3 (15–21)",
        "Semana 4 (22–fim)",
    ]
    periodo = st.selectbox(
        "Período",
        periodo_opcoes,
        label_visibility="collapsed",
        key="sb_periodo",
    )
    st.markdown("---")

    # Info do cliente selecionado
    if all_clients and selected_client:
        n_posts = selected_client.get("posts_organicos_mes") or 0
        plataformas = ["📸 Instagram"]
        if selected_client.get("tiktok_id"): plataformas.append("🎵 TikTok")
        if selected_client.get("youtube_id"): plataformas.append("▶️ YouTube")

        st.markdown(
            f'<div style="background:rgba(255,255,255,.08);border-radius:10px;padding:10px 12px;margin-bottom:10px;">'
            f'<div style="font-size:.78rem;color:rgba(255,255,255,.5);margin-bottom:4px;">CLIENTE SELECIONADO</div>'
            f'<div style="font-weight:700;font-size:.95rem;">{selected_client["name"]}</div>'
            f'<div style="font-size:.78rem;color:rgba(255,255,255,.6);margin-top:2px;">'
            f'{selected_client.get("nicho","")}</div>'
            f'<div style="font-size:.78rem;color:#f8b940;margin-top:6px;">'
            f'📅 {n_posts} posts/mês contratados</div>'
            f'<div style="font-size:.75rem;color:rgba(255,255,255,.5);margin-top:3px;">'
            f'{"  ·  ".join(plataformas)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        already_exists = calendar_exists(selected_client["key"], mes_ano_str)

        date_from, date_to = _periodo_dates(mes, ano, periodo)

        # Verifica se já existe conteúdo neste período
        posts_periodo = [
            p for p in load_calendar(selected_client["key"], mes_ano_str)
            if date_from <= str(p.get("data_publicacao", ""))[:10] <= date_to
        ]
        periodo_tem_posts = len(posts_periodo) > 0

        if periodo_tem_posts:
            st.markdown(
                f'<div style="background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);'
                f'border-radius:8px;padding:8px 12px;font-size:.78rem;color:#6ee7b7;margin-bottom:8px;">'
                f'✅ {len(posts_periodo)} posts gerados para {periodo}</div>',
                unsafe_allow_html=True,
            )
            if not st.session_state.confirm_regen:
                if st.button("🔄 Regenerar período com IA", use_container_width=True):
                    st.session_state.confirm_regen = True
                    st.rerun()
            else:
                st.warning(f"Apagará os {len(posts_periodo)} posts deste período. Confirma?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Sim", use_container_width=True):
                        st.session_state.confirm_regen = False
                        with st.spinner("Gerando..."):
                            try:
                                metrics  = load_latest_organic_metrics(selected_client["key"])
                                approved = load_approved_scripts_themes(
                                    selected_client["name"],
                                    client_key=selected_client.get("key", ""),
                                )
                                posts_gen = generate_calendar(
                                    selected_client, mes, ano, metrics, approved,
                                    date_from=date_from, date_to=date_to,
                                    periodo_label=periodo,
                                )
                                ok, msg = save_calendar(
                                    selected_client["key"], selected_client["name"],
                                    mes_ano_str, posts_gen,
                                    date_from=date_from, date_to=date_to,
                                )
                                if ok:
                                    load_calendar.clear()
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            except Exception as e:
                                st.error(str(e))
                with c2:
                    if st.button("❌ Não", use_container_width=True):
                        st.session_state.confirm_regen = False
                        st.rerun()
        else:
            if st.button(f"✨ Gerar {periodo} com IA", use_container_width=True):
                with st.spinner(f"Gerando {periodo}..."):
                    try:
                        metrics  = load_latest_organic_metrics(selected_client["key"])
                        approved = load_approved_scripts_themes(
                            selected_client["name"],
                            client_key=selected_client.get("key", ""),
                        )
                        posts_gen = generate_calendar(
                            selected_client, mes, ano, metrics, approved,
                            date_from=date_from, date_to=date_to,
                            periodo_label=periodo,
                        )
                        ok, msg = save_calendar(
                            selected_client["key"], selected_client["name"],
                            mes_ano_str, posts_gen,
                            date_from=date_from, date_to=date_to,
                        )
                        if ok:
                            load_calendar.clear()
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                    except Exception as e:
                        st.error(str(e))

        # Download
        posts_now = load_calendar(selected_client["key"], mes_ano_str)
        if posts_now:
            st.markdown("---")
            html_data = _build_download_html(posts_now, selected_client, mes, ano)
            st.download_button(
                label="⬇️ Baixar em HTML",
                data=html_data,
                file_name=f"calendario_{selected_client['key']}_{mes_ano_str}.html",
                mime="text/html",
                use_container_width=True,
            )

            # Stats rápidas
            total = len(posts_now)
            publicados = sum(1 for p in posts_now if p.get("status") == "publicado")
            em_prod    = sum(1 for p in posts_now if p.get("status") == "producao")
            restantes  = total - publicados

            st.markdown(
                f'<div style="background:rgba(255,255,255,.06);border-radius:10px;'
                f'padding:10px 12px;margin-top:8px;font-size:.78rem;">'
                f'<div style="color:#f8b940;font-weight:700;margin-bottom:6px;">Progresso do mês</div>'
                f'<div style="color:rgba(255,255,255,.7);">📋 {total} posts planejados</div>'
                f'<div style="color:#6ee7b7;">✅ {publicados} publicados</div>'
                f'<div style="color:#fcd34d;">🎬 {em_prod} em produção</div>'
                f'<div style="color:rgba(255,255,255,.5);">⏳ {restantes} pendentes</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if not all_clients:
    st.markdown(get_page_header_html(), unsafe_allow_html=True)
    st.info("Nenhum cliente cadastrado. Acesse o Gerenciador de Clientes para cadastrar.")
    st.stop()

if not selected_client:
    st.markdown(get_page_header_html(), unsafe_allow_html=True)
    st.stop()

mes_label_full = f"{MESES_PT[mes]} de {ano}"
st.markdown(
    get_page_header_html(selected_client["name"], mes_label_full),
    unsafe_allow_html=True,
)

# Carrega posts
posts = load_calendar(selected_client["key"], mes_ano_str)

if not posts:
    # Estado vazio
    n_contrato = selected_client.get("posts_organicos_mes") or 0
    has_metrics = bool(load_latest_organic_metrics(selected_client["key"]))

    st.markdown(
        f'<div style="background:#fff;border:1px solid #dde3ed;border-radius:16px;'
        f'padding:48px 32px;text-align:center;margin-top:8px;">'
        f'<div style="font-size:3rem;margin-bottom:16px;">📅</div>'
        f'<h2 style="color:#003f7c;font-size:1.3rem;margin-bottom:8px;">'
        f'Nenhum calendário gerado para {mes_label_full}</h2>'
        f'<p style="color:#6b7280;max-width:480px;margin:0 auto 20px;line-height:1.7;">'
        f'Clique em <strong>✨ Gerar Calendário com IA</strong> na barra lateral para criar '
        f'o planejamento de {n_contrato or "?"} posts para {selected_client["name"]} em {mes_label_full}.'
        f'</p>'
        + (
            f'<div style="background:#d1fae5;color:#065f46;display:inline-block;'
            f'padding:6px 16px;border-radius:20px;font-size:.82rem;font-weight:600;">'
            f'✅ Relatório orgânico disponível — IA vai usar dados reais</div>'
            if has_metrics else
            f'<div style="background:#fef3c7;color:#92400e;display:inline-block;'
            f'padding:6px 16px;border-radius:20px;font-size:.82rem;font-weight:600;">'
            f'⚠️ Sem relatório orgânico — IA vai usar apenas o cadastro do cliente</div>'
        )
        + f'</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_cal, tab_lista = st.tabs(["📅 Calendário", "📋 Lista & Gestão"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: CALENDÁRIO (grid visual)
# ══════════════════════════════════════════════════════════════════════════════
with tab_cal:
    # Stats rápidas
    total     = len(posts)
    pub_count = sum(1 for p in posts if p.get("status") == "publicado")
    fmt_counts = {}
    for p in posts:
        f = p.get("formato", "Outro")
        fmt_counts[f] = fmt_counts.get(f, 0) + 1

    fmt_str = "  ·  ".join(f"{_formato_icon(f)} {f}: {n}" for f, n in sorted(fmt_counts.items()))

    st.markdown(
        f'<div class="stat-bar">'
        f'<div class="stat-pill">📋 {total} posts planejados</div>'
        f'<div class="stat-pill">✅ {pub_count} publicados</div>'
        f'<div class="stat-pill">{fmt_str}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Legenda
    st.markdown(_build_legend_html(), unsafe_allow_html=True)

    # Grid do calendário
    st.markdown(_build_calendar_html(posts, mes, ano), unsafe_allow_html=True)

    st.caption(
        "💡 Use a aba **Lista & Gestão** para editar temas, alterar status e gerenciar cada post individualmente."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: LISTA & GESTÃO
# ══════════════════════════════════════════════════════════════════════════════
with tab_lista:
    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_status = st.selectbox(
            "Filtrar por status",
            ["Todos"] + [v["label"] for v in STATUS_CONFIG.values()],
            key="filtro_status",
        )
    with col_f2:
        filtro_formato = st.selectbox(
            "Filtrar por formato",
            ["Todos"] + list(FORMATO_CONFIG.keys()),
            key="filtro_formato",
        )
    with col_f3:
        filtro_pilar = st.selectbox(
            "Filtrar por pilar",
            ["Todos"] + PILARES,
            key="filtro_pilar",
        )

    # Aplica filtros
    status_label_to_key = {v["label"]: k for k, v in STATUS_CONFIG.items()}
    posts_filtrados = posts
    if filtro_status != "Todos":
        sk = status_label_to_key.get(filtro_status, filtro_status)
        posts_filtrados = [p for p in posts_filtrados if p.get("status") == sk]
    if filtro_formato != "Todos":
        posts_filtrados = [p for p in posts_filtrados if p.get("formato") == filtro_formato]
    if filtro_pilar != "Todos":
        posts_filtrados = [p for p in posts_filtrados if p.get("pilar") == filtro_pilar]

    st.markdown(
        f'<div style="font-size:.8rem;color:#9ca3af;margin-bottom:8px;">'
        f'Exibindo {len(posts_filtrados)} de {len(posts)} posts</div>',
        unsafe_allow_html=True,
    )

    if not posts_filtrados:
        st.info("Nenhum post corresponde ao filtro selecionado.")
    else:
        for p in posts_filtrados:
            post_id  = p["id"]
            fmt      = p.get("formato", "")
            status   = p.get("status", "ideia")
            st_cfg   = _status_cfg(status)
            fmt_cor  = _formato_cor(fmt)
            fmt_icon = _formato_icon(fmt)
            data_str = str(p.get("data_publicacao", ""))[:10]

            # Formata data para exibição
            try:
                dt = datetime.date.fromisoformat(data_str)
                DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
                data_label = f"{DIAS_PT[dt.weekday()]}, {dt.day:02d}/{dt.month:02d}"
            except Exception:
                data_label = data_str

            with st.expander(
                f"{fmt_icon} {data_label}  ·  {fmt}  ·  {p.get('tema','')[:50]}",
                expanded=(st.session_state.editing_post_id == post_id),
            ):
                # Status badges — clique para mudar
                st.markdown("**Status:**")
                status_cols = st.columns(len(STATUS_CONFIG))
                for idx, (sk, scfg) in enumerate(STATUS_CONFIG.items()):
                    with status_cols[idx]:
                        is_active = status == sk
                        btn_style = (
                            f"background:{scfg['cor']};color:#fff;"
                            if is_active else
                            f"background:{scfg['cor_bg']};color:{scfg['cor']};"
                        )
                        if st.button(
                            scfg["label"],
                            key=f"st_{post_id}_{sk}",
                            use_container_width=True,
                        ):
                            if update_status(post_id, sk):
                                load_calendar.clear()
                                st.rerun()

                st.markdown("---")

                # Campos editáveis
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_data = st.date_input(
                        "Data de publicação",
                        value=datetime.date.fromisoformat(data_str) if data_str else _TODAY,
                        key=f"data_{post_id}",
                    )
                    new_formato = st.selectbox(
                        "Formato",
                        list(FORMATO_CONFIG.keys()),
                        index=list(FORMATO_CONFIG.keys()).index(fmt) if fmt in FORMATO_CONFIG else 0,
                        key=f"fmt_{post_id}",
                    )
                    new_plataforma = st.selectbox(
                        "Plataforma",
                        ["Instagram", "TikTok", "YouTube"],
                        index=["Instagram", "TikTok", "YouTube"].index(p.get("plataforma", "Instagram"))
                        if p.get("plataforma") in ["Instagram", "TikTok", "YouTube"] else 0,
                        key=f"plt_{post_id}",
                    )
                with ec2:
                    new_pilar = st.selectbox(
                        "Pilar",
                        PILARES,
                        index=PILARES.index(p.get("pilar", PILARES[0])) if p.get("pilar") in PILARES else 0,
                        key=f"pil_{post_id}",
                    )
                    new_objetivo = st.selectbox(
                        "Objetivo",
                        OBJETIVOS,
                        index=OBJETIVOS.index(p.get("objetivo", OBJETIVOS[0])) if p.get("objetivo") in OBJETIVOS else 0,
                        key=f"obj_{post_id}",
                    )

                new_tema = st.text_input(
                    "Tema",
                    value=p.get("tema", ""),
                    key=f"tema_{post_id}",
                )
                new_hook = st.text_area(
                    "Hook sugerido",
                    value=p.get("hook_sugerido", ""),
                    height=70,
                    key=f"hook_{post_id}",
                )
                new_obs = st.text_area(
                    "Observações / Briefing adicional",
                    value=p.get("observacoes", ""),
                    height=70,
                    key=f"obs_{post_id}",
                    placeholder="Adicione detalhes, referências, notas para o editor...",
                )

                save_col, del_col = st.columns([4, 1])
                with save_col:
                    if st.button("💾 Salvar alterações", key=f"save_{post_id}", use_container_width=True):
                        ok = update_post(post_id, {
                            "data_publicacao": new_data.isoformat(),
                            "formato":         new_formato,
                            "plataforma":      new_plataforma,
                            "pilar":           new_pilar,
                            "objetivo":        new_objetivo,
                            "tema":            new_tema.strip(),
                            "hook_sugerido":   new_hook.strip(),
                            "observacoes":     new_obs.strip(),
                        })
                        if ok:
                            load_calendar.clear()
                            st.success("Post atualizado!")
                            st.rerun()
                        else:
                            st.error("Erro ao salvar.")
                with del_col:
                    if st.button("🗑️", key=f"del_{post_id}", use_container_width=True, help="Excluir post"):
                        if delete_post(post_id):
                            load_calendar.clear()
                            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<p style="text-align:center;font-size:.72rem;color:#9ca3af;margin-top:20px;">'
    "Calendário Editorial · Dash Digital · @dashdgt · Dados sincronizados via Supabase</p>",
    unsafe_allow_html=True,
)
