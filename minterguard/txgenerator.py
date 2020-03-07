"""
This script generates SetCandidateOn and SetCandidateOff transactions for node.
SetCandidateOff transaction is provided for guard.py to set candidate off,
if it starts to miss blocks. SetCandidateOn transaction is provided personally
for you to set candidate on, when everything is ok.

Script accepts 2 required arguments:
 - config file with API_URL and PUB_KEY
 - needed tx for node (on/off)
Script accepts 1 non-required argument:
 - multi set script to multisignature mode 
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
    if len(sys.argv) < 3 or len(sys.argv) > 4:
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

    multisig = False
    try:
        if sys.argv[3] == "multi":
            multisig = True
    except:
        pass
    # Get params from user
    if multisig:
        seeds = []
        count = int(input('Provide count of seed phrases: '))
        multi_addr = input('Provide address multisig: ')
        for i in range(count):
            seeds.append(getpass.getpass('Provide seed phrase (password like input): '))

    else:
        seed = getpass.getpass('Provide seed phrase (password like input): ')

    # When all data seems to be set, create txs
    try:
        # Get APIs
        minterapis = [MinterAPI(api_url) for api_url in api_urls]

        # Get wallet
        if multisig:
            privates_key = []
            for seed in seeds:
                privates_key.append(MinterWallet.create(mnemonic=seed)["private_key"])
        else:    
            wallet = MinterWallet.create(mnemonic=seed)

        # Get nonce from API
        nonce = None
        for minterapi in minterapis:
            try:
                if not multisig:
                    nonce = minterapi.get_nonce(address=wallet['address'])
                else:
                    nonce = minterapi.get_nonce(address=multi_addr)
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
            if multisig:
                tx.sign(private_key=privates_key,ms_address=multi_addr)
            else:
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
            if multisig:
                tx.sign(private_key=privates_key,ms_address=multi_addr)
            else:
                tx.sign(wallet['private_key'])
            tx_str = 'Set candidate OFF tx: {}'.format(tx.signed_tx)

        # Print collected data for user
        print('Public key: {}'.format(pub_key))
        if multisig:
            print('From address: {}'.format(multi_addr))
        else:
            print('From address: {}'.format(wallet['address']))
        print(tx_str)
    except Exception as e:
        print(e.__str__())
        sys.exit(1)

