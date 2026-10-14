# Como instalar e rodar localmente

Manual de instalação da **Imobiliária** (web).

## Requisitos

- Sistema operacional: Linux/macOS (Windows via WSL).
- Python 3.10+ no PATH.

## 1) Rodar local (rápido)

```bash
sh iniciar.sh
```

Abra **<http://127.0.0.1:5000>** no navegador.
A porta vem da variável `PORT` (padrão `5000`); troque com
`PORT=8080 sh iniciar.sh`.

## 2) Como serviço (sobe com a máquina)

```bash
sh instalar.sh                                  # registra serviço do usuário
systemctl --user status app-imobiliaria         # confere
```

## 3) Docker (teste isolado)

```bash
docker compose up --build
```

## Desinstalar

```bash
systemctl --user disable --now app-imobiliaria 2>/dev/null
rm -f ~/.config/systemd/user/app-imobiliaria.service
```
