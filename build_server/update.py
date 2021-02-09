import jwt
import os
import random
import requests
import json
from datetime import datetime, timedelta

def jwt_nonce():
    random_string = ''

    for _ in range(20):
        random_string += chr(random.randint(0, 127))

    return random_string

def generate_jwt():
    now = datetime.utcnow()
    exp = now + timedelta(seconds=60)
    test = jwt.encode({
        'iss': os.getenv('MOZILLA_ADDONS_USER'),
        'jti': jwt_nonce(),
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp())
    }, os.getenv('MOZILLA_ADDONS_SECRET'), algorithm='HS256')
    print(test)
    return test

def update_firefox_extensions():
    jwt_token = generate_jwt()
    headers = {
        'Authorization': f'JWT {jwt_token}'
    }
    res = requests.get("https://addons.mozilla.org/api/v5/addons/addon/3693247", headers=headers)
    print(json.loads(res.text))
