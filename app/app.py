from flask import Flask, render_template, request, redirect, url_for, jsonify
import redis
import os
import folium
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from folium.plugins import HeatMap

app = Flask(__name__)
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
r = redis.Redis.from_url(redis_url)
geolocator = Nominatim(user_agent="vote_manager")

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers['X-Forwarded-For'].split(',')[0]
    else:
        ip = request.remote_addr
    return ip

def get_location(ip, retries=3):
    try:
        location = geolocator.geocode(ip)
        if location:
            print(f"Location for IP {ip}: {location.latitude}, {location.longitude}")
            return (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        if retries > 0:
            time.sleep(1)  # add a delay before retrying
            return get_location(ip, retries - 1)
        else:
            print(f"Geocoding error for IP {ip}: {e}")
    return None

@app.route('/')
def index():
    votes = {k.decode('utf-8'): int(v) for k, v in r.hgetall('votes').items()}
    return render_template('index.html', votes=votes)

@app.route('/vote', methods=['POST'])
def vote():
    candidate = request.form['candidate']
    ip = get_client_ip()

    # Check if the IP has already voted
    if r.sismember('voted_ips', ip):
        return "You have already voted.", 403
    
    r.hincrby('votes', candidate, 1)
    r.sadd('voted_ips', ip)

    location = get_location(ip)
    if location:
        r.geoadd('locations', (location[1], location[0], ip))

    return redirect(url_for('index'))

@app.route('/results')
def results():
    votes = {k.decode('utf-8'): int(v) for k, v in r.hgetall('votes').items()}
    return jsonify(votes)

@app.route('/clear', methods=['POST'])
def clear():
    r.flushdb()
    return redirect(url_for('index'))

@app.route('/map')
def map_view():
    m = folium.Map(location=[0, 0], zoom_start=2)
    locations = r.georadius('locations', 0, 0, 10000000, unit='km', withcoord=True)
    heat_data = [(loc[1][1], loc[1][0]) for loc in locations]
    print(f"Heat data: {heat_data}")  # Log the heat data for debug

    if heat_data:
        HeatMap(heat_data).add_to(m)
    else:
        print("No data to display on the map")
        
    return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000) # Default port for Render Web Services
