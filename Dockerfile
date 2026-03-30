FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY memio/ memio/

RUN pip install --no-cache-dir ".[server,all]"

EXPOSE 8080

CMD ["memio-server"]
