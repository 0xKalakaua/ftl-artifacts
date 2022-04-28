#!/usr/bin/python3
import os
from brownie import Artifacts, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    xrlc = "0xE5586582E1a60E302a53e73E4FaDccAF868b459a"
    name = "FTL Artifacts"
    symbol = "ARTIFACT"
    base_uri = "https://fantomlordsapi.herokuapp.com/artifacts/"
    base_price = "122 ether"
    max_price = "222 ether"
    max_supply = 10000
    price_increase_factor = "0.08196 ether" # prod value
    # price_increase_factor = "0.8197 ether" # test value
    admin = "0x4a03721C829Ae3d448bF37Cac21527cbE75fc4Cb"
    Artifacts.deploy(
                name,
                symbol,
                base_uri,
                base_price,
                max_price,
                price_increase_factor,
                max_supply,
                xrlc,
                admin,
                {"from": work},
                publish_source=publish_source
    )
