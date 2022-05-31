from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Optional, Type


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


class _Block(ABC):
    pass


class _PrimaryBlock(_Block):
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


class _CanonicalBlock(_Block, ABC):
    block_type: int = 0
    block_number: int = 0
    control_flags: _ProcCtrlFlags = _ProcCtrlFlags()
    crc_type: CRCTypeEnum = CRCTypeEnum.NOCRC
    data: bytes = b""
    crc: Optional[str] = None


class _PayloadBlock(_CanonicalBlock):
    block_type = 1


class _ExtensionBlock(_Block, ABC):
    block_type: int = 0


class _PreviousNodeBlock(_ExtensionBlock):
    block_type = 6
    forwarder_id: str = ""


class _BundleAgeBlock(_ExtensionBlock):
    block_type = 7
    age: int = 0


class _HopCountBlock(_ExtensionBlock):
    block_type = 10
    hop_limit: int = 0
    hop_count: int = 0


class Bundle:
    primary_block: _PrimaryBlock = _PrimaryBlock()
    canonical_blocks: list[_CanonicalBlock] = [_PayloadBlock()]
    extension_blocks: list[_ExtensionBlock] = []

    def add_block_type(self, block_type: int):
        if block_type == 1:
            raise ValueError("Only exactly 1 payload block allowed in bundle (RFC 9171, 4.1)")
        elif block_type == 6:
            if self._has_block(_PreviousNodeBlock):
                raise ValueError(
                    "Only exactly 1 previous node block allowed in bundle (RFC 9171, 4.4.1)"
                )
            self.extension_blocks.append(_PreviousNodeBlock())
        elif block_type == 7:
            if self._has_block(_BundleAgeBlock):
                raise ValueError(
                    "Only exactly 1 bundle age block allowed in bundle (RFC 9171, 4.4.2)"
                )
            self.extension_blocks.append(_BundleAgeBlock())
        elif block_type == 10:
            if self._has_block(_HopCountBlock):
                raise ValueError(
                    "Only exactly 1 hop-count block allowed in bundle (RFC 9171, 4.4.3)"
                )
            self.extension_blocks.append(_HopCountBlock())
        elif 10 < block_type < 192:
            raise ValueError("Block types 11 to 191 aur unassigned (RFC 9171, 9.1")
        else:
            raise NotImplementedError(f"Block type {block_type} not yet supported.")

    def _has_block(self, block_type: Type[_CanonicalBlock | _ExtensionBlock]):
        return any([isinstance(block, block_type) for block in self.extension_blocks]) or any(
            [isinstance(block, block_type) for block in self.canonical_blocks]
        )

    def blocks(self) -> list[_Block]:
        ret: list[_Block] = [self.primary_block]
        return ret + self.canonical_blocks + self.extension_blocks
