import pytest
import brownie
from brownie import accounts, chain, Artifacts, ArcaneRelic
from brownie.test import given, strategy
import time

DEFAULT_ADMIN_ROLE = "0x0000000000000000000000000000000000000000000000000000000000000000"

def print_artifact_dist(artifacts):
    total_1 = 0
    total_2 = 0
    total = 0
    for i in range(1, 9):
        print(f"""{i}: {artifacts.balanceOf(accounts[1], i)} + \
{artifacts.balanceOf(accounts[2], i)} = {artifacts.totalSupply(i)}""")
        total += artifacts.totalSupply(i)
        total_1 += artifacts.balanceOf(accounts[1], i)
        total_2 += artifacts.balanceOf(accounts[2], i)
    print(f"Total: {total_1} + {total_2} = {total}")


@pytest.fixture
def xrlc():
    dev = accounts[0]
    xrlc = ArcaneRelic.deploy({'from': dev})
    for i in range(3):
        xrlc.mint(accounts[i], 30000000000000000000000, {'from': dev})
    return xrlc

@pytest.fixture
def contracts(xrlc):
    dev = accounts[0]
    name = "FTL Artifacts"
    symbol = "ARTIFACT"
    uri = "my_uri/"
    base_price = 122000000000000000000 # 122 * 1e18
    max_price = 222000000000000000000 # 222 * 1e18
    price_increase_factor = 827000000000000000 # 0.827
    admin = accounts[1]
    artifacts = Artifacts.deploy(
                            name,
                            symbol,
                            uri,
                            base_price,
                            max_price,
                            price_increase_factor,
                            xrlc,
                            admin,
                            {'from': dev})

    return xrlc, artifacts

def test_initial_state(contracts):
    xrlc, artifacts = contracts
    for i in range(3):
        assert xrlc.balanceOf(accounts[i]) == "30000 ether"
    assert artifacts.name() == "FTL Artifacts"
    assert artifacts.symbol() == "ARTIFACT"

def test_uri(contracts):
    xrlc, artifacts = contracts

    # not admin
    with brownie.reverts(f"""AccessControl: account \
{accounts[2].address.lower()} is missing role {DEFAULT_ADMIN_ROLE}"""):
        artifacts.setURI("new_uri/", {'from': accounts[2]})
        artifacts.setURIExtension(".kebab", {'from': accounts[2]})


    # URI query for nonexistent token
    with brownie.reverts("URI query for nonexistent token"):
        artifacts.uri(1)

    xrlc.approve(artifacts, "30000 ether", {'from': accounts[0]})
    artifacts.collectArtifact({'from': accounts[0]})
    for id_ in range(1, 9):
        if artifacts.balanceOf(accounts[0], id_):
            assert artifacts.uri(id_) == f"my_uri/{id_}.json"

            # test setURI
            artifacts.setURI("new_uri/", {'from': accounts[0]})
            assert artifacts.uri(id_) == f"new_uri/{id_}.json"

            # test setURIExtension
            artifacts.setURIExtension(".kebab", {'from': accounts[1]})
            assert artifacts.uri(id_) == f"new_uri/{id_}.kebab"

def test_price(contracts):
    xrlc, artifacts = contracts
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[0]})

    # not admin
    with brownie.reverts(f"""AccessControl: account \
{accounts[3].address.lower()} is missing role {DEFAULT_ADMIN_ROLE}"""):
        artifacts.setBasePrice("69 ether", {'from': accounts[3]})
        artifacts.setMaxPrice("420 ether", {'from': accounts[3]})
        artifacts.setPriceIncreaseFactor("0.699 ether", {'from': accounts[3]})

    base_price = 122000000000000000000 # 122 ether
    max_price = 222000000000000000000 # 222 ether
    price_increase_factor = 827000000000000000 # 0.827 ether

    # test price bonding curve
    for i in range(121):
        assert artifacts.price() == price_increase_factor * i + base_price
        artifacts.collectArtifact({'from': accounts[0]})

    assert artifacts.price() == max_price

    # test setMaxPrice
    artifacts.setMaxPrice("100 ether", {'from': accounts[0]})
    assert artifacts.price() == "100 ether"
    artifacts.setMaxPrice("500 ether", {'from': accounts[0]})
    assert artifacts.price() == price_increase_factor * 121 + base_price

    # test setBasePrice and setPriceIncreaseFactor
    artifacts.setBasePrice("80 ether", {'from': accounts[1]})
    artifacts.setPriceIncreaseFactor("2 ether", {'from': accounts[1]})
    assert artifacts.price() == 2000000000000000000 * 121 + 80000000000000000000

def test_collect_artifact(contracts):
    xrlc, artifacts = contracts

    # no xrlc allowance
    with brownie.reverts("ERC20: burn amount exceeds allowance"):
        artifacts.collectArtifact({'from': accounts[2]})

    xrlc.approve(artifacts, "30000 ether", {'from': accounts[1]})
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[2]})
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[3]})

    # not enough xrlc
    with brownie.reverts("ERC20: burn amount exceeds balance"):
        artifacts.collectArtifact({'from': accounts[3]})

    xrlc_total_supply = xrlc.totalSupply()
    balance_1 = xrlc.balanceOf(accounts[1])
    balance_2 = xrlc.balanceOf(accounts[2])
    for i in range(100):
        balance_1 -= artifacts.price()
        xrlc_total_supply -= artifacts.price()
        artifacts.collectArtifact({'from': accounts[1]})
        balance_2 -= artifacts.price()
        xrlc_total_supply -= artifacts.price()
        artifacts.collectArtifact({'from': accounts[2]})

    # assert xrlc movements
    assert xrlc.totalSupply() == xrlc_total_supply
    assert xrlc.balanceOf(accounts[1]) == balance_1
    assert xrlc.balanceOf(accounts[2]) == balance_2

    # assert token movements
    assert artifacts.totalSupply() == 200
    assert artifacts.totalMinted() == 200

    # check artifact random distribution
    print_artifact_dist(artifacts)

    # burn artifact
    artifacts.burn(accounts[1], 1, 1, {'from': accounts[1]})
    assert artifacts.totalSupply() == 199
    assert artifacts.totalMinted() == 200

    # dummy failed test so stdout gets printed
    # artifacts.collectArtifact({'from': accounts[3]})
