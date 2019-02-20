import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

data = {'positives': ['john is a the founder of microsoft'], 'negatives': ['i started the engine'],
        # these are optional:
        'dropout': 0.5,
        'n_trials': 3,
        'neg_dist': 0.2,
        'seed': 123,
        'n_per_page': 10,
        'page_num': 0
        }
r=requests.post('http://%s:%s/getsim' % (os.environ['HOST'], os.environ['PORT']),headers={'Content-Type': 'application/json' }, data=json.dumps(data))
print(r.json()['data'])
