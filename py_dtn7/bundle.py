from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Optional


class CRCTypeEnum(Enum):
    NOCRC = 0
    X25 = 1
    CRC32C = 2


class _ProcCtrlFlags:
    """
    4.2.3. Bundle Processing Control Flags
    Bundle processing control flags assert properties of the bundle as a whole rather than of any
    particular block of the bundle. They are conveyed in the primary block of the bundle.
    """

    # The bundle is a fragment
    is_fragment: bool = False
    # The bundle's payload is an administrative record
    payload_admin_rec: bool = False
    # The bundle must not be fragmented
    no_fragment: bool = False
    # Acknowledgment by the user application is requested
    request_ack: bool = False
    # Status time is requested in all status reports
    request_status_time: bool = False

    # Flags requesting types of status reports:
    # Request reporting of bundle reception
    report_reception: bool = False
    # Request reporting of bundle forwarding
    report_forwarding: bool = False
    # Request reporting of bundle delivery
    report_delivery: bool = False
    # Request reporting of bundle deletion
    report_deletion: bool = False


class _PrimaryBlock:
    version: int = 0
    control_flags: _ProcCtrlFlags = _ProcCtrlFlags()
    crc_type: CRCTypeEnum = CRCTypeEnum.NOCRC
    destination_eid: str = ""
    source_node_eid: str = ""
    report_to_eid: str = ""
    creation_timestamp: datetime = datetime.utcnow()
    lifetime: int = 0
    fragment_offset: int = 0
    total_application_data_unit_length: int = 0
    crc: str = ""


class _CanonicalBlock(ABC):
    block_type: int = 0
    block_number: int = 0
    control_flags: _ProcCtrlFlags = _ProcCtrlFlags()
    crc_type: CRCTypeEnum = CRCTypeEnum.NOCRC
    data: bytes = b""
    crc: Optional[str] = None


class _PayloadBlock(_CanonicalBlock):
    block_type = 1


class _ExtensionBlock(ABC):
    block_type: int = 0


class _HopCountBlock(_ExtensionBlock):
    block_type = 10
    hop_limit: int = 0
    hop_count: int = 0


class Bundle:
    primary_block: _PrimaryBlock = _PrimaryBlock()
    canonical_blocks: list[_CanonicalBlock] = []
    extension_blocks: list[_ExtensionBlock] = []

    def add_block_type(self, block_type: int):
        if block_type == 1:
            self.canonical_blocks.append(_PayloadBlock())
