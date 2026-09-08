// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DataSovereignty
 * @dev Smart contract for managing farmer data consent on the blockchain
 * Farmers can grant/revoke access to their data and track who accessed it
 */
contract DataSovereignty {
    // Struct to store data access records
    struct AccessRecord {
        address farmerAddress;
        address organizationAddress;
        uint256 timestamp;
        string dataType;
        bool isActive;
        string purpose;
    }

    // Struct for farmer profile
    struct Farmer {
        string farmerId;
        string name;
        string location;
        bool isRegistered;
        uint256 registrationDate;
    }

    // State variables
    mapping(address => Farmer) public farmers;
    mapping(address => mapping(address => bool)) public accessPermissions;
    mapping(address => AccessRecord[]) public accessHistory;

    // Events for transparency
    event FarmerRegistered(address indexed farmerAddress, string farmerId);
    event AccessGranted(address indexed farmer, address indexed organization, string dataType);
    event AccessRevoked(address indexed farmer, address indexed organization);
    event DataAccessed(address indexed farmer, address indexed organization, uint256 timestamp);

    // Modifiers
    modifier onlyRegisteredFarmer() {
        require(farmers[msg.sender].isRegistered, "Farmer not registered");
        _;
    }

    /**
     * @dev Register a new farmer in the system
     * @param _farmerId Unique farmer identifier
     * @param _name Farmer's full name
     * @param _location Farmer's location/region
     */
    function registerFarmer(
        string memory _farmerId,
        string memory _name,
        string memory _location
    ) public {
        require(!farmers[msg.sender].isRegistered, "Farmer already registered");
        
        farmers[msg.sender] = Farmer({
            farmerId: _farmerId,
            name: _name,
            location: _location,
            isRegistered: true,
            registrationDate: block.timestamp
        });

        emit FarmerRegistered(msg.sender, _farmerId);
    }

    /**
     * @dev Grant data access permission to an organization
     * @param _organization Address of the organization
     * @param _dataType Type of data being shared
     * @param _purpose Purpose of data access
     */
    function grantAccess(
        address _organization,
        string memory _dataType,
        string memory _purpose
    ) public onlyRegisteredFarmer {
        require(_organization != address(0), "Invalid organization address");
        require(!accessPermissions[msg.sender][_organization], "Access already granted");

        accessPermissions[msg.sender][_organization] = true;
        accessHistory[msg.sender].push(AccessRecord({
            farmerAddress: msg.sender,
            organizationAddress: _organization,
            timestamp: block.timestamp,
            dataType: _dataType,
            isActive: true,
            purpose: _purpose
        }));

        emit AccessGranted(msg.sender, _organization, _dataType);
    }

    /**
     * @dev Revoke data access permission from an organization
     * @param _organization Address of the organization
     */
    function revokeAccess(address _organization) public onlyRegisteredFarmer {
        require(accessPermissions[msg.sender][_organization], "Access not granted");

        accessPermissions[msg.sender][_organization] = false;
        
        // Update latest access record
        uint256 historyLength = accessHistory[msg.sender].length;
        for (uint256 i = 0; i < historyLength; i++) {
            if (accessHistory[msg.sender][i].organizationAddress == _organization && 
                accessHistory[msg.sender][i].isActive) {
                accessHistory[msg.sender][i].isActive = false;
                break;
            }
        }

        emit AccessRevoked(msg.sender, _organization);
    }

    /**
     * @dev Check if an organization has access to a farmer's data
     * @param _farmer Address of the farmer
     * @param _organization Address of the organization
     * @return bool True if access is granted
     */
    function hasAccess(address _farmer, address _organization) public view returns (bool) {
        return accessPermissions[_farmer][_organization];
    }

    /**
     * @dev Get access history for a farmer
     * @param _farmer Address of the farmer
     * @return AccessRecord[] Array of access records
     */
    function getAccessHistory(address _farmer) public view returns (AccessRecord[] memory) {
        return accessHistory[_farmer];
    }

    /**
     * @dev Log data access (called by organizations when they access farmer data)
     */
    function logDataAccess(address _farmer) public {
        require(accessPermissions[_farmer][msg.sender], "No access permission");
        emit DataAccessed(_farmer, msg.sender, block.timestamp);
    }

    /**
     * @dev Get farmer profile
     * @param _farmer Address of the farmer
     * @return Farmer struct
     */
    function getFarmer(address _farmer) public view returns (Farmer memory) {
        return farmers[_farmer];
    }
}