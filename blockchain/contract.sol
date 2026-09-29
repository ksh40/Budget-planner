// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PermitRegistry {
    
    struct PermitRecord {
        string permitNumber;
        string issuingAuthority;
        uint256 timestamp;
        bool exists;
    }
    
    mapping(string => PermitRecord) private permits;
    address public owner;
    
    event PermitRegistered(string permitNumber, string issuingAuthority, uint256 timestamp);
    event PermitVerified(string permitNumber, bool isValid);
    
    constructor() {
        owner = msg.sender;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can register permits");
        _;
    }
    
    function registerPermit(string memory permitNumber, string memory issuingAuthority) public onlyOwner {
        permits[permitNumber] = PermitRecord({
            permitNumber: permitNumber,
            issuingAuthority: issuingAuthority,
            timestamp: block.timestamp,
            exists: true
        });
        emit PermitRegistered(permitNumber, issuingAuthority, block.timestamp);
    }
    
    function verifyPermit(string memory permitNumber, string memory issuingAuthority) public returns (bool) {
        PermitRecord memory record = permits[permitNumber];
        bool isValid = record.exists && 
            keccak256(bytes(record.issuingAuthority)) == keccak256(bytes(issuingAuthority));
        emit PermitVerified(permitNumber, isValid);
        return isValid;
    }
    
    function getPermit(string memory permitNumber) public view returns (string memory, string memory, uint256, bool) {
        PermitRecord memory record = permits[permitNumber];
        return (record.permitNumber, record.issuingAuthority, record.timestamp, record.exists);
    }
}