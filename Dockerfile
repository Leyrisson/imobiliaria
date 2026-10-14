# imobiliaria — container para distribuir ao cliente
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true
ENV PORT=5000
EXPOSE 5000
CMD ["sh", "iniciar.sh"]
