from enum import Enum


class NodeType(Enum):
    CERT_TEMPLATE = "CertTemplate"
    COMPUTER = "Computer"
    DOMAIN = "Domain"
    ENTERPRISE_CA = "EnterpriseCA"
    GROUP = "Group"
    GPO = "GPO"
    OU = "OU"
    ROOT_CA = "RootCA"
    USER = "User"


NODE_TYPES = {node_type.name: node_type.value for node_type in NodeType}


class EdgeType(Enum):
    ADCSESC1 = "ADCSES1"
    ADCSESC3 = "ADCSES3"
    ADCSESC6A = "ADCSES6a"
    ADCSESC9A = "ADCSES9a"
    ADCSESC10A = "ADCSES10a"
    ADD_ALLOWED_TO_ACT = "AddAllowedToAct"
    ADD_KEY_CREDENTIAL_LINK = "AddKeyCredentialLink"
    ADD_MEMBER = "AddMember"
    ADD_SELF = "AddSelf"
    ALLOWED_TO_ACT = "AllowedToAct"
    ALLOWED_TO_DELEGATE = "AllowedToDelegate"
    ALL_EXTENDED_RIGHTS = "AllExtendedRights"
    DC_SYNC = "DCSync"
    ENROLL = "Enroll"
    FORCE_CHANGE_PASSWORD = "ForceChangePassword"
    GENERIC_ALL = "GenericAll"
    GENERIC_WRITE = "GenericWrite"
    GET_CHANGES = "GetChanges"
    GET_CHANGES_ALL = "GetChangesAll"
    GET_CHANGES_IN_FILTERED_SET = "GetChangesInFilteredSet"
    MANAGE_CA = "ManageCA"
    MANAGE_CERTIFICATES = "ManageCertificates"
    MEMBER_OF = "MemberOf"
    OWNS = "Owns"
    READ_GMSA_PASSWORD = "ReadGMSAPassword"
    READ_LAPS_PASSWORD = "ReadLAPSPassword"
    SQL_ADMIN = "SQLAdmin"
    SYNC_LAPS_PASSWORD = "SyncLAPSPassword"
    WRITE_ACCOUNT_RESTRICTIONS = "WriteAccountRestrictions"
    WRITE_DACL = "WriteDacl"
    WRITE_OWNER = "WriteOwner"
    WRITE_PKI_ENROLLMENT_FLAG = "WritePKIEnrollmentFlag"
    WRITE_PKI_NAME_FLAG = "WritePKINameFlag"
    WRITE_SPN = "WriteSPN"


EDGES_TYPES = {edge.name: edge.value for edge in EdgeType}


class NodeAttributes(Enum):
    SYSTEM_TAGS = []


NODE_ATTRIBUTES = {prop.name.lower(): prop.value for prop in NodeAttributes}
