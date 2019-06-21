"""
Script, which can be used as a tracking service for node.

It accepts only one argument, if it is --config argument. You should provide
path to config file to read params from.
Or you can provide all needed arguments in command line:
    --api-url=
    --pub-key=
    --set-off-tx=
    --missed-blocks= (this argument is optional and is 4 by default)
"""

import configparser
import logging
import sys
import time
from mintersdk.minterapi import MinterAPI
from mintersdk.sdk.transactions import MinterTx, MinterSetCandidateOffTx


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
shandler = logging.StreamHandler()
shandler.setLevel(logging.INFO)
shandler.setFormatter(formatter)
logger.addHandler(shandler)


class Guard(object):
    """
    Guard class
    """

    def __init__(self, api_url, pub_key, set_off_tx, missed_blocks=4):
        """
        Args:
            api_url (str): URL for Minter API
            pub_key (str): Pub key of validator under control
            set_off_tx (str): Signed tx, which will be sent to chain
            missed_blocks (int): Amount of missed blocks, when validator
                                 should be offed
        """
        super().__init__()

        # Set attributes
        self.minterapi = MinterAPI(api_url=api_url)
        self.pub_key = pub_key
        self.set_off_tx = set_off_tx
        self.missed_blocks = int(missed_blocks)

        # Check set off tx to be valid
        tx = MinterTx.from_raw(self.set_off_tx)
        if not isinstance(tx, MinterSetCandidateOffTx):
            raise Exception('Set off tx is not instance of MinterSetCandidateOffTx')

        nonce = self.minterapi.get_nonce(tx.from_mx)
        if tx.nonce != nonce:
            raise Exception('Set off tx has {} nonce, expected {}'.format(
                tx.nonce,
                nonce
            ))

    def track(self):
        """
        Tracking method
        """

        while True:
            try:
                # Get missed blocks
                response = self.minterapi.get_missed_blocks(
                    public_key=self.pub_key
                )

                # Raise exception on non 404 error (Validator not found)
                if response.get('error'):
                    if response['error']['code'] != 404:
                        raise Exception(response['error'])
                    else:
                        time.sleep(1)
                        continue

                # If response is ok, get missed blocks count
                mb = int(response['result']['missed_blocks_count'])

                # If missed blocks is greater than limit, set candidate off
                if mb >= self.missed_blocks:
                    # Send set candidate off transaction
                    response = self.minterapi.send_transaction(
                        tx=self.set_off_tx
                    )

                    if response.get('error'):
                        raise Exception(response['error'])

                    # Write log info message abount setting candidate off
                    logger.info('Set candidate off. Blocks missed: {}'.format(mb))
            except Exception as e:
                logger.error('{}: {}'.format(
                    e.__class__.__name__,
                    e.__str__()
                ))

            # Wait a second between each loop
            time.sleep(1)


if __name__ == '__main__':
    try:
        # Future kwargs for Guard(**kwargs)
        kwargs = {}

        # Process sys argv and generate kwargs for Guard(**kwargs)
        if len(sys.argv) == 2 and '--config=' in sys.argv[1]:
            config = configparser.ConfigParser()
            config.read(sys.argv[1].split('=')[1])

            # If log file path is provided in config file, create file handler
            # and remove stream handler
            if 'SERVICE' in config.sections() and config['SERVICE'].get('LOG') and \
               config['SERVICE']['LOG'] != '':
                logger.removeHandler(shandler)
                fhandler = logging.FileHandler(config['SERVICE']['LOG'])
                fhandler.setLevel(logging.INFO)
                fhandler.setFormatter(formatter)
                logger.addHandler(fhandler)

            # Check sections
            for section in ['API', 'NODE']:
                if section not in config.sections():
                    raise Exception('Section {} not found'.format(section))

            # Check sections attributes
            if config['API'].get('API_URL') is None or \
               config['API']['API_URL'] == '':
                raise Exception('API_URL should be provided')

            if config['NODE'].get('PUB_KEY') is None or \
               config['NODE']['PUB_KEY'] == '':
                raise Exception('PUB_KEY should be provided')

            if config['NODE'].get('SET_OFF_TX') is None or \
               config['NODE']['SET_OFF_TX'] == '':
                raise Exception('SET_OFF_TX should be provided')

            # Set kwargs
            kwargs.update({
                'api_url': config['API']['API_URL'],
                'pub_key': config['NODE']['PUB_KEY'],
                'set_off_tx': config['NODE']['SET_OFF_TX']
            })

            if config['NODE'].get('MISSED_BLOCKS'):
                kwargs['missed_blocks'] = int(config['NODE']['MISSED_BLOCKS'])
        else:
            for argv in sys.argv:
                kv = argv.split('=')
                if kv[0][:2] == '--':
                    k = kv[0].replace('--', '').replace('-', '_')
                    v = kv[1]
                    kwargs[k] = v

        # Create guard object and start tracking
        guard = Guard(**kwargs)
        guard.track()
    except Exception as e:
        logger.error('{}: {}'.format(e.__class__.__name__, e.__str__()))
        sys.exit(1)
