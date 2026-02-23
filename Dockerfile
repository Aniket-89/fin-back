FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Let the compose file handle command based on service
# default will run uvicorn on $PORT provided by Railway
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
