FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY research/requirements.txt /app/research/requirements.txt
RUN pip install --disable-pip-version-check -r /app/research/requirements.txt \
    && groupadd --system research && useradd --system --gid research research
COPY research /app/research
RUN chown -R research:research /app
USER research
EXPOSE 8090
CMD ["uvicorn", "research.service:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "1"]
