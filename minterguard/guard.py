"""
Script, which can be used as a tracking service for node.

There are two ways of using script:
    - manual
    - automatic (service)

It accepts at least one required argument --config (path to a config file)
If there are no more arguments provided, we treat it as automatic work mode.

Other manual arguments are --on or --off.
You can use it for manual setting your node on or off.
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

    def __init__(self, minterapi, pub_key, set_off_tx, missed_blocks=4):
        """
        Args:
            minterapi (MinterAPI): Minter API instance
            pub_key (str): Pub key of validator under control
            set_off_tx (str): Signed tx, which will be sent to chain
            missed_blocks (int): Amount of missed blocks, when validator
                                 should be offed
        """
        super().__init__()

        # Set attributes
        self.minterapi = minterapi
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
        # Check for required --config argument
        configargv = [a for a in sys.argv if '--config=' in a]
        if not configargv:
            raise Exception('Required --config argument is missing')

        # Parse config and check required data
        config = configparser.ConfigParser()
        config.read(configargv[0].split('=')[1])

        # If log file path is provided in config file, create file handler
        # and remove stream handler
        if 'SERVICE' in config.sections() and config['SERVICE'].get('log') and \
           config['SERVICE']['log'] != '':
            logger.removeHandler(shandler)
            fhandler = logging.FileHandler(config['SERVICE']['log'])
            fhandler.setLevel(logging.INFO)
            fhandler.setFormatter(formatter)
            logger.addHandler(fhandler)

        # Check sections
        for section in ['API', 'NODE']:
            if section not in config.sections():
                raise Exception('Section {} not found'.format(section))

        # Check sections attributes
        if config['API'].get('api_url') is None or \
           config['API']['api_url'] == '':
            raise Exception('"api_url" should be provided')

        if config['NODE'].get('pub_key') is None or \
           config['NODE']['pub_key'] == '':
            raise Exception('"pub_key" should be provided')

        if config['NODE'].get('set_off_tx') is None or \
           config['NODE']['set_off_tx'] == '':
            raise Exception('"set_off_tx" should be provided')

        # Now, when config is parsed and checked, we look for running mode
        # Create minterapi instance first
        minterapi = MinterAPI(config['API']['api_url'])

        # If there are only two arguments, this is automatic mode, we create
        # guard instance and run tracker.
        # Otherwise, we run actions, depending on manual arguments
        if len(sys.argv) == 2:
            kwargs = {
                'minterapi': minterapi,
                'pub_key': config['NODE']['pub_key'],
                'set_off_tx': config['NODE']['set_off_tx']
            }

            if config['NODE'].get('missed_blocks'):
                kwargs['missed_blocks'] = int(config['NODE']['missed_blocks'])

            # Create guard object and start tracking
            guard = Guard(**kwargs)
            guard.track()
        elif '--on' in sys.argv:
            # Check if set on tx exists
            if config['NODE'].get('set_on_tx') is None or \
               config['NODE']['set_on_tx'] == '':
                raise Exception('Please, set "set_on_tx" in config file')

            # If everything is ok, send tx
            response = minterapi.send_transaction(tx=config['NODE']['set_on_tx'])
            if response.get('error'):
                raise Exception(response['error'])

            logger.info('Set candidate ON transaction sent')
        elif '--off' in sys.argv:
            response = minterapi.send_transaction(tx=config['NODE']['set_off_tx'])
            if response.get('error'):
                raise Exception(response['error'])

            logger.info('Set candidate OFF transaction sent')
    except Exception as e:
        logger.error('{}: {}'.format(e.__class__.__name__, e.__str__()))
        sys.exit(1)
