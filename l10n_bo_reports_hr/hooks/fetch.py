import requests
import json
from odoo.exceptions import UserError

def useFetch(url, data, token=""):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'} if token != "" else {'Content-Type': 'application/json'}
    res=requests.post(url, data=data, headers=headers, verify=False)
    try:
        res = res.json()
        return res
    except json.decoder.JSONDecodeError:
        UserError(res)