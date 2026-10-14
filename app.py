#!/usr/bin/env python3
"""Imobiliaria — interface inicial (plataforma de imóveis com IA).

Aplicativo web único, servido apenas com a biblioteca padrão do Python.

Uso:
    python3 app.py                 # http://127.0.0.1:8791
    PORT=9000 python3 app.py
    python3 app.py --porta 9000

O ponto de entrada é este arquivo: ele sobe o servidor, expõe a API e
serve a interface web em ``web/``. Módulos internos são importados por
ele — não há servidor separado.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

import busca  # motor de busca avançada com IA local (módulo interno)
import condominios  # gestão de condomínios: coleta, rotatividade e manutenção
import propostas  # IA de propostas de venda personalizadas (módulo interno)

WEB = RAIZ / "web"
PORTA_PADRAO = int(os.environ.get("PORT", "8792"))
_HOST_PADRAO = os.environ.get("HOST", "127.0.0.1")

APP = "Imobiliaria"
VERSAO = "0.3.0"
SLOGAN = "Encontre, negocie e feche o imóvel certo — com IA ao seu lado."


class ImobiliariaHandler(BaseHTTPRequestHandler):
    server_version = "Imobiliaria/1.0"

    # ------------------------------------------------------------------ #
    # Utilidades de resposta
    # ------------------------------------------------------------------ #
    def _json(self, dados, status: HTTPStatus = HTTPStatus.OK) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, mensagem: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self._json({"erro": mensagem}, status)

    def _query(self) -> dict:
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

    def _ler_json(self) -> dict:
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho <= 0:
            return {}
        bruto = self.rfile.read(tamanho)
        try:
            dados = json.loads(bruto.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}
        return dados if isinstance(dados, dict) else {}

    def log_message(self, formato, *args):  # discreto por padrão
        if os.environ.get("IMOBILIARIA_VERBOSE"):
            super().log_message(formato, *args)

    # ------------------------------------------------------------------ #
    # GET
    # ------------------------------------------------------------------ #
    def do_GET(self) -> None:  # noqa: N802
        caminho = urlparse(self.path).path
        if caminho.startswith("/api/"):
            return self._api_get(caminho)
        return self._servir_estatico(caminho)

    def _api_get(self, caminho: str) -> None:
        try:
            if caminho == "/api/estado":
                return self._json(self._estado())
            if caminho == "/api/ping":
                return self._json({"ok": True, "app": APP, "versao": VERSAO})
            if caminho == "/api/busca":
                return self._json(self._buscar())
            if caminho == "/api/imoveis":
                return self._json({"total": len(busca.CATALOGO),
                                   "imoveis": busca.CATALOGO})
            if caminho == "/api/filtros":
                return self._json({"tipos": busca.tipos(),
                                   "localidades": busca.localidades()})
            if caminho == "/api/propostas/opcoes":
                return self._json(propostas.opcoes())
            if caminho == "/api/propostas/mercado":
                q = self._query()
                return self._json(propostas.analisar_mercado(
                    q.get("tipo") or None, q.get("cidade") or None))
            if caminho == "/api/condominios":
                return self._json({
                    "total": len(condominios.CONDOMINIOS),
                    "resumo": condominios.resumo_geral(),
                    "condominios": condominios.listar(),
                })
            if caminho == "/api/condominios/opcoes":
                return self._json(condominios.opcoes())
            if caminho == "/api/condominios/resumo":
                return self._json(condominios.resumo_geral())
            if caminho == "/api/condominios/coletas":
                return self._json({"coletas": condominios.coletas_recentes()})
            if caminho.startswith("/api/condominios/"):
                return self._json(
                    condominios.detalhar(caminho.rsplit("/", 1)[-1]))
        except Exception as exc:  # noqa: BLE001
            return self._erro(f"falha interna: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._erro("rota não encontrada", HTTPStatus.NOT_FOUND)

    # ------------------------------------------------------------------ #
    # POST
    # ------------------------------------------------------------------ #
    def do_POST(self) -> None:  # noqa: N802
        caminho = urlparse(self.path).path
        try:
            if caminho == "/api/propostas":
                dados = self._ler_json()
                if not dados.get("imovel_id"):
                    return self._erro("informe o imóvel para a proposta")
                proposta = propostas.gerar_proposta(
                    dados["imovel_id"],
                    dados.get("cliente") or {},
                    dados.get("tom") or "consultivo")
                return self._json(proposta)
            if caminho == "/api/condominios/coletar":
                return self._json(condominios.coletar(self._ler_json()))
        except ValueError as exc:
            return self._erro(str(exc), HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # noqa: BLE001
            return self._erro(f"falha interna: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR)
        return self._erro("rota não encontrada", HTTPStatus.NOT_FOUND)

    def _estado(self) -> dict:
        return {
            "app": APP,
            "versao": VERSAO,
            "slogan": SLOGAN,
            "ponto_de_entrada": "app.py",
            "recursos": [
                {"id": "busca", "nome": "Busca inteligente",
                 "descricao": "Filtre por preço, localização, quartos e tipo "
                              "— com IA que entende a sua frase."},
                {"id": "propostas", "nome": "Propostas de venda",
                 "descricao": "IA que cria propostas personalizadas a partir "
                              "do histórico de vendas e das tendências de mercado."},
                {"id": "condominios", "nome": "Gestão de condomínios",
                 "descricao": "Rotatividade e manutenção sob controle."},
            ],
        }

    def _buscar(self) -> dict:
        """Busca avançada: IA interpreta a frase + filtros explícitos."""
        q = self._query()
        filtros = {c: q.get(c) for c in
                   ("tipo", "operacao", "quartos_min", "vagas_min",
                    "area_min", "preco_min", "preco_max", "local")
                   if q.get(c)}
        return busca.buscar(q.get("q", ""), filtros)

    # ------------------------------------------------------------------ #
    def _servir_estatico(self, caminho: str) -> None:
        import mimetypes

        if caminho in ("/", ""):
            arquivo = WEB / "index.html"
        else:
            relativo = caminho.lstrip("/")
            arquivo = (WEB / relativo).resolve()
            if WEB not in arquivo.parents and arquivo != WEB / "index.html":
                return self._erro("acesso negado", HTTPStatus.FORBIDDEN)
        if not arquivo.is_file():
            arquivo = WEB / "index.html"
        tipo, _ = mimetypes.guess_type(str(arquivo))
        corpo = arquivo.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", tipo or "application/octet-stream")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def criar_servidor(porta: int = PORTA_PADRAO, host: str = _HOST_PADRAO) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, porta), ImobiliariaHandler)


def main() -> None:
    ap = argparse.ArgumentParser(description="Imobiliaria — servidor local")
    ap.add_argument("--porta", type=int, default=PORTA_PADRAO)
    ap.add_argument("--host", default=_HOST_PADRAO)
    args = ap.parse_args()

    servidor = criar_servidor(args.porta, args.host)
    print(f"Imobiliaria no ar em http://{args.host}:{args.porta}")
    print(f"   {SLOGAN}")
    print("   Ctrl+C para encerrar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nImobiliaria encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
