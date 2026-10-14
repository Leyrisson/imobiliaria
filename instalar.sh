#!/usr/bin/env bash
# Instala a Imobiliária como serviço do usuário (sobe junto com a máquina).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PORTA="${PORT:-5000}"
UNIDADE="$HOME/.config/systemd/user/app-imobiliaria.service"

mkdir -p "$(dirname "$UNIDADE")"
cat > "$UNIDADE" <<EOF
[Unit]
Description=Imobiliaria (web)
After=network.target

[Service]
WorkingDirectory=$DIR
Environment=PORT=$PORTA
ExecStart=/usr/bin/env python3 $DIR/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now app-imobiliaria
echo "Serviço app-imobiliaria ativo em http://127.0.0.1:$PORTA"
