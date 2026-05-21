from __future__ import annotations

import json
import requests
import streamlit as st


def _creds() -> tuple[str, str]:
    try:
        url = st.secrets.get("supabase_url", "") or ""
        key = st.secrets.get("supabase_service_key", "") or ""
        return url, key
    except Exception:
        return "", ""


def _configured() -> bool:
    u, k = _creds()
    return bool(u and k)


def _headers() -> dict:
    _, key = _creds()
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }


@st.cache_data(ttl=120)
def load_clients() -> list[dict]:
    """Carrega clientes ativos do Supabase."""
    if not _configured():
        return []
    url, _ = _creds()
    try:
        resp = requests.get(
            f"{url}/rest/v1/clients",
            headers=_headers(),
            params={
                "active": "eq.true",
                "order":  "name.asc",
                "select": "*",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return [
            {
                "name":               r["name"],
                "key":                r.get("key") or "",
                "handle":             r.get("handle") or "",
                "tone_of_voice":      r.get("tone_of_voice") or "",
                "bio":                r.get("bio") or "",
                "tags":               r.get("tags") or [],
                "observations":       r.get("observations") or "",
                "goals":              r.get("goals") or {},
                "nicho":              r.get("nicho") or "",
                "sub_nicho":          r.get("sub_nicho") or "",
                "publico_alvo":       r.get("publico_alvo") or "",
                "competitors":        r.get("competitors") or "",
                "posts_organicos_mes": int(r.get("posts_organicos_mes") or 0),
                "youtube_id":         r.get("youtube_id") or "",
                "tiktok_id":          r.get("tiktok_id") or "",
            }
            for r in resp.json()
        ]
    except Exception:
        return []


@st.cache_data(ttl=120)
def load_latest_organic_metrics(client_key: str) -> str:
    """
    Busca métricas do último relatório orgânico e retorna texto formatado
    para o prompt da IA. Retorna string vazia se não houver dados.
    """
    if not _configured() or not client_key:
        return ""
    url, key = _creds()
    try:
        r = requests.get(
            f"{url}/rest/v1/report_history",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={
                "client_key": f"eq.{client_key}",
                "order":      "generated_at.desc",
                "limit":      "1",
                "select":     "date_from,date_to,metrics",
            },
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return ""
        row = rows[0]
        m = row.get("metrics", {})
        if isinstance(m, str):
            try:
                m = json.loads(m)
            except Exception:
                return ""

        period = f"{row.get('date_from','')[:10]} → {row.get('date_to','')[:10]}"
        lines = [f"Dados do último relatório orgânico ({period}):"]

        if m.get("org_eng_rate"):
            lines.append(f"- Taxa de engajamento: {float(m['org_eng_rate']):.2f}%")
        if m.get("org_reach"):
            lines.append(f"- Alcance orgânico: {int(m['org_reach']):,}".replace(",", "."))
        if m.get("followers_gained"):
            lines.append(f"- Seguidores ganhos: +{int(m['followers_gained'])}")

        # Frequência de postagem
        posting_days = m.get("posting_days", 0)
        total_posts   = m.get("total_posts", 0)
        days          = m.get("days", 0)
        if posting_days and days:
            lines.append(
                f"- Frequência histórica: {total_posts} posts em {days} dias "
                f"({posting_days} dias com publicação)"
            )

        # Performance por formato
        formats = m.get("content_formats", [])
        best_format = m.get("best_format", "")
        if formats:
            lines.append("\nPerformance por formato (use para distribuir o calendário):")
            for f in formats:
                lines.append(
                    f"  • {f.get('type','')}: {f.get('count',0)} posts | "
                    f"alcance médio {float(f.get('avg_reach',0)):.0f} | "
                    f"engaj. {float(f.get('avg_eng_rate',0)):.2f}%"
                )
            if best_format:
                lines.append(f"  → Formato com melhor desempenho: {best_format}")
                lines.append(
                    "  → Priorize esse formato no calendário (pelo menos 40% dos posts)."
                )

        # Melhores dias/horários
        best_hours = m.get("best_hours", [])
        if best_hours:
            lines.append("\nMelhores horários para publicar:")
            for h in best_hours[:3]:
                lines.append(
                    f"  • {h.get('label','')} — "
                    f"média de {float(h.get('avg_interactions',0)):.0f} interações"
                )
            lines.append(
                "  → Use esses horários para sugerir a distribuição dos posts ao longo da semana."
            )

        # Top posts — temas que performaram
        top_posts = m.get("top_posts", [])
        if top_posts:
            lines.append("\nTop posts do período (temas que mais geraram alcance):")
            for i, post in enumerate(top_posts[:5], 1):
                topic = post.get("caption_preview", post.get("topic", ""))
                fmt   = post.get("format", "")
                reach = post.get("reach", 0)
                lines.append(
                    f"  {i}. [{fmt}] Alcance: {int(reach):,} — {str(topic)[:80]}".replace(",", ".")
                )
            lines.append(
                "  → Inspire temas similares no calendário. Não repita, mas explore ângulos próximos."
            )

        # Perfil da audiência
        aud = m.get("audience", {})
        if aud:
            parts = []
            if aud.get("pct_female") or aud.get("pct_male"):
                parts.append(
                    f"{float(aud.get('pct_female',0)):.0f}% feminino / "
                    f"{float(aud.get('pct_male',0)):.0f}% masculino"
                )
            if aud.get("dominant_age"):
                parts.append(f"faixa dominante: {aud['dominant_age']} anos")
            if aud.get("top_country"):
                parts.append(f"principal país: {aud['top_country']}")
            if parts:
                lines.append(f"\nPerfil da audiência: {' | '.join(parts)}")

        # Análise estratégica
        ai = m.get("ai_strategic")
        if ai and isinstance(ai, dict):
            attentions = ai.get("attentions", [])
            if attentions:
                import re as _re
                lines.append("\nPontos de atenção do último relatório (evite repetir esses erros):")
                for item in attentions[:3]:
                    text = item[1] if isinstance(item, (list, tuple)) else item.get("text", "")
                    text = _re.sub(r"<[^>]+>", "", str(text))
                    lines.append(f"  • {text}")

        return "\n".join(lines)

    except Exception:
        return ""


@st.cache_data(ttl=60)
def load_approved_scripts_themes(client_name: str, client_key: str = "") -> str:
    """
    Carrega temas dos roteiros aprovados para o cliente.
    Filtra por client_key (preferencial) ou client_name como fallback.
    Retorna texto formatado para o prompt.
    """
    if not _configured() or (not client_name and not client_key):
        return ""
    url, key = _creds()
    filter_param = (
        {"client_key": f"eq.{client_key}"}
        if client_key
        else {"client_name": f"eq.{client_name}"}
    )
    try:
        r = requests.get(
            f"{url}/rest/v1/script_copies",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={
                **filter_param,
                "status":      "eq.aprovado",
                "order":       "hook_score_num.desc",
                "limit":       "10",
                "select":      "produto_tema,formato,pilar,hook_score_num",
            },
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return ""
        lines = ["\nTemas de roteiros aprovados para este cliente (use como referência):"]
        for row in rows:
            score = row.get("hook_score_num", 0)
            fmt   = row.get("formato", "")
            pilar = row.get("pilar", "")
            tema  = row.get("produto_tema", "")
            if tema:
                lines.append(f"  • [{fmt} · {pilar}] {tema} (hook score: {score}/10)")
        lines.append("  → Esses temas já foram validados pelo cliente. Explore variações deles.")
        return "\n".join(lines)
    except Exception:
        return ""
