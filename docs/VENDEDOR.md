# Instalação para clientes

Guia de entrega e instalação da **Imobiliária** para clientes.

## Empacotando para entregar

### Cliente com Docker (recomendado para web)

```bash
docker build -t imobiliaria .
docker save imobiliaria | gzip > imobiliaria.tar.gz
```

Entregue `imobiliaria.tar.gz`, `docker-compose.yml` e a pasta `docs/`. No
servidor do cliente:

```bash
docker load < imobiliaria.tar.gz && docker compose up -d
```

### Hospedagem leve (VPS)

- Suba o container na VPS, exponha a porta com um proxy (Caddy/nginx) + HTTPS.
- Combine com o cliente o valor do servidor + taxa de manutenção mensal.

## Checklist de entrega

- [ ] Código deste repositório (com tag de versão)
- [ ] `docs/INSTALACAO.md` e `docs/USO.md` entregues
- [ ] Dados de exemplo removidos/resetados, se houver
- [ ] Acesso, backup e manutenção combinados
