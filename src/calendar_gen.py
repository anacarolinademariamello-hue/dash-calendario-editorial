from __future__ import annotations

import json
import re
import calendar
import anthropic
import streamlit as st

# ── Configurações visuais ─────────────────────────────────────────────────────

FORMATO_CONFIG = {
    "Reels":         {"cor": "#8b5cf6", "cor_bg": "#f5f3ff", "icon": "🎬"},
    "Stories":       {"cor": "#f59e0b", "cor_bg": "#fffbeb", "icon": "📱"},
    "Carrossel":     {"cor": "#3b82f6", "cor_bg": "#eff6ff", "icon": "🖼️"},
    "Post Feed":     {"cor": "#10b981", "cor_bg": "#ecfdf5", "icon": "📸"},
    "YouTube Short": {"cor": "#ef4444", "cor_bg": "#fef2f2", "icon": "▶️"},
    "TikTok":        {"cor": "#000000", "cor_bg": "#f3f4f6", "icon": "🎵"},
}

STATUS_CONFIG = {
    "ideia":     {"label": "Ideia",       "cor": "#9ca3af", "cor_bg": "#f3f4f6"},
    "roteiro":   {"label": "Roteiro",     "cor": "#3b82f6", "cor_bg": "#eff6ff"},
    "producao":  {"label": "Em produção", "cor": "#f59e0b", "cor_bg": "#fffbeb"},
    "editado":   {"label": "Editado",     "cor": "#f97316", "cor_bg": "#fff7ed"},
    "publicado": {"label": "Publicado",   "cor": "#10b981", "cor_bg": "#ecfdf5"},
}

MESES_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

PILARES = [
    "Educação",
    "Entretenimento",
    "Autoridade",
    "Engajamento",
    "Inspiração",
    "Bastidores",
    "Vendas Orgânicas",
]

# Datas comemorativas brasileiras por mês (apenas as mais relevantes para marketing)
DATAS_COMEMORATIVAS = {
    1:  ["01/01 – Ano Novo", "25/01 – Aniversário de São Paulo"],
    2:  ["Carnaval (data variável)", "14/02 – Dia dos Namorados (algumas regiões)"],
    3:  ["08/03 – Dia Internacional da Mulher", "20/03 – Dia da Primavera (hemisfério norte)"],
    4:  ["21/04 – Tiradentes", "Páscoa (data variável)", "22/04 – Dia da Terra"],
    5:  ["01/05 – Dia do Trabalho", "Dia das Mães (2º domingo)", "12/05 – Dia do Nutricionista"],
    6:  ["12/06 – Dia dos Namorados", "Festa Junina / São João", "29/06 – São Pedro"],
    7:  ["Férias escolares de julho", "28/07 – Dia do Nutricionista (variações)"],
    8:  ["11/08 – Dia dos Pais", "22/08 – Dia do Folclore"],
    9:  ["07/09 – Independência do Brasil", "15/09 – Dia do Cliente"],
    10: ["12/10 – Dia das Crianças / Nossa Senhora Aparecida", "31/10 – Halloween"],
    11: ["02/11 – Finados", "15/11 – Proclamação da República", "Black Friday (última sexta)"],
    12: ["25/12 – Natal", "31/12 – Réveillon", "Dezembro: mês de balanço e retrospectiva"],
}


def _build_prompt(
    client: dict,
    mes: int,
    ano: int,
    organic_metrics: str,
    approved_themes: str,
    date_from: str = "",
    date_to: str = "",
    periodo_label: str = "",
) -> str:
    mes_label = MESES_PT[mes]
    _, n_days_month = calendar.monthrange(ano, mes)

    # Período efetivo
    if date_from and date_to:
        try:
            import datetime as _dt
            df = _dt.date.fromisoformat(date_from)
            dt = _dt.date.fromisoformat(date_to)
            n_days = (dt - df).days + 1
            periodo_str = f"{periodo_label} ({df.strftime('%d/%m')} a {dt.strftime('%d/%m/%Y')})"
            data_ini = date_from
            data_fim = date_to
        except Exception:
            n_days = n_days_month
            periodo_str = f"{mes_label}/{ano} (mês completo)"
            data_ini = f"{ano}-{mes:02d}-01"
            data_fim = f"{ano}-{mes:02d}-{n_days_month:02d}"
    else:
        n_days = n_days_month
        periodo_str = f"{mes_label}/{ano} (mês completo)"
        data_ini = f"{ano}-{mes:02d}-01"
        data_fim = f"{ano}-{mes:02d}-{n_days_month:02d}"

    # Posts proporcionais ao período
    posts_mes = client.get("posts_organicos_mes") or 12
    n_posts = max(1, round(posts_mes * n_days / n_days_month))

    # Plataformas ativas
    plataformas = ["Instagram"]
    if client.get("tiktok_id"):
        plataformas.append("TikTok")
    if client.get("youtube_id"):
        plataformas.append("YouTube")
    plataformas_str = ", ".join(plataformas)

    # Datas comemorativas relevantes no período
    datas_comemorativas = DATAS_COMEMORATIVAS.get(mes, [])
    datas_str = "\n".join(f"  • {d}" for d in datas_comemorativas) if datas_comemorativas else "  • Nenhuma data comemorativa relevante"

    # Tags / áreas
    tags = client.get("tags", [])
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

    # Pilares
    pilares_str = "\n".join(f"  • {p}" for p in PILARES)

    # Métricas e temas aprovados
    metrics_block = (
        f"\n## DADOS DO ÚLTIMO RELATÓRIO ORGÂNICO\n{organic_metrics}"
        if organic_metrics else ""
    )
    themes_block = (
        f"\n## TEMAS JÁ APROVADOS PELO CLIENTE\n{approved_themes}"
        if approved_themes else ""
    )

    # Tom de voz
    tov_block = (
        f"\n## TOM DE VOZ DO CLIENTE\n{client['tone_of_voice']}"
        if client.get("tone_of_voice") else ""
    )

    prompt = f"""Você é um estrategista de conteúdo orgânico sênior especializado no mercado brasileiro. \
Sua tarefa é criar um calendário editorial para o período: {periodo_str}.

## CLIENTE

- **Nome:** {client['name']}
- **Nicho:** {client.get('nicho','')} › {client.get('sub_nicho','')}
- **Público-alvo:** {client.get('publico_alvo','Não definido')}
- **Áreas de atuação:** {tags_str}
- **Plataformas ativas:** {plataformas_str}
- **Descrição:** {client.get('bio','')}
{tov_block}

## CONTRATO E PERÍODO

- **Posts orgânicos contratados:** {posts_mes} posts/mês
- **Período solicitado:** {periodo_str} ({n_days} dias)
- **Posts a gerar para este período:** {n_posts} posts (proporcional ao período)

## PILARES DE CONTEÚDO DISPONÍVEIS

{pilares_str}
{metrics_block}{themes_block}

## DATAS COMEMORATIVAS DE {mes_label.upper()}

{datas_str}

## SUA TAREFA

Distribua os **{n_posts} posts** no período de {data_ini} a {data_fim} seguindo estas diretrizes:

1. **Distribuição temporal:** Espalhe os posts de forma equilibrada. Evite mais de 2 posts no mesmo dia.
2. **Variedade de formatos:** {"Priorize Reels e Carrossel por terem maior alcance orgânico. " if len(plataformas) == 1 else f"Distribua entre as plataformas: {plataformas_str}. "}Use dados do relatório para definir a proporção ideal.
3. **Rotação de pilares:** Não repita o mesmo pilar mais de 2 vezes seguidas. Use todos os pilares ao longo do mês.
4. **Temas relevantes:** Use as datas comemorativas estrategicamente. Adapte temas ao nicho e público.
5. **Hook sugerido:** Para cada post, escreva a primeira frase/linha de abertura — o hook inicial.
6. **Progressão estratégica:** Monte o mês como uma narrativa: início (apresentação/valor), meio (aprofundamento) e fim (engajamento/CTA de mês).

## REGRAS DE QUALIDADE

- Cada tema deve ser específico e acionável — não use "Dicas de X" genericamente
- Hooks devem ser diretos, sem saudações e com gatilho de curiosidade ou valor
- Varie os objetivos: não faça todos os posts "educativos" — misture entretenimento, inspiração, engajamento
- Para Stories: pense em sequências interativas (enquetes, perguntas, antes/depois)
- Para Carrossel: pense em listas, comparações, passo-a-passo
- Para Reels: pense em narrativa visual de 15-60 segundos

## FORMATO DE RESPOSTA

Retorne EXCLUSIVAMENTE um JSON válido — sem texto antes ou depois, sem markdown, sem blocos de código.
O JSON deve ser um array com exatamente {n_posts} objetos, um por post:

[
  {{
    "data": "YYYY-MM-DD",
    "formato": "Reels|Stories|Carrossel|Post Feed|YouTube Short|TikTok",
    "plataforma": "Instagram|TikTok|YouTube",
    "pilar": "Um dos pilares listados acima",
    "tema": "Tema específico e acionável para o conteúdo (máximo 80 caracteres)",
    "objetivo": "Educar|Entreter|Inspirar|Engajar|Construir Autoridade|Vendas Orgânicas|Viralizar",
    "hook_sugerido": "Primeira frase/linha exata de abertura do conteúdo (máximo 120 caracteres)"
  }}
]

IMPORTANTE: Todas as datas devem estar dentro de {data_ini} e {data_fim}."""

    return prompt


def _parse_json_response(raw: str) -> list[dict]:
    """Extrai e parseia o JSON da resposta do Claude."""
    # Remove blocos de código markdown se presentes
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    raw = raw.strip("`").strip()

    # Tenta parsear direto
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # Tenta encontrar array JSON dentro do texto
    match = re.search(r"\[\s*\{.*\}\s*\]", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return []


def generate_calendar(
    client: dict,
    mes: int,
    ano: int,
    organic_metrics: str = "",
    approved_themes: str = "",
    date_from: str = "",
    date_to: str = "",
    periodo_label: str = "Mês completo",
) -> list[dict]:
    """
    Chama o Claude para gerar o calendário editorial.
    Retorna lista de posts ou lança ValueError em caso de falha.
    """
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("anthropic_api_key")
    except Exception:
        api_key = None

    if not api_key:
        raise ValueError("Chave ANTHROPIC_API_KEY não encontrada em .streamlit/secrets.toml.")

    claude = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(
        client, mes, ano, organic_metrics, approved_themes,
        date_from=date_from, date_to=date_to, periodo_label=periodo_label,
    )

    message = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    posts = _parse_json_response(raw)

    if not posts:
        raise ValueError(
            f"Não foi possível interpretar a resposta da IA.\n\nTrecho:\n{raw[:400]}"
        )

    # Normaliza campos
    n_posts = client.get("posts_organicos_mes") or 12
    for p in posts:
        if p.get("formato") not in FORMATO_CONFIG:
            p["formato"] = "Reels"
        if p.get("status") not in STATUS_CONFIG:
            p["status"] = "ideia"

    return posts[:n_posts]  # garante que não ultrapassa o contrato
