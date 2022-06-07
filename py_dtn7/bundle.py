from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Optional, Type


class CRCTypeEnum(Enum):
    NOCRC = 0
    X25 = 1
    CRC32C = 2


class _BundleProcCtrlFlags:
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
    request_report_reception: bool = False
    # Request reporting of bundle forwarding
    request_report_forwarding: bool = False
    # Request reporting of bundle delivery
    request_report_delivery: bool = False
    # Request reporting of bundle deletion
    request_report_deletion: bool = False

    def __repr__(self):
        res: int = 0
        res += 1 if self.is_fragment else 0
        res += 2 if self.payload_admin_rec else 0
        res += 4 if self.no_fragment else 0
        res += 32 if self.request_ack else 0
        res += 64 if self.request_status_time else 0
        res += 16384 if self.request_report_reception else 0
        res += 65536 if self.request_report_forwarding else 0
        res += 131072 if self.request_report_delivery else 0
        res += 262144 if self.request_report_deletion else 0
        return hex(res)


class _BlockProcCtrlFlags:
    must_be_replicated: bool = False
    process_unable_status_report: bool = False
    process_unable_delete: bool = False
    process_unable_discard: bool = False

    def __repr__(self):
        res: int = 0
        res += 1 if self.must_be_replicated else 0
        res += 2 if self.process_unable_status_report else 0
        res += 4 if self.process_unable_delete else 0
        res += 16 if self.process_unable_discard else 0
        return hex(res)


class _Block(ABC):
    pass


class _PrimaryBlock(_Block):
    """
    4.3.1. Primary Bundle Block

       The primary bundle block contains the basic information needed to forward bundles to their
       destinations.

       Each primary block SHALL be represented as a CBOR array; the number of elements in the array
       SHALL be 8 (if the bundle is not a fragment and the block has no CRC), 9 (if the block has a
       CRC and the bundle is not a fragment), 10 (if the bundle is a fragment and the block has no
       CRC), or 11 (if the bundle is a fragment and the block has a CRC).

       The primary block of each bundle SHALL be immutable. The CBOR- encoded values of all fields
       in the primary block MUST remain unchanged from the time the block is created to the time it
       is delivered.

       The fields of the primary bundle block SHALL be as follows, listed in the order in which
       they MUST appear:
    """

    _version: int = 7
    _bundle_proc_ctrl_flags: _BundleProcCtrlFlags = _BundleProcCtrlFlags()
    _crc_type: CRCTypeEnum = CRCTypeEnum.NOCRC
    _destination_eid: str = ""
    _source_node_eid: str = ""
    _report_to_eid: str = ""
    _creation_timestamp: datetime = datetime.utcnow()
    _lifetime: int = 0
    _fragment_offset: Optional[int]
    _total_adu_length: int = 0
    _crc: Optional[str]

    @property
    def version(self):
        return self._version

    @property
    def bundle_proc_ctrl_flags(self):
        return self._bundle_proc_ctrl_flags

    @property
    def crc_type(self):
        return self._crc_type

    @property
    def destination_eid(self):
        return self._destination_eid

    @property
    def source_node_eid(self):
        return self._source_node_eid

    @property
    def creation_timestamp(self):
        return self._creation_timestamp

    @property
    def lifetime(self):
        return self._lifetime

    @property
    def fragment_offset(self):
        return self._fragment_offset

    @property
    def total_adu_length(self):
        return self._total_adu_length

    def __repr__(self) -> str:
        return (
            f"<PrimaryBlock: [{self._version}, {self._bundle_proc_ctrl_flags},"
            f' {self._crc_type.value}, "{self._destination_eid}", "{self._source_node_eid}",'
            f' "{self._report_to_eid}", "{self._report_to_eid}"]>'
        )


class _CanonicalBlock(_Block, ABC):
    block_type: int = 0
    block_number: int = 0
    block_proc_ctrl_flags: _BlockProcCtrlFlags = _BlockProcCtrlFlags()
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
            raise ValueError("Block types 11 to 191 are unassigned (RFC 9171, 9.1")
        else:
            raise NotImplementedError(f"Block type {block_type} not yet supported.")

    def _has_block(self, block_type: Type[_CanonicalBlock | _ExtensionBlock]):
        return any([isinstance(block, block_type) for block in self.extension_blocks]) or any(
            [isinstance(block, block_type) for block in self.canonical_blocks]
        )

    def __repr__(self) -> str:
        ret: list[_Block] = [self.primary_block]
        return str(ret + self.canonical_blocks + self.extension_blocks)
