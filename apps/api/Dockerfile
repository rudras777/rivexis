FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY rivexis_api ./rivexis_api
COPY docker-entrypoint.sh ./docker-entrypoint.sh
COPY migrate-database.sh ./migrate-database.sh
COPY configure-alert-worker-role.py ./configure-alert-worker-role.py
RUN pip install --no-cache-dir '.[full]' && chmod +x ./docker-entrypoint.sh ./migrate-database.sh ./configure-alert-worker-role.py
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn","rivexis_api.main:app","--host=0.0.0.0","--port=8000"]
