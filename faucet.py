import re
import dbm
import json
import argparse
import subprocess
from datetime import datetime

import yaml
import base58

from bottle import run, post
from bottle import default_app, request, response

app = default_app()
re_address = re.compile("0x[0-9a-fA-F]{40}$")

class Blockchain:
    def __init__(self):
        self.balance = 0
        self.k = .00001
        self.update_balance()
        return

    def transfer(self, address, amount):
        transaction = create_transaction(address, amount)
        call = [app.config["signing_tool_bin"], "-w", "-k", app.config["private_key_file"]]
        rpc_call = subprocess.check_output(call)
        # TODO: Make actual rpc call here
        return

    def update_balance(self):
        # TODO: Fetch actual balance from chain
        self.balance = 10000000000 #(1000.0000000)
        return

def create_transaction(to_address, amount):
    args = create_args(app.config["wallet_address"], to_address, amount)
    transaction = {'id': 'z11', 'active_data': {'resource_limit': 0,
    'nonce': 0, 'operations': [{'type': 'koinos::protocol::call_contract_operation',
    'value': {'contract_id': app.config["contract_id"], 'entry_point': app.config["entry_point"], 'args': args, 'extensions': {}}}]},
    'passive_data': {}, 'signature_data': ''}
    return transaction

def create_args(from_address, to_address, amount):
    from_bytes = address_to_bytes(from_address)
    to_bytes = address_to_bytes(to_address)
    amt_bytes = amount.to_bytes(8, 'big')
    return to_base58(from_bytes + to_bytes + amt_bytes)

def to_base58(b):
    s = base58.b58encode(b)
    return "z" + "".join(chr(x) for x in s)

# address in form 0x...
def address_to_bytes(address):
    print(address)
    return b'\x14' + bytes.fromhex(address[2:])

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
        return (False, f"Cannot receive funds for {difference} more seconds.")
    update_timestamp(id)
    return (True, None)

# Calculate the payout amount, submit the transaction
def pay_address(address):
    amount = min(int(app.chain.balance*app.config["k"]), app.config["koin_payout"])
    app.chain.transfer(address, amount)
    app.chain.balance -= amount
    return amount

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
    if re_address.match(address) is None:
        response.status = 400
        return json.dumps({"message": "Invalid address format."})

    # Check the identifier against the database
    id_result = check_identifier(id)
    if not id_result[0]:
        response.status = 406
        response.headers['Content-Type'] = 'application/json'
        return json.dumps({"message": id_result[1]})

    # Execute the payout
    amount = pay_address(address)
    s_amount = "{:7f}".format(amount / 10000000.0)

    response.status = 202
    response.headers['Content-Type'] = 'application/json'
    return json.dumps({"message": f"Transferring {s_amount} KOIN to address {address}."})

def main():
    parser = argparse.ArgumentParser(description='Koinos testnet faucet server.')
    parser.add_argument('--config', '-c', type=str, default="config.yaml", help="configuration yaml file")
    parser.add_argument('--database', '-d', type=str, default="faucet.db", help="database file")
    args = parser.parse_args()

    # Load the config
    with open(args.config, "r") as f:
        app.config = yaml.load(f.read(), Loader=yaml.SafeLoader)

    # Sanitize database filename since dbm expects it without extension for some reason
    db_fname = args.database
    if args.database.endswith(".db"):
        db_fname = db_fname[:-3]

    app.chain = Blockchain()
    with dbm.open(db_fname, "c") as db:
        app.db = db
        run(app, server=app.config["server_type"], 
            host=app.config["host"], port=app.config["port"])
    return

if __name__ == "__main__":
    main()
