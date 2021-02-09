import jwt
import os
import random
import requests
import json
from datetime import datetime, timezone

def jwt_nonce():
    random_string = ''

    for _ in range(20):
        random_string += chr(random.randint(0, 127))

    return random_string

def generate_jwt():
    now = datetime.now(tzinfo=timezone.utc)
    exp = now + datetime.timedelta(seconds=60)
    test = jwt.encode({
        'iss': os.getenv('ADDONS_MOZILLA_USER'),
        'jti': jwt_nonce(),
        'iat': now.timestamp(),
        'exp': exp.timestamp()
    }, os.getenv('ADDONS_MOZILLA_SECRET'), algorithm='HS256')
    print(test)
    return test

def update_firefox_extensions():
    jwt_token = generate_jwt()
    headers = {
        'Authorization': f'JWT {jwt_token}'
    }
    res = requests.get("https://addons.mozilla.org/api/v5/addons/addon/3693247", headers=headers)
    print(json.loads(res.text))
