import pytest
import brownie
from brownie import accounts, chain, Artifacts, ArcaneRelic
from brownie.test import given, strategy
import time

DEFAULT_ADMIN_ROLE = "0x0000000000000000000000000000000000000000000000000000000000000000"

def print_artifact_dist(artifacts):
    tokens_1 = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
    tokens_2 = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    for i in range(90):
        token_id_1 = artifacts.tokenOfOwnerByIndex(accounts[1], i)
        token_id_2 = artifacts.tokenOfOwnerByIndex(accounts[2], i)
        tokens_1[artifacts.artifactType(token_id_1)] += 1
        tokens_2[artifacts.artifactType(token_id_2)] += 1

    for i in range(8):
        print(f"{i}: {tokens_1[i]} + {tokens_2[i]} = {artifacts.totalSupplyPerType(i)}")

    total_1 = artifacts.balanceOf(accounts[1])
    total_2 = artifacts.balanceOf(accounts[2])
    print(f"Total: {total_1} + {total_2} = {artifacts.totalSupply()}")


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
    base_uri = "my_uri/"
    base_price = 122000000000000000000 # 122 * 1e18
    max_price = 222000000000000000000 # 222 * 1e18
    price_increase_factor = 827000000000000000 # 0.827
    max_supply = 180
    admin = accounts[1]
    artifacts = Artifacts.deploy(
                            name,
                            symbol,
                            base_uri,
                            base_price,
                            max_price,
                            price_increase_factor,
                            max_supply,
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
        artifacts.setBaseURI("new_uri/", {'from': accounts[2]})
        artifacts.setURIExtension(".kebab", {'from': accounts[2]})
        artifacts.setTypeURI("type_1_uri/", {'from': accounts[2]})


    # URI query for nonexistent token
    with brownie.reverts("URI query for nonexistent token"):
        artifacts.tokenURI(1)

    artifacts.startMint({'from': accounts[0]})
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[0]})
    artifacts.collectArtifacts(2, {'from': accounts[0]})

    # test tokenURI
    assert artifacts.tokenURI(2) == "my_uri/2"

    # test setBaseURI
    artifacts.setBaseURI("new_uri/", {'from': accounts[0]})
    assert artifacts.tokenURI(2) == f"new_uri/2"

    # test setURIExtension
    artifacts.setURIExtension(".kebab", {'from': accounts[1]})
    assert artifacts.tokenURI(2) == f"new_uri/2.kebab"

    # test setTypeURI
    artifact_type = artifacts.artifactType(2)
    type_token_id = artifacts.typeTokenId(2)
    artifacts.setTypeURI(artifact_type, "type_uri/", {'from': accounts[1]})
    assert artifacts.tokenURI(2) == f"type_uri/{type_token_id}.kebab"

def test_price(contracts):
    xrlc, artifacts = contracts
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[0]})
    artifacts.startMint({'from': accounts[0]})

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
        assert artifacts.price(1) == price_increase_factor * i + base_price
        artifacts.collectArtifacts(1, {'from': accounts[0]})

        if i == 110:
            assert artifacts.price(10) == "2175.185 ether"
        if i == 111:
            assert artifacts.price(10) == "2183.388 ether"

    assert artifacts.price(1) == max_price
    assert artifacts.price(5) == max_price * 5

    # test setMaxPrice
    artifacts.setMaxPrice("100 ether", {'from': accounts[0]})
    assert artifacts.price(2) == "200 ether"
    artifacts.setMaxPrice("500 ether", {'from': accounts[0]})
    assert artifacts.price(1) == price_increase_factor * 121 + base_price

    # test setBasePrice and setPriceIncreaseFactor
    artifacts.setBasePrice("80 ether", {'from': accounts[1]})
    artifacts.setPriceIncreaseFactor("2 ether", {'from': accounts[1]})
    assert artifacts.price(1) == 2000000000000000000 * 121 + 80000000000000000000

def test_collect_artifacts(contracts):
    xrlc, artifacts = contracts

    # mint not started yet
    with brownie.reverts("mint has not started yet"):
        artifacts.collectArtifacts(1, {'from': accounts[2]})

    artifacts.startMint({'from': accounts[0]})

    # mint more than 10 at a time
    with brownie.reverts("can't mint more than 10 at a time"):
        artifacts.collectArtifacts(11, {'from': accounts[2]})

    # no xrlc allowance
    with brownie.reverts("ERC20: burn amount exceeds allowance"):
        artifacts.collectArtifacts(2, {'from': accounts[2]})

    xrlc.approve(artifacts, "30000 ether", {'from': accounts[1]})
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[2]})
    xrlc.approve(artifacts, "30000 ether", {'from': accounts[3]})

    # not enough xrlc
    with brownie.reverts("ERC20: burn amount exceeds balance"):
        artifacts.collectArtifacts(1, {'from': accounts[3]})

    xrlc_total_supply = xrlc.totalSupply()
    balance_1 = xrlc.balanceOf(accounts[1])
    balance_2 = xrlc.balanceOf(accounts[2])
    for i in range(5):
        balance_1 -= artifacts.price(10)
        xrlc_total_supply -= artifacts.price(10)
        artifacts.collectArtifacts(10, {'from': accounts[1]})
        balance_2 -= artifacts.price(10)
        xrlc_total_supply -= artifacts.price(10)
        artifacts.collectArtifacts(10, {'from': accounts[2]})

    # assert xrlc movements
    assert xrlc.totalSupply() == xrlc_total_supply
    assert xrlc.balanceOf(accounts[1]) == balance_1
    assert xrlc.balanceOf(accounts[2]) == balance_2

    for i in range(10):
        if i == 9:
            # not enough tokens left to mint
            with brownie.reverts("not enough tokens left to mint"):
                artifacts.collectArtifacts(9, {'from': accounts[2]})

        artifacts.collectArtifacts(4, {'from': accounts[1]})
        artifacts.collectArtifacts(4, {'from': accounts[2]})

    # assert token movements
    assert artifacts.totalSupply() == 180
    assert artifacts.balanceOf(accounts[1]) == 90
    assert artifacts.balanceOf(accounts[2]) == 90

    # all tokens have been minted
    with brownie.reverts("all tokens have been minted"):
        artifacts.collectArtifacts(1, {'from': accounts[1]})

    # check artifact random distribution
    print_artifact_dist(artifacts)

    # dummy failed test so stdout gets printed
    assert 1 == 2
