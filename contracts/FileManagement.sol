// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileManagement {
    struct File {
        string fileHash;
        string fileName;
        string fileType;
        uint256 timestamp;
        address uploadedBy;
        string department;
        bool isApproved;
        string approvalStatus;
        address[] approvers;
        string[] comments;
    }

    struct User {
        string name;
        string role;
        string department;
        bool isActive;
        uint256[] fileIds;
    }

    mapping(uint256 => File) public files;
    mapping(address => User) public users;
    mapping(string => uint256[]) public departmentFiles;
    
    uint256 public fileCount;
    address public admin;
    
    event FileUploaded(uint256 fileId, string fileName, address uploadedBy);
    event FileApproved(uint256 fileId, address approver);
    event FileRejected(uint256 fileId, address rejector);
    event UserRegistered(address user, string name, string role, string department);
    
    constructor() {
        admin = msg.sender;
    }
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }
    
    modifier onlyApprover() {
        require(users[msg.sender].role == "approver", "Only approvers can perform this action");
        _;
    }
    
    function registerUser(address _user, string memory _name, string memory _role, string memory _department) public onlyAdmin {
        require(!users[_user].isActive, "User already registered");
        users[_user] = User({
            name: _name,
            role: _role,
            department: _department,
            isActive: true,
            fileIds: new uint256[](0)
        });
        emit UserRegistered(_user, _name, _role, _department);
    }
    
    function uploadFile(string memory _fileHash, string memory _fileName, string memory _fileType, string memory _department) public {
        require(users[msg.sender].isActive, "User not registered");
        fileCount++;
        files[fileCount] = File({
            fileHash: _fileHash,
            fileName: _fileName,
            fileType: _fileType,
            timestamp: block.timestamp,
            uploadedBy: msg.sender,
            department: _department,
            isApproved: false,
            approvalStatus: "Pending",
            approvers: new address[](0),
            comments: new string[](0)
        });
        
        users[msg.sender].fileIds.push(fileCount);
        departmentFiles[_department].push(fileCount);
        
        emit FileUploaded(fileCount, _fileName, msg.sender);
    }
    
    function approveFile(uint256 _fileId) public onlyApprover {
        require(files[_fileId].timestamp > 0, "File does not exist");
        require(!files[_fileId].isApproved, "File already approved");
        
        files[_fileId].approvers.push(msg.sender);
        files[_fileId].isApproved = true;
        files[_fileId].approvalStatus = "Approved";
        
        emit FileApproved(_fileId, msg.sender);
    }
    
    function rejectFile(uint256 _fileId, string memory _comment) public onlyApprover {
        require(files[_fileId].timestamp > 0, "File does not exist");
        require(!files[_fileId].isApproved, "File already approved");
        
        files[_fileId].approvers.push(msg.sender);
        files[_fileId].approvalStatus = "Rejected";
        files[_fileId].comments.push(_comment);
        
        emit FileRejected(_fileId, msg.sender);
    }
    
    function getFile(uint256 _fileId) public view returns (File memory) {
        require(files[_fileId].timestamp > 0, "File does not exist");
        return files[_fileId];
    }
    
    function getUserFiles(address _user) public view returns (uint256[] memory) {
        require(users[_user].isActive, "User not registered");
        return users[_user].fileIds;
    }
    
    function getDepartmentFiles(string memory _department) public view returns (uint256[] memory) {
        return departmentFiles[_department];
    }
} 