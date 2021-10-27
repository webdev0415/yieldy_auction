from time import time, sleep

from algosdk import account, encoding
from algosdk.logic import get_application_address
from auction.operations import createAuctionApp, setupAuctionApp, placeBid, closeAuction
from auction.util import (
    getBalances,
    getAppGlobalState,
    getLastBlockTimestamp,
)
from auction.testing.setup import getAlgodClient
from auction.testing.resources import (
    getTemporaryAccount,
    optInToAsset,
    createDummyAsset,
)

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