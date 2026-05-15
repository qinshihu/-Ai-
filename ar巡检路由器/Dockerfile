FROM python:3.11-slim

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

WORKDIR /app
ENV PYTHONWARNINGS="ignore"
COPY src/ src/          
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "src.app:app"]

