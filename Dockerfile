FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/opt/sonic/src
ENV SONIC_RUNTIME_MODE=paper
ENV SONIC_DRY_RUN=true
ENV SONIC_STORAGE_PATH=/data/v2.db
ENV EXECUTION_ENABLED=false
ENV LIVE_TRADING_ENABLED=false

WORKDIR /opt/sonic

COPY pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY scripts ./scripts
COPY docs ./docs
COPY security ./security

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

RUN adduser --disabled-password --gecos "" --home /home/sonic sonic \
    && mkdir -p /data \
    && chown -R sonic:sonic /opt/sonic /data

USER sonic

VOLUME ["/data"]

# Paper-only canonical runtime health probe entrypoint.
ENTRYPOINT ["python", "-m", "sonic_xrpl.cli.main"]
CMD ["health", "--json"]
