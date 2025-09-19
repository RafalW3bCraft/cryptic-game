# TheFool - Mock LLM service (deterministic & safe)
# Author: RafalW3bCraft

from flask import Flask, request, jsonify
import hashlib
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=("safe","vuln","noisy"), default="safe")
args = parser.parse_args()
MODE = args.mode

app = Flask(__name__)

# deterministic canned responses for safe testing. No external model downloads.
RESPONSES = {
    'expose_secret': 'I cannot reveal secrets. [LAB-SAFE-RESPONSE] example_secret: REDACTED',
    'default': 'This is a safe mock response from TheFool lab. Use only in authorized labs.'
}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'time': time.time()})

@app.route('/v1/generate', methods=['POST'])
def generate():
    data = request.get_json(force=True) or {}
    prompt = data.get('prompt', '')
    # simple deterministic fingerprint to simulate varying responses
    h = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    # simple rules to simulate prompt-injection scenarios
    if 'secret' in prompt.lower() or 'api_key' in prompt.lower():
        resp = RESPONSES['expose_secret']
        flagged = True
    elif len(prompt) > 1000:
        resp = 'Prompt too long; truncated. [LAB-SAFE]'
        flagged = True
    else:
        # pseudo-random but deterministic
        idx = int(h, 16) % 3
        if idx == 0:
            resp = RESPONSES['default'] + ' (variant A)'
        elif idx == 1:
            resp = RESPONSES['default'] + ' (variant B)'
        else:
            resp = RESPONSES['default'] + ' (variant C)'
        flagged = False

    out = {
        'id': h[:12],
        'prompt_summary': prompt[:200],
        'response': resp,
        'flagged': flagged,
        'meta': {
            'length': len(prompt),
            'server_time': time.time()
        }
    }
    return jsonify(out)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
