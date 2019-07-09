"""
This script generates SetCandidateOn and SetCandidateOff transactions for node.
SetCandidateOff transaction is provided for guard.py to set candidate off,
if it starts to miss blocks. SetCandidateOn transaction is provided personally
for you to set candidate on, when everything is ok.

Script accepts at least 2 required arguments:
 - config file with API_URL and PUB_KEY
 - needed tx for node (on/off)

Optional arguments:
 - --gas= (int), gas price for generated transaction (default is 50)
 - --write, if set script updates generated tx in provided config file
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
    if len(sys.argv) < 3:
        print('Please, provide at least 2 required arguments: config file, action')
        sys.exit(1)

    # First arg is always config file
    config = configparser.ConfigParser()
    config.read(sys.argv[1])

    # Try to get API url
    try:
        api_url = config['API']['api_url'].strip()
        if api_url == '':
            raise
    except Exception:
        print('"api_url" is not set in config file')
        sys.exit(1)

    # Try to get pub key
    try:
        pub_key = config['NODE']['pub_key'].strip()
        if pub_key == '':
            raise
    except Exception:
        print('"pub_key" is not set in config file')
        sys.exit(1)

    # Second arg is always action with node
    action = sys.argv[2]
    if action not in ['on', 'off']:
        print('Specify correct tx action (on/off)')
        sys.exit(1)

    # Get optional arguments
    write = False
    gas_price = 50
    for optarg in sys.argv[3:]:
        if '--gas=' in optarg:
            gas_price = int(optarg.split('=')[1])

        if '--write' in optarg:
            write = True

    # Get params from user
    seed = getpass.getpass('Provide seed phrase (password like input): ')

    # When all data seems to be set, create txs
    try:
        # Get API and wallet
        minterapi = MinterAPI(api_url)
        wallet = MinterWallet.create(mnemonic=seed)

        if action == 'on':
            # Set candidate on tx
            tx = MinterSetCandidateOnTx(
                pub_key=pub_key,
                nonce=minterapi.get_nonce(address=wallet['address']),
                gas_coin='BIP',
                gas_price=gas_price
            )
            tx.sign(wallet['private_key'])
            tx_str = 'Set candidate ON tx: {}'.format(tx.signed_tx)

            # Update config without saving
            config['NODE']['set_on_tx'] = tx.signed_tx
        elif action == 'off':
            # Set candidate off tx
            tx = MinterSetCandidateOffTx(
                pub_key=pub_key,
                nonce=minterapi.get_nonce(address=wallet['address']),
                gas_coin='BIP',
                gas_price=gas_price
            )
            tx.sign(wallet['private_key'])
            tx_str = 'Set candidate OFF tx: {}'.format(tx.signed_tx)

            # Update config without saving
            config['NODE']['set_off_tx'] = tx.signed_tx

        # Print collected data for user
        print('Public key: {}'.format(pub_key))
        print('From address: {}'.format(wallet['address']))
        print(tx_str)

        # If config file should be overriden
        if write:
            with open(sys.argv[1], 'w') as configfile:
                config.write(configfile)
    except Exception as e:
        print(e.__str__())
        sys.exit(1)
