import requests, argparse
from flask import Flask, request, Response, abort
from prometheus_client import CollectorRegistry, Gauge, generate_latest

app = Flask(__name__)

API_URLS = ['https://www.iplocate.io/api/lookup/', 'https://freegeoip.live/json/']

def get_location(ip):
    for api_url in API_URLS:
        try:
            response = requests.get(f'{api_url}{ip}')
            response.raise_for_status()
            data = response.json()
            if 'country_code' in data and 'city' in data:
                return data
        except requests.RequestException as e:
            print(f"Error fetching data from {api_url}: {e}")
    return None  # Return None if all APIs fail

def get_ips_from_prometheus(query, prometheus_url, metric_label):
    response = requests.get(f'{prometheus_url}/api/v1/query', params={'query': query})
    result = response.json()
    ips = [item['metric'][metric_label] for item in result['data']['result']]
    return ips

@app.route('/metrics')
def metrics():
    query = request.args.get('query')
    metric_label = request.args.get('metrics', query)

    if not query or not metric_label:
        abort(400, description="Missing required query parameters 'query' and/or 'metrics'")
    
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

    print(f"[Info] Metrics endpoint show at /metrics?query=<metrics>&metrics=<optional-label>")
    print(f"[Exp] http://localhost:{args.port}/metrics?query=fgVpnSslTunnelSrcIp")

    app.run(host='0.0.0.0', port=args.port, debug=args.debug)

