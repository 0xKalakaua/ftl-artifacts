#!/usr/bin/python3
import os
from brownie import Artifacts, accounts, network, config

def main():
    work = accounts.load("work")
    print(network.show_active())
    publish_source = True # Not supported on Testnet
    xrlc = "0x7b8Ca0e3A88d3BaEC8Cb8781e9Ca83706315e0DD"
    name = "FTL Artifacts"
    symbol = "ARTIFACT"
    base_uri = "my_uri/"
    base_price = "122 ether"
    max_price = "222 ether"
    max_supply = 500
    # price_increase_factor = "0.08196 ether"
    price_increase_factor = "0.827 ether"
    admin = work
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
