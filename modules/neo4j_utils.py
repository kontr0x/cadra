from typing import Any, Dict, List

from models.bloodhound import NODE_TYPES


def get_node_type_from_labels(labels: List[str]) -> str:
    for label in labels:
        if label in NODE_TYPES.values():
            return label
    return "Unknown"


def get_uac_flags_from_properties(props: Dict[str, Any]) -> List[str]:
    flags = []
    # 'SCRIPT',
    # 'ACCOUNTDISABLE',
    if 'enabled' in props:
        if props['enabled'] == False:
            flags.append('ACCOUNTDISABLE')
    # 'HOMEDIR_REQUIRED',
    # 'LOCKOUT',
    # 'PASSWD_NOTREQD',
    if 'passwordnotreqd' in props:
        if props['passwordnotreqd'] == True:
            flags.append('PASSWD_NOTREQD')
    # 'PASSWD_CANT_CHANGE',
    # 'ENCRYPTED_TEXT_PASSWORD_ALLOWED',
    # 'TEMP_DUPLICATE_ACCOUNT',
    # 'NORMAL_ACCOUNT',
    # 'INTERDOMAIN_TRUST_ACCOUNT',
    # 'WORKSTATION_TRUST_ACCOUNT',
    # 'SERVER_TRUST_ACCOUNT',
    # 'DONT_EXPIRE_PASSWD',
    if 'pwdneverexpires' in props:
        if props['pwdneverexpires'] == True:
            flags.append('DONT_EXPIRE_PASSWD')
    # 'MNS_LOGON_ACCOUNT',
    # 'SMARTCARD_REQUIRED',
    # 'TRUSTED_FOR_DELEGATION',
    if 'unconstraineddelegation' in props:
        if props['unconstraineddelegation'] == True:
            flags.append('TRUSTED_FOR_DELEGATION')
    # 'NOT_DELEGATED',
    if 'sensitive' in props:
        if props['sensitive'] == True:
            flags.append('NOT_DELEGATED')
    # 'USE_DES_KEY_ONLY',
    # 'DONT_REQUIRE_PREAUTH',
    if 'dontreqpreauth' in props:
        if props['dontreqpreauth'] == True:
            flags.append('DONT_REQUIRE_PREAUTH')
    # 'PASSWORD_EXPIRED',
    # 'TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION',
    if 'trustedtoauth' in props:
        if props['trustedtoauth'] == True:
            flags.append('TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION')
    # 'PARTIAL_SECRETS_ACCOUNT'
    return flags
