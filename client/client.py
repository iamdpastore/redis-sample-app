import requests
import random
import os

# URL dell'applicazione Flask
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:10000/')

# Candidati disponibili per il voto
candidates = ['Game of Thrones', 'Stranger Things', 'The Walking Dead']

def generate_random_ip():
    return '.'.join(str(random.randint(0, 255)) for _ in range(4))

def vote(ip):
    headers = {
        'X-Forwarded-For': ip
    }
    candidate = random.choice(candidates)
    data = {'candidate': candidate}
    response = requests.post(f'{BASE_URL}/vote', data=data, headers=headers)
    if response.status_code == 200:
        print(f'Vote from {ip} for {candidate} successful.')
    else:
        print(f'Vote from {ip} failed: {response.text}')

if __name__ == '__main__':
    num_votes = 100  # Numero di voti da simulare
    for _ in range(num_votes):
        ip = generate_random_ip()
        vote(ip)
