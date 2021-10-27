from typing import Optional, List

from algosdk.v2client.algod import AlgodClient
from algosdk.kmd import KMDClient

import os
from dotenv import load_dotenv

from ..account import Account

load_dotenv()

BASE_SERVER=os.getenv('TESTNET_BASE_SERVER')
INDEXER_SERVER=os.getenv('TESTNET_INDEXER_SERVER')
# ALGOD_ADDRESS = "http://localhost:4001"
ALGOD_TOKEN = os.getenv('PURESTAKE_KEY')


def getAlgodClient() -> AlgodClient:
    algoClient = new algosdk.Algodv2(token, baseServer, port);
    return AlgodClient(ALGOD_TOKEN, BASE_SERVER)


KMD_ADDRESS = "http://localhost:4002"
KMD_TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def getKmdClient() -> KMDClient:
    return KMDClient(KMD_TOKEN, KMD_ADDRESS)


KMD_WALLET_NAME = "unencrypted-default-wallet"
KMD_WALLET_PASSWORD = ""

kmdAccounts: Optional[List[Account]] = None


def getGenesisAccounts() -> List[Account]:
    global kmdAccounts

    if kmdAccounts is None:
        kmd = getKmdClient()

        wallets = kmd.list_wallets()
        walletID = None
        for wallet in wallets:
            if wallet["name"] == KMD_WALLET_NAME:
                walletID = wallet["id"]
                break

        if walletID is None:
            raise Exception("Wallet not found: {}".format(KMD_WALLET_NAME))

        walletHandle = kmd.init_wallet_handle(walletID, KMD_WALLET_PASSWORD)

        try:
            addresses = kmd.list_keys(walletHandle)
            privateKeys = [
                kmd.export_key(walletHandle, KMD_WALLET_PASSWORD, addr)
                for addr in addresses
            ]
            kmdAccounts = [Account(sk) for sk in privateKeys]
        finally:
            kmd.release_wallet_handle(walletHandle)

    return kmdAccounts
