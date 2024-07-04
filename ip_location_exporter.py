import requests, argparse
from flask import Flask, request, Response, abort, render_template_string, jsonify
from prometheus_client import CollectorRegistry, Gauge, generate_latest, push_to_gateway, delete_from_gateway

app = Flask(__name__)

API_CONFIGS = [
    {
        'url': 'https://ipinfo.io/',
        'key_name': '',
        'key_value': '',
        'fields': {
            'ip': 'ip',
            'country_code': 'country',
            'city': 'city',
            'loc': 'loc'  # loc contains both latitude and longitude
        }
    },
    {
        'url': 'https://www.iplocate.io/api/lookup/',
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

@app.route('/')
def home():
    return render_template_string('''
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>IP-Location Exporter</title>
      <style>body {
        font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,Noto Sans,Liberation Sans,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol,Noto Color Emoji;
        margin: 0;
      }
      header {
        background-color: #e6522c;
        color: #fff;
        font-size: 1rem;
        padding: 1rem;
      }
      main {
        padding: 1rem;
      }
      label {
        display: inline-block;
        width: 3.5em;
      }
      </style>
    </head>
    <body>
      <header>
        <h1>IP-Location Exporter</h1>
      </header>
      <main>
        <h2>Prometheus Exporter for IP-Locaton APIs</h2>
        <div>Version: (version=0.26.0, branch=HEAD, revision=44f8732988e726bad3f13d5779f1da7705178642)</div>
        <br>
        <form action="/metrics" method="get">
          <label>Query:</label>&nbsp;<input type="text" name="target" placeholder="Enter PromQL metrics contain IPs" value=""><br>
          <label>Metrics:</label>&nbsp;<input type="text" name="metrics" placeholder="Default equal to metric name" value=""><br>
          <input type="submit" value="Submit">
        </form>
        <br>
        <h3>Lookup IP</h3>
        <form action="/lookup" method="get">
          <label>IP:</label>&nbsp;<input type="text" name="ip" placeholder="Enter IP address" value=""><br>
          <input type="submit" value="Lookup">
        </form>
      </main>
    </body>
    </html>
    ''')

@app.route('/metrics')
def metrics():
    target = request.args.get('target')
    metric_label = request.args.get('metrics', target)
    if metric_label == '':
        metric_label = target

    if not target:
        abort(400, description="Missing required parameter 'target'")

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

    if pushgateway_url:
        delete_from_gateway(pushgateway_url, instance='ip_location_exporter:'+str(args.port))
        push_to_gateway(pushgateway_url, job=target, instance="ip_location_exporter:"+str(args.port), registry=registry)

    return Response(generate_latest(registry), mimetype='text/plain')

@app.route('/lookup')
def lookup():
    ip = request.args.get('ip')
    if not ip:
        abort(400, description="Missing required parameter 'ip'")

    location = get_location(ip)
    if location:
        return jsonify(location)
    else:
        return jsonify({"error": "Failed to get location for IP"}), 400

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IP Location Exporter')
    parser.add_argument('-u', '--prometheus_url', default='http://prometheus:9090', help='URL of Prometheus server (default: http://prometheus:9090)')
    parser.add_argument('-p', '--port', default=9012, help='Port to run the exporter on (default: 9012)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--push-gateway', help='Send metrics to Pushgateway server (e.g: http://pushgateway:9091)')

    args = parser.parse_args()
    prometheus_url = args.prometheus_url
    pushgateway_url = args.push_gateway

    print(f"[Info] Metrics endpoint available at /metrics?target=<query>&metrics=<optional-label>")
    print(f"[Example] http://localhost:{args.port}/metrics?target=fgVpnSslTunnelSrcIp")

    app.run(host='0.0.0.0', port=args.port, debug=args.debug)
