// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import './ArcaneRelic.sol';

contract Artifacts is AccessControl, ERC721Enumerable {
    using Counters for Counters.Counter;
    using Strings for uint256;
    using Math for uint256;

    ArcaneRelic public immutable xrlc;
    uint256 public immutable MAX_SUPPLY;

    Counters.Counter private _tokenIdCounter;
    Counters.Counter[8] private _typeTokenIdCounters;

    // tokenId to Artifact type (0-7)
    mapping(uint256 => uint256) private _tokenIdToArtifactType;
    // tokenId to tokenId per type
    mapping(uint256 => uint256) private _tokenIdToTypeTokenId;
    // Artifact type (0-7) to URI
    mapping(uint256 => string) private _typeIdToTypeURI;

    string private _baseTokenURI;
    string private _uriExtension = ".json";
    bool private _mintStarted = false;
    uint256 private _basePrice;
    uint256 private _maxPrice;
    uint256 private _priceIncreaseFactor;
    uint256 private _nonce;


    constructor (
        string memory name,
        string memory symbol,
        string memory baseURI,
        uint256 basePrice,
        uint256 maxPrice,
        uint256 priceIncreaseFactor,
        uint256 max_supply,
        ArcaneRelic _xrlc,
        address admin)
        ERC721(name, symbol)
    {
        MAX_SUPPLY = max_supply;
        _baseTokenURI = baseURI;
        _basePrice = basePrice;
        _maxPrice = maxPrice;
        _priceIncreaseFactor = priceIncreaseFactor;
        xrlc = _xrlc;
        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    modifier onlyAdmin() {
        _checkRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _;
    }

    function setBaseURI(string memory newBaseURI) external onlyAdmin {
        _baseTokenURI = newBaseURI;
    }

    function setURIExtension(string memory newuriExtension)
        external
        onlyAdmin
    {
        _uriExtension = newuriExtension;
    }

    function setTypeURI(uint256 artifactTypeId, string memory newTypeUri) external onlyAdmin {
        _typeIdToTypeURI[artifactTypeId] = newTypeUri;
    }
    
    function setBasePrice(uint256 newBasePrice) external onlyAdmin {
        _basePrice = newBasePrice;
    }

    function setMaxPrice(uint256 newMaxPrice) external onlyAdmin {
        _maxPrice = newMaxPrice;
    }

    function setPriceIncreaseFactor(uint256 newPriceIncreaseFactor)
        external
        onlyAdmin
    {
        _priceIncreaseFactor = newPriceIncreaseFactor;
    }

    function artifactType(uint256 tokenId) external view returns (uint256) {
        return _tokenIdToArtifactType[tokenId];
    }

    function typeTokenId(uint256 tokenId) external view returns (uint256) {
        return _tokenIdToTypeTokenId[tokenId];
    }

    function totalSupplyPerType(uint256 artifactTypeId) external view returns (uint256) {
        return _typeTokenIdCounters[artifactTypeId].current();
    }

    function startMint() external onlyAdmin {
        _mintStarted = true;
    }

    function collectArtifacts(uint256 amount) external {
        uint256 totalPrice = price(amount);
        require(_mintStarted, "mint has not started yet");
        require(_tokenIdCounter.current() < MAX_SUPPLY, "all tokens have been minted");
        require(amount <= 10, "can't mint more than 10 at a time");
        require(
            _tokenIdCounter.current() + amount < MAX_SUPPLY + 1,
            "not enough tokens left to mint"
        );

        xrlc.burnFrom(msg.sender, totalPrice);

        for (uint256 i = 0; i < amount; ++i) {
            uint256 artifactTypeId = _randomArtifact();

            _tokenIdCounter.increment();
            _typeTokenIdCounters[artifactTypeId].increment();

            uint256 tokenId = _tokenIdCounter.current();
            uint256 typeTokenId = _typeTokenIdCounters[artifactTypeId].current();

            _tokenIdToTypeTokenId[tokenId] = typeTokenId;
            _tokenIdToArtifactType[tokenId] = artifactTypeId;
            _safeMint(msg.sender, tokenId);
        }
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_exists(tokenId), "URI query for nonexistent token");

        uint256 typeTokenId = _tokenIdToTypeTokenId[tokenId];
        uint256 artifactType = _tokenIdToArtifactType[tokenId];
        string memory baseURI = _baseURI();
        string memory typeURI = _typeIdToTypeURI[artifactType];

        if (bytes(typeURI).length > 0) {
            return string(abi.encodePacked(typeURI, typeTokenId.toString(), _uriExtension));
        }
        return string(abi.encodePacked(baseURI, tokenId.toString(), _uriExtension));
    }

    function price(uint256 amount) public view returns (uint256) {
        uint256 totalPrice;
        for (uint256 i = 0; i < amount; ++i) {
            totalPrice += _price(totalSupply() + i);
        }
        return totalPrice;
    }

    function _price(uint256 totalMinted) private view returns (uint256) {
        return _maxPrice.min(_priceIncreaseFactor * totalMinted + _basePrice);
    }

    function _randomArtifact() private returns (uint256) {
        return 
            uint256(keccak256(abi.encodePacked(++_nonce, block.timestamp, msg.sender, blockhash(block.number - 1)))) % 8;
    }

    function _baseURI() internal view override returns (string memory) {
        return _baseTokenURI;
    }

    //function _artifactTypeName(uint256 artifactTypeId) private pure returns (string memory) {
        //if (artifactTypeId == 1) {
            //return "TYPE 1";
        //} else if (artifactTypeId == 2) {
            //return "TYPE 2";
        //} else if (artifactTypeId == 3) {
            //return "TYPE 3";
        //} else if (artifactTypeId == 4) {
            //return "TYPE 4";
        //} else if (artifactTypeId == 5) {
            //return "TYPE 5";
        //} else if (artifactTypeId == 6) {
            //return "TYPE 6";
        //} else if (artifactTypeId == 7) {
            //return "TYPE 7";
        //} else if (artifactTypeId == 8) {
            //return "TYPE 8";
        //} else {
            //return "";
        //}
    //}

    function _beforeTokenTransfer(address from, address to, uint256 tokenId)
        internal
        override(ERC721Enumerable)
    {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(AccessControl, ERC721Enumerable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
