import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import start_http_server, Gauge, generate_latest
from pyrad.client import Client
from pyrad.packet import AccessRequest, AccessAccept
from pyrad.dictionary import Dictionary

# Configuration
RADIUS_SERVER = "10.1.41.68"  # FreeRADIUS server address
RADIUS_PORT = 18121  # Default RADIUS port
SECRET = b"adminsecret"  # Shared secret for RADIUS
METRICS_PORT = 8080  # Port for Prometheus to scrape metrics

# Prometheus metrics
total_access_requests = Gauge('freeradius_total_access_requests', 'Total number of access requests', ['server'])

# Function to fetch stats from FreeRADIUS
def fetch_radius_stats():
    # Create a client to communicate with FreeRADIUS
    client = Client(server=RADIUS_SERVER, secret=SECRET, dict="/etc/raddb/dictionary")
    client.AuthPort = RADIUS_PORT
    client.Timeout = 5  # Timeout for requests

    try:
        # Send an AccessRequest to get stats (you may need to customize this for your FreeRADIUS setup)
        req = client.CreateAuthPacket(code=AccessRequest, id=1)
        req.AddAttribute(1, b"testuser")  # Example: Add a user attribute (replace as needed)
        
        # Send the request and get the response
        response = client.SendPacket(req)

        # Check if the response is an AccessAccept (or handle other response codes as needed)
        if response.code == AccessAccept:
            # Here, we can process the response and extract relevant stats
            # For example, increment the metric with the response's data or attributes
            total_access_requests.labels(RADIUS_SERVER).inc(random.randint(1, 5))  # Incrementing randomly for demo
            print("Fetched stats from FreeRADIUS:", response)

        else:
            print(f"Unexpected response: {response.code}")
        
    except Exception as e:
        print(f"Error fetching stats from FreeRADIUS: {e}")

# HTTP server to serve Prometheus metrics
class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            # Serve the metrics page
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            # Generate the latest metrics
            self.wfile.write(generate_latest())
        else:
            self.send_response(404)
            self.end_headers()

# Function to collect FreeRADIUS metrics in a background thread
def collect_metrics():
    while True:
        fetch_radius_stats()
        threading.Event().wait(10)  # Wait for 10 seconds before the next fetch

# Start the HTTP server for Prometheus to scrape
def start_server():
    server_address = ('', METRICS_PORT)
    httpd = HTTPServer(server_address, MetricsHandler)
    print(f"Serving metrics on port {METRICS_PORT}...")
    httpd.serve_forever()

# Main entry point
if __name__ == "__main__":
    # Start the metrics collection in a separate thread
    metrics_thread = threading.Thread(target=collect_metrics)
    metrics_thread.daemon = True
    metrics_thread.start()

    # Start the HTTP server to serve the metrics
    start_server()

