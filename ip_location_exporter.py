import requests, argparse
from flask import Flask, request, Response, abort
from prometheus_client import CollectorRegistry, Gauge, generate_latest

app = Flask(__name__)

API_CONFIGS = [
    {
        'url': 'https://ipinfo.io/',
        'key_name': 'token',
        'key_value': '#',
        'fields': {
            'ip': 'ip',
            'country_code': 'country',
            'city': 'city',
            'loc': 'loc'  # loc contains both latitude and longitude
        }
    },
    {
        'url': 'https://www.iplocate.io/api/lookup/',
        'key_name': 'apikey',
        'key_value': '#',
        'fields': {
            'ip': 'ip',
            'country_code': 'country_code',
            'city': 'city',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
    },
    {
        'url': 'https://freegeoip.live/json/',
        'key_name': '',
        'key_value': '',
        'fields': {
            'ip': 'ip',
            'country_code': 'country_code',
            'city': 'city',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
    },
]

def get_location(ip):
    for api in API_CONFIGS:
        try:
            url = f"{api['url']}{ip}"
            if api['key_name'] and api['key_value']:
                url += f"?{api['key_name']}={api['key_value']}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            fields = api['fields']

            if 'loc' in fields:  # Special case for APIs with combined latitude and longitude
                loc = data[fields['loc']]
                latitude, longitude = loc.split(',')
                return {
                    'ip': data[fields['ip']],
                    'country_code': data[fields['country_code']],
                    'city': data[fields['city']],
                    'latitude': float(latitude),
                    'longitude': float(longitude)
                }
            else:
                if all(field in data for field in fields.values()):
                    return {key: data[field] for key, field in fields.items()}
        except requests.RequestException as e:
            print(f"Error fetching data from {api['url']}: {e}")
    return None  # Return None if all APIs fail

def get_ips_from_prometheus(query, prometheus_url, metric_label):
    response = requests.get(f'{prometheus_url}/api/v1/query', params={'query': query})
    result = response.json()
    ips = [item['metric'][metric_label] for item in result['data']['result']]
    return ips

@app.route('/metrics')
def metrics():
    target = request.args.get('target')
    metric_label = request.args.get('metrics', target)

    if not target:
        abort(400, description="Missing required parameters 'target' and/or 'metrics'")

    query = target

    ips = get_ips_from_prometheus(query, prometheus_url, metric_label)
    registry = CollectorRegistry()
    g = Gauge('ip_location', 'IP Location Metrics', ['ip', 'country_code', 'city', 'latitude', 'longitude'], registry=registry)

    for ip in ips:
        location = get_location(ip)
        if location:
            g.labels(ip=ip, country_code=location['country_code'], city=location['city'], latitude=location['latitude'], longitude=location['longitude']).set(1)
        else:
            print(f"Failed to get location for IP: {ip}")

    return Response(generate_latest(registry), mimetype='text/plain')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IP Location Exporter')
    parser.add_argument('-u', '--prometheus_url', default='http://prometheus:9090', help='URL of Prometheus server (default: http://prometheus:9090)')
    parser.add_argument('-p', '--port', default=9012, help='Port to run the exporter on (default: 9012)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()
    prometheus_url = args.prometheus_url

    print(f"[Info] Metrics endpoint available at /metrics?target=<query>&metrics=<optional-label>")
    print(f"[Example] http://localhost:{args.port}/metrics?target=fgVpnSslTunnelSrcIp")

    app.run(host='0.0.0.0', port=args.port, debug=args.debug)
