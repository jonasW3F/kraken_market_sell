#!/usr/bin/python3

import time
from time import sleep 
import os
import requests
import urllib.parse
import hashlib
import hmac
import base64

# Read Kraken API key and secret stored in environment variables
api_url = "https://api.kraken.com"
api_key = os.environ['API_KEY_KRAKEN']
api_sec = os.environ['API_SEC_KRAKEN']

asset = 'KSM'
fiat = 'EUR'
pair = asset + fiat


def get_kraken_signature(urlpath, data, secret):

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def makeRequest(uri_path, data, api_key, api_sec):
    headers = {}
    headers['API-Key'] = api_key
    # get_kraken_signature() as defined in the 'Authentication' section
    headers['API-Sign'] = get_kraken_signature(uri_path, data, api_sec)             
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

# Construct the request and print the result
token_balance_request = makeRequest('/0/private/TradeBalance', {
    "nonce": str(int(1000*time.time())),
    "asset": asset
}, api_key, api_sec)


dot_ticker = requests.get('https://api.kraken.com/0/public/Ticker?pair=DOTEUR')
dot_price = dot_ticker.json()['result']['DOTEUR']['a'][0]

ksm_ticker = requests.get('https://api.kraken.com/0/public/Ticker?pair=KSMEUR')
ksm_price = ksm_ticker.json()['result']['KSMEUR']['a'][0]

balances = makeRequest('/0/private/Balance', {
    "nonce": str(int(1000*time.time()))
}, api_key, api_sec)

dot_balance = float(balances.json()['result']['DOT'])
ksm_balance = float(balances.json()['result']['KSM'])

print('KSM is currently trading at ' + str(ksm_price) + '.' + ' You currently have ' + str(ksm_balance) + ' available')
print('DOT is currently trading at ' + str(dot_price) + '.' + ' You currently have ' + str(dot_balance) + ' available')


while True:
    try:
        sell_asset = int(input('Which asset do you want to trade? Insert 1 for KSM and 2 for DOT '))
        if (sell_asset == 1 or sell_asset == 2):
            break
        raise Exception()
    except:
        print('Please input valid option')

while True:
    try:
        sell_amount = float(input('And how much of the token do you want to sell? '))
        if (sell_asset == 1):
            if(sell_amount <= ksm_balance and sell_amount >= 0.02):
                pair = 'KSM' + fiat
                break
        else:
            if(sell_amount <= dot_balance and sell_amount >= 0.02):
                pair = 'DOT' + fiat
                break
        raise Exception()
    except:
        print('You cannot sell more than you have or the minimum sell amount is 0.02.')


sell = makeRequest('/0/private/AddOrder', {
    "nonce": str(int(1000*time.time())),
    "ordertype": "market",
    "type": "sell",
    "volume": str(sell_amount),
    "pair": pair,
}, api_key, api_sec)

tx_id = sell.json()['result']['txid'][0]

# To give Kraken backend time
sleep(1)

trade = makeRequest('/0/private/QueryOrders', {
    "nonce": str(int(1000*time.time())),
    "txid": tx_id,
    "trades": False
}, api_key, api_sec)

profit = trade.json()['result'][tx_id]['cost']
fee = trade.json()['result'][tx_id]['fee']
price = trade.json()['result'][tx_id]['price']

print('Your trade was successful. You sold at ' + price + ' ' + fiat + ' and had a profit of ' + profit + ' ' + fiat + '. You paid ' + fee + ' ' + fiat +  ' in fees.')