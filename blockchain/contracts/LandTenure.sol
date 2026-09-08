// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title LandTenure
 * @dev Smart contract for managing verifiable land tenure records
 * Farmers can store and retrieve digital representations of their land rights
 */
contract LandTenure {
    // Struct to store land records
    struct LandRecord {
        string landId;
        address owner;
        string location;
        string documentType; // "Offer Letter", "99-Year Lease", etc.
        string documentHash; // IPFS hash of the actual document
        uint256 registrationDate;
        uint256 lastUpdated;
        bool isVerified;
        string plotNumber;
        string district;
        string province;
        uint256 sizeInHectares;
    }

    // Struct for land transfer history
    struct TransferHistory {
        address from;
        address to;
        uint256 timestamp;
        string reason;
    }

    // State variables
    mapping(string => LandRecord) public landRecords; // landId => LandRecord
    mapping(string => address) public landOwners; // landId => owner address
    mapping(string => TransferHistory[]) public landTransfers; // landId => transfer history
    mapping(address => string[]) public farmerLandHoldings; // farmer address => list of landIds

    // Events
    event LandRegistered(string landId, address indexed owner, string documentHash);
    event LandUpdated(string landId, address indexed owner, string documentHash);
    event LandTransferred(string landId, address indexed from, address indexed to);
    event LandVerified(string landId, bool status);

    /**
     * @dev Register a new land tenure record
     * @param _landId Unique land identifier
     * @param _location Geographic location
     * @param _documentType Type of document
     * @param _documentHash IPFS hash of the document
     * @param _plotNumber Plot number
     * @param _district District where land is located
     * @param _province Province where land is located
     * @param _sizeInHectares Size of land in hectares
     */
    function registerLand(
        string memory _landId,
        string memory _location,
        string memory _documentType,
        string memory _documentHash,
        string memory _plotNumber,
        string memory _district,
        string memory _province,
        uint256 _sizeInHectares
    ) public {
        require(bytes(_landId).length > 0, "Land ID cannot be empty");
        require(bytes(landRecords[_landId].landId).length == 0, "Land ID already exists");
        require(_sizeInHectares > 0, "Size must be greater than 0");

        landRecords[_landId] = LandRecord({
            landId: _landId,
            owner: msg.sender,
            location: _location,
            documentType: _documentType,
            documentHash: _documentHash,
            registrationDate: block.timestamp,
            lastUpdated: block.timestamp,
            isVerified: false,
            plotNumber: _plotNumber,
            district: _district,
            province: _province,
            sizeInHectares: _sizeInHectares
        });

        landOwners[_landId] = msg.sender;
        farmerLandHoldings[msg.sender].push(_landId);

        emit LandRegistered(_landId, msg.sender, _documentHash);
    }

    /**
     * @dev Update an existing land record
     * @param _landId Unique land identifier
     * @param _documentHash New IPFS hash of the document
     * @param _documentType New document type
     */
    function updateLandRecord(
        string memory _landId,
        string memory _documentHash,
        string memory _documentType
    ) public {
        require(bytes(landRecords[_landId].landId).length > 0, "Land ID does not exist");
        require(landRecords[_landId].owner == msg.sender, "Not the owner of this land");

        landRecords[_landId].documentHash = _documentHash;
        landRecords[_landId].documentType = _documentType;
        landRecords[_landId].lastUpdated = block.timestamp;

        emit LandUpdated(_landId, msg.sender, _documentHash);
    }

    /**
     * @dev Verify a land record (can only be called by authorized authorities)
     * @param _landId Unique land identifier
     * @param _status Verification status
     */
    function verifyLand(string memory _landId, bool _status) public {
        require(bytes(landRecords[_landId].landId).length > 0, "Land ID does not exist");
        // In a real implementation, you'd add access control here
        landRecords[_landId].isVerified = _status;
        emit LandVerified(_landId, _status);
    }

    /**
     * @dev Transfer land ownership to another farmer
     * @param _landId Unique land identifier
     * @param _newOwner Address of the new owner
     * @param _reason Reason for transfer
     */
    function transferLand(
        string memory _landId,
        address _newOwner,
        string memory _reason
    ) public {
        require(bytes(landRecords[_landId].landId).length > 0, "Land ID does not exist");
        require(landRecords[_landId].owner == msg.sender, "Not the owner of this land");
        require(_newOwner != address(0), "Invalid new owner address");

        address oldOwner = landRecords[_landId].owner;
        
        // Update ownership
        landRecords[_landId].owner = _newOwner;
        landOwners[_landId] = _newOwner;
        landRecords[_landId].lastUpdated = block.timestamp;

        // Update farmer holdings
        // Remove from old owner's holdings
        string[] storage oldHoldings = farmerLandHoldings[oldOwner];
        for (uint256 i = 0; i < oldHoldings.length; i++) {
            if (keccak256(bytes(oldHoldings[i])) == keccak256(bytes(_landId))) {
                oldHoldings[i] = oldHoldings[oldHoldings.length - 1];
                oldHoldings.pop();
                break;
            }
        }

        // Add to new owner's holdings
        farmerLandHoldings[_newOwner].push(_landId);

        // Add to transfer history
        landTransfers[_landId].push(TransferHistory({
            from: oldOwner,
            to: _newOwner,
            timestamp: block.timestamp,
            reason: _reason
        }));

        emit LandTransferred(_landId, oldOwner, _newOwner);
    }

    /**
     * @dev Get land record details
     * @param _landId Unique land identifier
     * @return LandRecord struct
     */
    function getLandRecord(string memory _landId) public view returns (LandRecord memory) {
        return landRecords[_landId];
    }

    /**
     * @dev Check if a land record exists
     * @param _landId Unique land identifier
     * @return bool True if exists
     */
    function landExists(string memory _landId) public view returns (bool) {
        return bytes(landRecords[_landId].landId).length > 0;
    }

    /**
     * @dev Get all land holdings for a farmer
     * @param _farmer Address of the farmer
     * @return string[] Array of land IDs
     */
    function getFarmerLandHoldings(address _farmer) public view returns (string[] memory) {
        return farmerLandHoldings[_farmer];
    }

    /**
     * @dev Get transfer history for a land
     * @param _landId Unique land identifier
     * @return TransferHistory[] Array of transfer records
     */
    function getTransferHistory(string memory _landId) public view returns (TransferHistory[] memory) {
        return landTransfers[_landId];
    }

    /**
     * @dev Get current owner of a land
     * @param _landId Unique land identifier
     * @return address Owner address
     */
    function getLandOwner(string memory _landId) public view returns (address) {
        return landOwners[_landId];
    }
}