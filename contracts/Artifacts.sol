// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Burnable.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Supply.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import './ArcaneRelic.sol';

contract Artifacts is AccessControl, ERC1155Burnable, ERC1155Supply {
    using Strings for uint256;
    using Math for uint256;

    // token
    ArcaneRelic public immutable xrlc;
    string public name;
    string public symbol;

    string private _uri;
    string private _uriExtension;
    uint256 private _basePrice;
    uint256 private _maxPrice;
    uint256 private _priceIncreaseFactor;
    uint256 private _totalContractSupply;
    uint256 private _totalMinted;
    uint256 private nonce;

    constructor(
        string memory _name,
        string memory _symbol,
        string memory uri_,
        uint256 basePrice,
        uint256 maxPrice,
        uint256 priceIncreaseFactor,
        ArcaneRelic _xrlc,
        address admin)
        ERC1155(uri_)
    {
        name = _name;
        symbol = _symbol;
        _uri = uri_;
        _uriExtension = ".json";
        _basePrice = basePrice;
        _maxPrice = maxPrice;
        _priceIncreaseFactor = priceIncreaseFactor;
        xrlc = _xrlc;
        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    function setURI(string memory newuri) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _setURI(newuri);
    }

    function setURIExtension(string memory newuriExtension)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        _uriExtension = newuriExtension;
    }

    function setBasePrice(uint256 newBasePrice) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _basePrice = newBasePrice;
    }

    function setMaxPrice(uint256 newMaxPrice) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _maxPrice = newMaxPrice;
    }

    function setPriceIncreaseFactor(uint256 newPriceIncreaseFactor)
        external
        onlyRole(DEFAULT_ADMIN_ROLE) {
        _priceIncreaseFactor = newPriceIncreaseFactor;
    }

    function collectArtifact() external {
        uint256 _price = price();
        xrlc.burnFrom(msg.sender, _price);
        _mint(msg.sender, _randomArtifact(), 1, "");
    }

    function uri(uint256 id) public view override returns (string memory) {
        require(exists(id), "URI query for nonexistent token");
        return string(abi.encodePacked(_uri, id.toString(), _uriExtension));
    }

    function totalSupply() public view returns (uint256) {
        return _totalContractSupply;
    }

    function totalMinted() public view returns (uint256) {
        return _totalMinted;
    }

    function price() public view returns (uint256) {
        return _maxPrice.min(_priceIncreaseFactor * _totalMinted + _basePrice);
    }


    function _setURI(string memory newuri) internal override {
        _uri = newuri;
    }

    function _randomArtifact() private returns (uint256) {
        // add 1 so the number is between 1 and 8
        return 
            uint256(keccak256(abi.encodePacked(++nonce, block.timestamp, msg.sender, blockhash(block.number - 1)))) % 8 + 1;
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _beforeTokenTransfer(
        address operator,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    )
        internal
        override(ERC1155, ERC1155Supply) {
            super._beforeTokenTransfer(operator, from, to, ids, amounts, data);
            if (from == address(0)) {
                for (uint256 i = 0; i < ids.length; ++i) {
                    _totalContractSupply += amounts[i];
                    _totalMinted += amounts[i];
                }
            }

            if (to == address(0)) {
                for (uint256 i = 0; i < ids.length; ++i) {
                    uint256 amount = amounts[i];
                    require(_totalContractSupply >= amount, "ERC1155: burn amount exceeds totalSupply");
                    unchecked {
                        _totalContractSupply -= amount;
                    }
                }
        }
    }
}
