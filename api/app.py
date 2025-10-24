from flask import Flask, request, jsonify
import requests
import threading
import time
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# === Tokens ===
tokens = {
    '4243859463': 'BY_MR-XKRVZSI2Y-RAFI',
    '4243859597': 'BY_MR-ZJRGDHOWS-RAFI',
    '4243859714': 'BY_MR-N2ZHBLPA1-RAFI',
    '4243859840': 'BY_MR-KMITSX5JJ-RAFI',
    '4243861270': 'BY_MR-DBO6CLFYH-RAFI'
}

# --- JWT Fetcher ---
def get_jwt_token(uid, password):
    url = f"https://api-store.top/jwt.php?id={uid}&pass={password}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('token'):
                return data['token']
            else:
                print(f"❌ Failed to get JWT token for UID {uid}: {data}")
        else:
            print(f"❌ HTTP Error {response.status_code} for UID {uid}")
    except Exception as e:
        print(f"⚠️ Error getting JWT token for UID {uid}: {e}")
    return None

# --- Encrypt functions ---
def Encrypt_ID(x):
    x = int(x)
    dec = [hex(i)[2:] for i in range(128, 256)]  # 80 -> ff
    xxx = [hex(i)[2:] for i in range(1, 64)]
    x = x / 128
    strx = int(x)
    y = (x - strx) * 128
    stry = int(y)
    z = (y - stry) * 128
    strz = int(z)
    n = (z - strz) * 128
    strn = int(n)
    return dec[strn] + dec[strz] + dec[stry] + xxx[strx]

def encrypt_api(plain_text):
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
    iv = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

# --- Send Like ---
def FOX_SendLike(token, target_id):
    url = "https://clientbp.ggblueshark.com/LikeProfile"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB50",
        "Host": "clientbp.common.ggbluefox.com",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "User-Agent": "Free%20Fire/2019117061 CFNetwork/1399 Darwin/22.1.0",
        "Connection": "keep-alive",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "Accept": "/"
    }
    data = bytes.fromhex(encrypt_api("08" + Encrypt_ID(target_id) + "1801"))
    response = requests.post(url, headers=headers, data=data, verify=False)
    return response.status_code == 200

def send_like_for_token(uid, password, target_id):
    token = get_jwt_token(uid, password)
    if token:
        return FOX_SendLike(token, target_id)
    return False

# --- Flask route ---
@app.route('/send_likes', methods=['GET'])
def send_likes():
    target_id = request.args.get('uid')
    if not target_id:
        return jsonify({"error": "uid (target) is required"}), 400
    try:
        target_id = int(target_id)
    except ValueError:
        return jsonify({"error": "uid must be an integer"}), 400

    results = {}
    threads = []

    for uid, password in tokens.items():
        thread = threading.Thread(
            target=lambda u=uid, p=password: results.update({u: send_like_for_token(u, p, target_id)})
        )
        threads.append(thread)
        thread.start()
        time.sleep(0.1)

    for thread in threads:
        thread.join()

    return jsonify(results)
