import base64
import hashlib
import json
import random
import re
import subprocess
import time
import urllib.parse
from functools import partial
from os import path

import requests

requests.packages.urllib3.disable_warnings()

import execjs
import execjs._external_runtime as execjs_external_runtime

execjs_external_runtime.Popen = partial(subprocess.Popen, encoding="utf-8")

BASE_DIR = path.dirname(__file__)
ASSETS_DIR = path.join(BASE_DIR, "assets")
PROJECT_DIR = path.dirname(BASE_DIR)
LOCAL_NODE_MODULES_DIR = path.join(PROJECT_DIR, "node_modules")
FALLBACK_NODE_MODULES_DIR = path.join(path.dirname(PROJECT_DIR), "Douyin_Spider", "node_modules")
NODE_MODULES_DIR = LOCAL_NODE_MODULES_DIR if path.exists(LOCAL_NODE_MODULES_DIR) else FALLBACK_NODE_MODULES_DIR

dy_js = execjs.compile(open(path.join(ASSETS_DIR, "dy_ab.js"), "r", encoding="utf-8").read(), cwd=NODE_MODULES_DIR)


def trans_cookies(cookies_str):
    cookies = {}
    if not cookies_str:
        return cookies
    for i in cookies_str.split("; "):
        try:
            cookies[i.split("=")[0]] = "=".join(i.split("=")[1:])
        except Exception:
            continue
    return cookies


def generate_req_sign(e, priK):
    return dy_js.call("get_req_sign", e, priK)


def generate_a_bogus(query, data="", ua=None):
    return dy_js.call("get_ab", query, data, ua)


def generate_ree_key(prik):
    return dy_js.call("get_ree_key", prik)


def generate_bd_ticket_client_data(api, ticket, ts_sign, priK):
    timestamp = int(time.time())
    res_sign = f"ticket={ticket}&path={api}&timestamp={timestamp}"
    p = {
        "ts_sign": ts_sign,
        "req_content": "ticket,path,timestamp",
        "req_sign": generate_req_sign(res_sign, priK),
        "timestamp": timestamp,
    }
    p = json.dumps(p, ensure_ascii=False, separators=(",", ":"))
    return base64.urlsafe_b64encode(p.encode("utf-8")).decode("utf-8")


def generate_msToken(randomlength=107):
    random_str = ""
    base_str = "ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789="
    length = len(base_str) - 1
    for _ in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str


def generate_fake_webid(random_length=19):
    random_str = ""
    base_str = "0123456789"
    length = len(base_str) - 1
    for _ in range(random_length):
        random_str += base_str[random.randint(0, length)]
    return random_str


def generate_webid(auth=None, url=""):
    if url == "":
        url = "https://www.douyin.com/discover?modal_id=7376449060384935209"
    try:
        from .header import HeaderBuilder, HeaderType

        headers = HeaderBuilder.build(HeaderType.DOC)
        headers.set_header("cookie", auth.cookie_str if auth else "")
        headers.set_header("upgrade-insecure-requests", "1")
        response = requests.get(url, headers=headers.get(), verify=False)
        res_text = response.text
        return re.findall(r'\\"user_unique_id\\":\\"(.*?)\\"', res_text)[0]
    except Exception:
        return generate_fake_webid()


def generate_csrf_token(cookies_str):
    try:
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "cookie": cookies_str,
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.douyin.com/?recommend=1",
            "sec-ch-ua": '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "x-secsdk-csrf-request": "1",
            "x-secsdk-csrf-version": "1.2.22",
        }
        response = requests.head("https://www.douyin.com/service/2/abtest_config/", headers=headers, verify=False)
        token = response.headers["X-Ware-Csrf-Token"].split(",")
        return token[1], token[4]
    except Exception:
        return None, None


def generate_millisecond():
    return int(round(time.time() * 1000))


def splice_url(params):
    splice_url_str = ""
    for key, value in params.items():
        if value is None:
            value = ""
        splice_url_str += key + "=" + urllib.parse.quote(str(value)) + "&"
    return splice_url_str[:-1]
