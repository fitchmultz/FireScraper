FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libstdc++6

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt && \
    pip uninstall -y py && \
    playwright install chromium && playwright install-deps chromium && \
    ln -s /usr/local/bin/supervisord /usr/bin/supervisord

COPY . ./

EXPOSE $PORT
CMD hypercorn main:app --bind [::]:$PORT
