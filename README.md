# Ip-location Exporter



## Requirements and build

```
pip3 install Flask requests prometheus_client
python3 ip_location_exporter.py --prometheus_url=http://prometheus:9090
```

## Build with Docker

```
# docker-compose.yml
services:
  ip_location_exporter:
    image: ip_location_exporter
    ports:
      - "9012:9012"
    volumes:
      - ./ip_location_exporter.py:/app/ip_location_exporter.py
    command: ["python", "ip_location_exporter.py", "--prometheus_url=http://192.168.0.121:9090"]
```

## Example

After deploy, metrics are show at `/metrics` with port `9012` (default)

Sample query:
```
http://192.168.0.159:9012/metrics?query=fgVpnSslTunnelSrcIp
```

![image](https://github.com/lucthienphong1120/ip-location-exporter/assets/90561566/3a085e0c-0238-4e29-a884-c7d8d983ff6d)

## Prometheus Jobs

On prometheus you can scrape job from ip_location_exporter as follow:

```
scrape_configs:
  - job_name: 'ip_location_exporter'
    metrics_path: /metrics
    params:
      query: [fgVpnSslTunnelSrcIp]
    static_configs:
      - targets: ['ip_location_exporter:9012']
```
