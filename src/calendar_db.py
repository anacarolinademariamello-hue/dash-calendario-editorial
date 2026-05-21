"""
calendar_db.py — Persistência do calendário editorial no Supabase.

Tabela: editorial_calendar

SQL para criar:

create table editorial_calendar (
  id              serial primary key,
  client_key      text    default '',
  client_name     text    default '',
  mes_ano         text    default '',
  data_publicacao date,
  formato         text    default '',
  plataforma      text    default '',
  pilar           text    default '',
  tema            text    default '',
  objetivo        text    default '',
  hook_sugerido   text    default '',
  status          text    default 'ideia',
  observacoes     text    default '',
  ordem           int     default 0,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);
create index on editorial_calendar (client_key, mes_ano);
"""
from __future__ import annotations

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


def _headers(prefer: str = "return=minimal") -> dict:
    _, key = _creds()
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        prefer,
    }


def _rest() -> str:
    url, _ = _creds()
    return f"{url}/rest/v1/editorial_calendar"


# ── Carregar calendário ───────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_calendar(client_key: str, mes_ano: str) -> list[dict]:
    """Carrega todos os posts do calendário de um cliente/mês."""
    if not _configured():
        return []
    try:
        r = requests.get(
            _rest(),
            headers=_headers("return=representation"),
            params={
                "client_key": f"eq.{client_key}",
                "mes_ano":    f"eq.{mes_ano}",
                "order":      "data_publicacao.asc,ordem.asc",
                "select":     (
                    "id,client_key,client_name,mes_ano,data_publicacao,"
                    "formato,plataforma,pilar,tema,objetivo,hook_sugerido,"
                    "status,observacoes,ordem,created_at"
                ),
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


# ── Salvar calendário gerado ──────────────────────────────────────────────────

def save_calendar(
    client_key: str,
    client_name: str,
    mes_ano: str,
    posts: list[dict],
    date_from: str = "",
    date_to: str = "",
) -> tuple[bool, str]:
    """
    Salva posts no calendário. Se date_from/date_to fornecidos,
    apaga apenas posts nesse intervalo antes de inserir.
    Retorna (sucesso, mensagem).
    """
    if not _configured():
        return False, "Supabase não configurado."

    # 1. Deleta posts do período (intervalo ou mês inteiro)
    try:
        params = {
            "client_key": f"eq.{client_key}",
            "mes_ano":    f"eq.{mes_ano}",
        }
        if date_from and date_to:
            params["data_publicacao"] = f"gte.{date_from}"
            # Supabase REST não suporta dois filtros na mesma coluna via params dict,
            # então deletamos por range separado
            requests.delete(
                _rest(),
                headers=_headers(),
                params={
                    "client_key":      f"eq.{client_key}",
                    "mes_ano":         f"eq.{mes_ano}",
                    "data_publicacao": f"gte.{date_from}",
                    "and":             f"(data_publicacao.lte.{date_to})",
                },
                timeout=10,
            )
        else:
            requests.delete(
                _rest(),
                headers=_headers(),
                params=params,
                timeout=10,
            )
    except Exception:
        pass

    # 2. Insere novos posts
    payload = [
        {
            "client_key":      client_key,
            "client_name":     client_name,
            "mes_ano":         mes_ano,
            "data_publicacao": p.get("data", ""),
            "formato":         p.get("formato", ""),
            "plataforma":      p.get("plataforma", "Instagram"),
            "pilar":           p.get("pilar", ""),
            "tema":            p.get("tema", ""),
            "objetivo":        p.get("objetivo", ""),
            "hook_sugerido":   p.get("hook_sugerido", ""),
            "status":          "ideia",
            "observacoes":     "",
            "ordem":           i,
        }
        for i, p in enumerate(posts)
    ]
    try:
        r = requests.post(
            _rest(),
            headers=_headers("return=minimal"),
            json=payload,
            timeout=15,
        )
        if r.status_code in (200, 201):
            load_calendar.clear()
            return True, f"{len(posts)} posts salvos no calendário."
        return False, f"Erro {r.status_code}: {r.text}"
    except Exception as e:
        return False, f"Erro: {e}"


# ── Atualizar post individual ─────────────────────────────────────────────────

def update_post(post_id: int, fields: dict) -> bool:
    """Atualiza campos de um post específico."""
    if not _configured():
        return False
    try:
        r = requests.patch(
            _rest(),
            headers=_headers(),
            params={"id": f"eq.{post_id}"},
            json=fields,
            timeout=10,
        )
        load_calendar.clear()
        return r.status_code in (200, 204)
    except Exception:
        return False


# ── Atualizar status ──────────────────────────────────────────────────────────

def update_status(post_id: int, status: str) -> bool:
    return update_post(post_id, {"status": status})


# ── Deletar post ──────────────────────────────────────────────────────────────

def delete_post(post_id: int) -> bool:
    if not _configured():
        return False
    try:
        r = requests.delete(
            _rest(),
            headers=_headers(),
            params={"id": f"eq.{post_id}"},
            timeout=10,
        )
        load_calendar.clear()
        return r.status_code in (200, 204)
    except Exception:
        return False


# ── Verificar se já existe calendário ────────────────────────────────────────

def calendar_exists(client_key: str, mes_ano: str) -> bool:
    posts = load_calendar(client_key, mes_ano)
    return len(posts) > 0
