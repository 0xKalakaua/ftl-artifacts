#!/usr/bin/python3
import os
from brownie import Artifacts, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    xrlc = "0x6F849B9781f4ee13B983f5E5b1485786A4D411d5"
    name = "FTL Artifacts"
    symbol = "ARTIFACT"
    uri = "my_uri/"
    base_price = "122 ether"
    max_price = "222 ether"
    price_increase_factor = "0.08196 ether"
    admin = work
    Artifacts.deploy(
                name,
                symbol,
                uri,
                base_price,
                max_price,
                price_increase_factor,
                xrlc,
                admin,
                {"from": work},
                publish_source=publish_source
    )
