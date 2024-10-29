import re
import dbm
import json
import requests
import argparse
import subprocess
from datetime import datetime
from decimal import *

import yaml
import base58
import base64

from bottle import run, post
from bottle import default_app, request, response

app = default_app()

class Blockchain:
    request_id = 0

    def __init__(self):
        self.balance_re = re.compile(f"((\d+(\.\d*)?)|(\.\d+)) {app.config['token_symbol']}")
        return

    def invoke_wallet(self, command, wallet=False):
        call = [app.config["wallet_bin"], "--rpc", app.config["rpc_endpoint"]]
        if wallet:
            call.extend(["-x", f"open {app.config['wallet_file']} {app.config['wallet_password']}"])
        call.extend(["-x", f"register_token tkoin {app.config['token_address']}"])
        call.extend(["-x", command])
        output = subprocess.check_output(call, encoding='ascii')
        print(output)
        return output

    def transfer(self, address, amount):
        d_amount = satoshi_to_decimal(amount, 8)
        self.invoke_wallet(f"tkoin.transfer {address} {d_amount}", wallet=True)
        return

    def get_balance(self, address):
        balance_return = self.invoke_wallet(f"tkoin.balance_of {address}", wallet=False)
        m = self.balance_re.search(balance_return)
        if m:
           d = Decimal(m.group(1))
           return decimal_to_satoshi(d, 8)
        return 0

def check_key(name, password):
    return True # TODO: Add authentication

def update_timestamp(id):
    app.db[id] = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S.%f")

def fetch_timestamp(id):
    data = app.db[id]
    return datetime.strptime(data.decode("ascii"), "%Y-%m-%d %H:%M:%S.%f")

# Check the given identifier, update database, return result
def check_identifier(id):
    # If the id is not in the database, add it
    if id not in app.db:
        update_timestamp(id)
        return (True, None)

    id_time = fetch_timestamp(id)
    dt = datetime.now() - id_time
    dseconds = dt.total_seconds()
    if dseconds < app.config["rate_seconds"]:
        difference = max(int(app.config["rate_seconds"] - dseconds), 1)
        return (False, f"Cannot receive {app.config['token_symbol']} for {(difference/60.0):.1f} more minutes.")
    update_timestamp(id)
    return (True, None)

# Calculate the payout amount, submit the transaction
def pay_address(address, balance):
    amount = min(int(balance*app.config["k"]), app.config["koin_payout"])
    app.chain.transfer(address, amount)
    return amount

def decimal_to_satoshi(balance, precision):
    return int(balance * (10 ** precision))

def satoshi_to_decimal(balance, precision):
    return balance / (10 ** precision)

@post('/balance')
def balance():
    data = request.json
    try:
        if data is None: raise ValueError
        try:
            address = data['address']
        except(TypeError, KeyError):
            raise ValueError
    except ValueError:
        response.headers['Content-Type'] = 'application/json'
        response.status = 400
        return json.dumps({"message": "Input error."})

    # Ensure the address has a valid format
    try:
        base58.b58decode(address)
    except ValueError:
        response.status = 400
        return json.dumps({"message": "Invalid address format."})
    
    # Execute the payout
    balance = app.chain.get_balance(address)
    s_balance = "{:8f}".format(balance / 100000000.0)

    response.status = 202
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({"message": f"Balance at address {address} is {s_balance} {app.config['token_symbol']}."})

@post('/request_koin')
def request_koin():
    data = request.json
    try:
        if data is None: raise ValueError
        try:
            id = data['id']
            address = data['address']
        except(TypeError, KeyError):
            raise ValueError
    except ValueError:
        response.headers['Content-Type'] = 'application/json'
        response.status = 400
        return json.dumps({"message": "Input error."})

    # Ensure the address has a valid format
    try:
        base58.b58decode(address)
    except ValueError:
        response.status = 400
        return json.dumps({"message": "Invalid address format."})

    # Check the identifier against the database
    id_result = check_identifier(id)
    if not id_result[0]:
        response.status = 406
        response.headers['Content-Type'] = 'application/json'
        return json.dumps({"message": id_result[1]})

    # Execute the payout
    balance = app.chain.get_balance(app.config["wallet_address"])
    amount = pay_address(address, balance)
    s_amount = "{:8f}".format(amount / 100000000.0)

    response.status = 202
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({"message": f"Transferring {s_amount} {app.config['token_symbol']} to address {address}."})

def main():
    parser = argparse.ArgumentParser(description='Koinos testnet faucet server.')
    parser.add_argument('--config', '-c', type=str, default="config.yaml", help="configuration yaml file")
    parser.add_argument('--database', '-d', type=str, default="faucet.db", help="database file")
    args = parser.parse_args()

    # Load the config
    with open(args.config, "r") as f:
        app.config = yaml.load(f.read(), Loader=yaml.SafeLoader)

    app.chain = Blockchain()
    with dbm.open(args.database, "c") as db:
        app.db = db
        run(app, server=app.config["server_type"],
            host=app.config["host"], port=app.config["port"])
    return

if __name__ == "__main__":
    main()
