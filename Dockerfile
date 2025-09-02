
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libnl-3-dev \
    libnl-route-3-dev \
    libprotobuf-dev \
    pkg-config \
    protobuf-compiler \
    git \
    flex \
    bison \
    && git clone https://github.com/google/nsjail.git /tmp/nsjail \
    && cd /tmp/nsjail \
    && make \
    && cp /tmp/nsjail/nsjail /usr/local/bin/ \
    && chmod +x /usr/local/bin/nsjail \
    && rm -rf /tmp/nsjail \
    && apt-get purge -y build-essential git flex bison \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .


EXPOSE 8080

CMD ["bash","-lc","exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 60 app:app"]
