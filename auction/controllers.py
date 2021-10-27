from time import time, sleep

from algosdk import account, encoding
from algosdk.logic import get_application_address
from auction.operations import createAuctionApp, setupAuctionApp, placeBid, closeAuction
from auction.util import (
    getBalances,
    getAppGlobalState,
    getLastBlockTimestamp,
    printCreatedAsset,
    printAssetHolding
)
from auction.testing.setup import getAlgodClient
from auction.testing.resources import (
    getTemporaryAccount,
    optInToAsset,
    createDummyAsset,
)
def createNonFungibleToken():
    sender = request.body.sender
    amount = request.body.amount
  # For ease of reference, add account public and private keys to
  # an accounts dict.
  print("--------------------------------------------")
  print("Creating account...")
  accounts = {}
  m = create_account()
  accounts[1] = {}
  accounts[1]['pk'] = mnemonic.to_public_key(m)
  accounts[1]['sk'] = mnemonic.to_private_key(m)


client = getAlgodClient()
  print("--------------------------------------------")
  print("Creating Asset...")
  # CREATE ASSET
  # Get network params for transactions before every transaction.
  params = client.suggested_params()
  # comment these two lines if you want to use suggested params
  params.fee = 1000
  params.flat_fee = True
    
  # JSON file
  f = open ('aliceNFTmetadata.json', "r")
  
  # Reading from file
  metadataJSON = json.loads(f.read())
  metadataStr = json.dumps(metadataJSON)

  hash = hashlib.new("sha512_256")
  hash.update(b"arc0003/amj")
  hash.update(metadataStr.encode("utf-8"))
  json_metadata_hash = hash.digest()


  # Account 1 creates an asset called latinum and
  # sets Account 1 as the manager, reserve, freeze, and clawback address.
  # Asset Creation transaction
  txn = AssetConfigTxn(
      sender=sender.address,
      sp=params,
      total=1,
      default_frozen=False,
      unit_name="ALICE001",
      asset_name="Alice's Artwork 001",
      manager=accounts[1]['pk'],
      reserve=None,
      freeze=None,
      clawback=None,
      strict_empty_address_check=False,
      url="https://path/to/my/asset/details", 
      metadata_hash=json_metadata_hash,
      decimals=0)

  # Sign with secret key of creator
  stxn = txn.sign(sender.sk)

  # Send the transaction to the network and retrieve the txid.
  txid = client.send_transaction(stxn)
  print("Asset Creation Transaction ID: {}".format(txid))

  # Wait for the transaction to be confirmed
  wait_for_confirmation(client,txid,4)

  try:
      # Pull account info for the creator
      # account_info = client.account_info(accounts[1]['pk'])
      # get asset_id from tx
      # Get the new asset's information from the creator account
      ptx = client.pending_transaction_info(txid)
      asset_id = ptx["asset-index"]
      printCreatedAsset(client, sender.address, asset_id)
      printAssetHolding(client, sender.address, asset_id)
  except Exception as e:
      print(e)

  print("--------------------------------------------")
  print("You have successfully created your own Non-fungible token! For the purpose of the demo, we will now delete the asset.")
  print("Deleting Asset...")

  # Asset destroy transaction
  txn = AssetConfigTxn(
      sender=sender.address,
      sp=params,
      index=asset_id,
      strict_empty_address_check=False
      )

  # Sign with secret key of creator
  stxn = txn.sign(sender.sk)
  # Send the transaction to the network and retrieve the txid.
  txid = client.send_transaction(stxn)
  print("Asset Destroy Transaction ID: {}".format(txid))
  # Wait for the transaction to be confirmed
  wait_for_confirmation(client, txid, 4)

  # Asset was deleted.
  try:
      printAssetHolding(client, sender.address, asset_id)
      printCreatedAsset(client, sender.address, asset_id)
      print("Asset is deleted.")
  except Exception as e:
      print(e)
  
  print("--------------------------------------------")
  print("Sending closeout transaction back to the testnet dispenser...")
  closeout_account(sender.address, sender.sk, client)

# utility for waiting on a transaction confirmation

def auction():
    client = getAlgodClient()
    creator = request.body.creator
    seller = request.body.seller
    bidder = request.body.bidder
    auction_time = request.body.auction_time

    startTime = int(time()) + 10  # start time is 10 seconds in the future
    endTime = startTime + auction_time  # end time is 30 seconds after start
    reserve = request.body.reserve # 1_000_000  # 1 Algo
    increment = 100_000  # 0.1 Algo
    
    assetID = request.body.assetID
    # creating auction smart contract that lasts 30 seconds to auction off NFT...
    print(
        "Alice is creating auction smart contract that lasts 30 seconds to auction off NFT..."
    )
    appID = createAuctionApp(
        client=client,
        sender=creator,
        seller=seller.getAddress(),
        nftID=nftID,
        startTime=startTime,
        endTime=endTime,
        reserve=reserve,
        minBidIncrement=increment,
    )
    # setting up and funding NFT auction...
    print("Alice is setting up and funding NFT auction...")
    setupAuctionApp(
        client=client,
        appID=appID,
        funder=creator,
        nftHolder=seller,
        nftID=nftID,
        nftAmount=nftAmount,
    )

    sellerAlgosBefore = getBalances(client, seller.getAddress())[0]
    print("Alice's algo balance: ", sellerAlgosBefore, " algos")

    _, lastRoundTime = getLastBlockTimestamp(client)
    if lastRoundTime < startTime + 5:
        sleep(startTime + 5 - lastRoundTime)
    actualAppBalancesBefore = getBalances(client, get_application_address(appID))
    print("The smart contract now holds the following:", actualAppBalancesBefore)
    bidAmount = reserve
    bidderAlgosBefore = getBalances(client, bidder.getAddress())[0]
    print("Carla wants to bid on NFT, her algo balance: ", bidderAlgosBefore, " algos")
    print("Carla is placing bid for: ", bidAmount, " algos")

    placeBid(client=client, appID=appID, bidder=bidder, bidAmount=bidAmount)

    print("Carla is opting into NFT with id:", nftID)

    optInToAsset(client, nftID, bidder)

    _, lastRoundTime = getLastBlockTimestamp(client)
    if lastRoundTime < endTime + 5:
        sleep(endTime + 5 - lastRoundTime)

    print("Alice is closing out the auction....")
    closeAuction(client, appID, seller)

    actualAppBalances = getBalances(client, get_application_address(appID))
    expectedAppBalances = {0: 0}
    print("The smart contract now holds the following:", actualAppBalances)
    assert actualAppBalances == expectedAppBalances

    bidderNftBalance = getBalances(client, bidder.getAddress())[nftID]

    print("Carla's NFT balance:", bidderNftBalance, " for NFT ID: ", nftID)

    assert bidderNftBalance == nftAmount

    actualSellerBalances = getBalances(client, seller.getAddress())
    print("Alice's balances after auction: ", actualSellerBalances, " Algos")
    actualBidderBalances = getBalances(client, bidder.getAddress())
    print("Carla's balances after auction: ", actualBidderBalances, " Algos")
    assert len(actualSellerBalances) == 2
    # seller should receive the bid amount, minus the txn fee
    assert actualSellerBalances[0] >= sellerAlgosBefore + bidAmount - 1_000
    assert actualSellerBalances[nftID] == 0