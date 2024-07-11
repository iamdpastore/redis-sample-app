from flask import Flask, render_template, request, redirect, url_for, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host='red-cq803u6ehbks7397u18g', port=6379, db=0)

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers['X-Forwarded-For'].split(',')[0]
    else:
        ip = request.remote_addr
    return ip

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
    return redirect(url_for('index'))

@app.route('/results')
def results():
    votes = {k.decode('utf-8'): int(v) for k, v in r.hgetall('votes').items()}
    return jsonify(votes)

if __name__ == '__main__':
    app.run(debug=True)
