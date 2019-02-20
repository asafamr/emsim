from flask import Flask, jsonify
from flask import request
import os
from dotenv import load_dotenv

load_dotenv()

from emsim import preload, get_close_sents

app = Flask(__name__)

preload()


@app.route('/getsim', methods=['POST'])
def get_sim():
    data = request.json

    params = dict(dropout=0.5, n_trials=3, neg_dist=0.2, seed=123, n_per_page=10, page_num=0)

    for x in params:
        if x in data:
            params[x] = data[x]

    params['positives'] = data['positives']
    params['negatives'] = data['negatives']

    close_sents = get_close_sents(**params)

    return jsonify(message="Success",
                   data=close_sents), 200


if __name__ == '__main__':
    app.run(os.environ['HOST'], os.environ['PORT'])
