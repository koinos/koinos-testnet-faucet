# Deprecated

This repository contains the legacy Python testnet faucet server and is no longer used by the current public Koinos testnet.

The current public testnet faucet is the Telegram faucet maintained in:

https://github.com/koinos/koinos-testnet/tree/main/faucet-bot

Current faucet user and operator documentation:

https://github.com/koinos/koinos-testnet/blob/main/docs/faucet.md

This repository is retained for historical reference only.

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
