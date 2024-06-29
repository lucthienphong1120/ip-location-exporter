FROM python:3.8-slim

WORKDIR /app
COPY ip_location_exporter.py /app
RUN pip install Flask requests prometheus_client

EXPOSE 9012

CMD ["python", "ip_location_exporter.py"]

