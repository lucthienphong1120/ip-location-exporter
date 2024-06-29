pip install Flask requests prometheus_client 

Run:
```
python3 ip_location_exporter.py --prometheus_url=http://prometheus:9090
```

Docker compose:
```
services:
  ip_location_exporter:
    image: ip_location_exporter
    ports:
      - "9012:9012"
    volumes:
      - ./ip_location_exporter.py:/app/ip_location_exporter.py
    command: ["python", "ip_location_exporter.py", "--prometheus_url=http://192.168.0.121:9090"]
```

Sample query:
```
http://192.168.0.159:9012/metrics?query=fgVpnSslTunnelSrcIp
```

Prometheus Jobs:
```
scrape_configs:
  - job_name: 'ip_location_exporter'
    metrics_path: /metrics
    params:
      query: [fgVpnSslTunnelSrcIp]
    static_configs:
      - targets: ['ip_location_exporter:9012']
```

