FROM python:3.11-slim

# 安装必要的系统工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
ENV PYTHONWARNINGS="ignore"

COPY src/ /app/src/ 
EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "4", "--timeout", "600", "--max-requests", "100", "--max-requests-jitter", "10", "--reload", "src.app:app"]

