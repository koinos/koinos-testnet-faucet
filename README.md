## Koinos Testnet Faucet

### How To Install

Create a new virtual environment

`sudo apt install python3-venv`

`python3 -m venv ~/venv/faucet`

Activate the virtual environment:

`source ~/venv/faucet/bin/activate`

Install prereqs in virtual environment:

`pip install -r requirements.txt`

Copy the example config, then set desired parameters:

`cp example_config.yaml config.yaml`


### How To Run

Activate the virtual environment:

`source ~/venv/faucet/bin/activate`

Run the script:

`python faucet.py`
