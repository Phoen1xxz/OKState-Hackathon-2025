import os
import json

import json
import os

users_file = "userVals.json"

def get_metadata(user_id, param):
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            data = json.load(f)
            return data.get(user_id, {}).get(param)
    return None

def set_metadata(user_id, param, var):
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data.setdefault(user_id, {})

    data[user_id][param] = var

    with open(users_file, "w") as f:
        json.dump(data, f, indent=4)



