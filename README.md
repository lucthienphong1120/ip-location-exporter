# Ip-location Exporter

Ip-location Exporter for Prometheus expose IP to location using public APIs to retrieve location information from IPs.

API sources sample:
+ `https://www.iplocate.io/api/lookup/1.52.219.140`
+ `https://freegeoip.live/json/1.52.219.140`

![image](https://github.com/lucthienphong1120/ip-location-exporter/assets/90561566/836e84f5-c128-4d83-bb10-81942acea43c)

## Requirements and build

The exporter is built with the Flask library, and also uses prometheus_client to query the prometheus server to reference IP metrics, then uses the requests library to query the public API IP-location database to get location information.

```
pip3 install Flask requests prometheus_client
python3 ip_location_exporter.py --prometheus_url=http://prometheus:9090
```

## Build with Docker

You can use docker to deploy ip-location exporter quickly, below is an example of docker compose:

```
# docker-compose.yml
services:
  ip_location_exporter:
    image: ltp1120/ip_location_exporter
    ports:
      - "9012:9012"
    volumes:
      - ./ip_location_exporter.py:/app/ip_location_exporter.py
    command: ["python", "ip_location_exporter.py", "--prometheus_url=http://prometheus:9090"]
```

## Example output

After deploy, metrics are show at `/metrics` with port `9012` (default)

Sample query:
```
http://localhost:9012/target?query=fgVpnSslTunnelSrcIp
```

![image](https://github.com/lucthienphong1120/ip-location-exporter/assets/90561566/9692b8b0-003f-4503-97e5-940f5dc8378c)

## Prometheus Jobs

On prometheus you can scrape job from ip_location_exporter as follow:

```
- job_name: 'ip_location_exporter'
    scrape_interval: 1m
    scrape_timeout: 30s
    static_configs:
      - targets: ["fgVpnSslTunnelSrcIp"]
      - targets: ["fgVpnTunEntLocGwyIp"]
      - targets: ["fgVpnTunEntRemGwyIp"]
    metrics_path: /metrics
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 'ip_location_exporter:9012' # IP Location Exporter
```

## Visualize with Grafana

In grafana, you just need to add query to ip-location-exporter job to get the corresponding reference, then use join table or group by to merge into a unified table.

Finally you can use geomap to display data on a map based on latitude and longitude.
