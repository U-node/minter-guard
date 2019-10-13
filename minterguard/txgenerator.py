"""
This script generates SetCandidateOn and SetCandidateOff transactions for node.
SetCandidateOff transaction is provided for guard.py to set candidate off,
if it starts to miss blocks. SetCandidateOn transaction is provided personally
for you to set candidate on, when everything is ok.

Script accepts 2 required arguments:
 - config file with API_URL and PUB_KEY
 - needed tx for node (on/off)
"""

import sys
import getpass
import configparser

from mintersdk.minterapi import MinterAPI
from mintersdk.sdk.transactions import (MinterSetCandidateOnTx,
                                        MinterSetCandidateOffTx)
from mintersdk.sdk.wallet import MinterWallet


if __name__ == '__main__':
    # Process argv
    if len(sys.argv) != 3:
        print('Please, provide 2 required arguments: config file, action')
        sys.exit(1)

    # First arg is always config file
    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    # Try to get API urls
    try:
        api_urls = config['API']['API_URL'].split()
        if len(api_urls) == 0:
            raise
    except Exception:
        print('API_URL is not set in config file')
        sys.exit(1)

    # Try to get pub key
    try:
        pub_key = config['NODE']['PUB_KEY'].strip()
        if pub_key == '':
            raise
    except Exception:
        print('PUB_KEY is not set in config file')
        sys.exit(1)

    # Second arg is always action with node
    action = sys.argv[2]
    if action not in ['on', 'off']:
        print('Specify correct tx action (on/off)')
        sys.exit(1)

    # Get params from user
    seed = getpass.getpass('Provide seed phrase (password like input): ')

    # When all data seems to be set, create txs
    try:
        # Get APIs
        minterapis = [MinterAPI(api_url) for api_url in api_urls]

        # Get wallet
        wallet = MinterWallet.create(mnemonic=seed)

        # Get nonce from API
        nonce = None
        for minterapi in minterapis:
            try:
                nonce = minterapi.get_nonce(address=wallet['address'])
                break
            except Exception as e:
                print(e.__str__())

        if nonce is None:
            raise

        if action == 'on':
            # Set candidate on tx
            tx = MinterSetCandidateOnTx(
                pub_key=pub_key,
                nonce=nonce,
                gas_coin='BIP'
            )
            tx.sign(wallet['private_key'])
            tx_str = 'Set candidate ON tx: {}'.format(tx.signed_tx)
        elif action == 'off':
            # Set candidate off tx
            tx = MinterSetCandidateOffTx(
                pub_key=pub_key,
                nonce=nonce,
                gas_coin='BIP',
                gas_price=50
            )
            tx.sign(wallet['private_key'])
            tx_str = 'Set candidate OFF tx: {}'.format(tx.signed_tx)

        # Print collected data for user
        print('Public key: {}'.format(pub_key))
        print('From address: {}'.format(wallet['address']))
        print(tx_str)
    except Exception as e:
        print(e.__str__())
        sys.exit(1)
