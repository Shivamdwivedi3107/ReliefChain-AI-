// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReliefChainLedger
 * @dev Cryptographic Audit Ledger for Disaster Relief Operations.
 * Records immutable SHA-256 state hashes, verification proofs, and milestone events
 * with ZERO personally identifiable information (PII) on-chain.
 */
contract ReliefChainLedger {
    address public owner;

    struct AuditRecord {
        bytes32 recordHash;
        string eventType;      // donation, allocation, distribution, qr_verification
        string referenceId;    // Non-PII UUID reference
        address submitter;
        uint256 timestamp;
        bool isVerified;
    }

    // Mapping from SHA-256 hash (bytes32) to AuditRecord
    mapping(bytes32 => AuditRecord) private _records;
    
    // Mapping from reference ID to array of related hashes
    mapping(string => bytes32[]) private _referenceHashes;

    // Authorized organizations / submitters
    mapping(address => bool) public authorizedCallers;

    // Total audit records count
    uint256 public totalRecordsCount;

    // Events
    event RecordRegistered(
        bytes32 indexed recordHash,
        string indexed eventType,
        string referenceId,
        address indexed submitter,
        uint256 timestamp
    );

    event DistributionVerified(
        bytes32 indexed recordHash,
        string referenceId,
        address indexed verifier,
        uint256 timestamp
    );

    event CallerAuthorized(address indexed caller);
    event CallerRevoked(address indexed caller);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only contract owner can execute this action");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == owner || authorizedCallers[msg.sender],
            "Caller is not authorized to register audit records"
        );
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedCallers[msg.sender] = true;
    }

    function setCallerAuthorization(address caller, bool isAuthorized) external onlyOwner {
        require(caller != address(0), "Invalid caller address");
        authorizedCallers[caller] = isAuthorized;
        if (isAuthorized) {
            emit CallerAuthorized(caller);
        } else {
            emit CallerRevoked(caller);
        }
    }

    /**
     * @notice Register a tamper-evident SHA-256 record hash for any operational event.
     */
    function registerRecord(
        bytes32 recordHash,
        string calldata eventType,
        string calldata referenceId
    ) external onlyAuthorized returns (bool) {
        require(recordHash != bytes32(0), "Record hash cannot be zero");
        require(bytes(eventType).length > 0, "Event type is required");
        require(_records[recordHash].timestamp == 0, "Record hash already exists on ledger");

        _records[recordHash] = AuditRecord({
            recordHash: recordHash,
            eventType: eventType,
            referenceId: referenceId,
            submitter: msg.sender,
            timestamp: block.timestamp,
            isVerified: false
        });

        _referenceHashes[referenceId].push(recordHash);
        totalRecordsCount += 1;

        emit RecordRegistered(recordHash, eventType, referenceId, msg.sender, block.timestamp);
        return true;
    }

    /**
     * @notice Verify a completed distribution on-chain upon cryptographic QR verification.
     */
    function verifyDistribution(
        bytes32 recordHash,
        string calldata referenceId
    ) external onlyAuthorized returns (bool) {
        require(recordHash != bytes32(0), "Record hash cannot be zero");
        
        if (_records[recordHash].timestamp == 0) {
            // Auto-register if not present
            _records[recordHash] = AuditRecord({
                recordHash: recordHash,
                eventType: "qr_verification",
                referenceId: referenceId,
                submitter: msg.sender,
                timestamp: block.timestamp,
                isVerified: true
            });
            _referenceHashes[referenceId].push(recordHash);
            totalRecordsCount += 1;
        } else {
            _records[recordHash].isVerified = true;
        }

        emit DistributionVerified(recordHash, referenceId, msg.sender, block.timestamp);
        return true;
    }

    /**
     * @notice Query verification status and timestamp of a record hash.
     */
    function verifyRecord(bytes32 recordHash) external view returns (
        bool exists,
        string memory eventType,
        string memory referenceId,
        address submitter,
        uint256 timestamp,
        bool isVerified
    ) {
        AuditRecord memory rec = _records[recordHash];
        if (rec.timestamp == 0) {
            return (false, "", "", address(0), 0, false);
        }
        return (
            true,
            rec.eventType,
            rec.referenceId,
            rec.submitter,
            rec.timestamp,
            rec.isVerified
        );
    }

    /**
     * @notice Get all recorded state hashes linked to a reference ID.
     */
    function getHashesForReference(string calldata referenceId) external view returns (bytes32[] memory) {
        return _referenceHashes[referenceId];
    }
}
