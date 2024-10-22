# [IP-Location Exporter](https://github.com/lucthienphong1120/ip-location-exporter)

IP-Location Exporter for Prometheus expose IP to location using public APIs to retrieve location information from IPs.

API sources:
+ `https://ipinfo.io/`
+ `https://www.iplocate.io/api/lookup/`
+ `https://freegeoip.live/json/`

## Requirements and build

The exporter is built with the Flask library, and also uses prometheus_client to query the prometheus server to reference IP metrics, then uses the requests library to query the public API IP-location database to get location information.

```
pip3 install Flask requests prometheus_client
python3 ip_location_exporter.py --prometheus_url=http://prometheus:9090
```

You can defined flag `--push-gateway=http://pushgateway:9091` to send metrics to Pushgateway

*P/s: You should define your APIs and Token at code for some API sources at [API_CONFIGS](./ip_location_exporter.py#L7)!

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
      - .:/app
    command: ["python", "ip_location_exporter.py", "--prometheus_url=http://prometheus:9090"]
```

Quick deploy with Docker:

```
docker run -p 9012:9012 -v .:/app ltp1120/ip_location_exporter python ip_location_exporter.py --prometheus_url=http://prometheus:9090
```

Screenshot:

![image](https://github.com/lucthienphong1120/ip-location-exporter/assets/90561566/84703084-8803-4f76-b95d-5338d52e3048)

## Example output

After deploy, metrics are show at `/metrics` with port `9012` (default)

Sample query:
```
http://localhost:9012/metrics?target=fgVpnSslTunnelSrcIp
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

```
# PromQL to replace labels and join metrics
label_replace(
  fgVpnSslTunnelSrcIp{}, #input_query
  "ip", #dest_label
  "$1", #replacement
  "fgVpnSslTunnelSrcIp", #src_label
  "(.*)" #regex
)
or
label_join(fgVpnSslTunnelSrcIp, "ip", ",", "fgVpnSslTunnelSrcIp")
-> add new label "ip" from label "fgVpnSslTunnelSrcIp" of metrics fgVpnSslTunnelSrcIp{}
```

Finally you can use geomap to display data on a map based on latitude and longitude.

![image](https://github.com/lucthienphong1120/ip-location-exporter/assets/90561566/1b0d0693-9dce-4667-83dc-8537567376f2)
