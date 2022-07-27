# for postponed evaluation of annotation of Bundle.from_cbor()
# more info: https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Optional, Type, List

import cbor2

from py_dtn7.utils import from_dtn_timestamp


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
    is_fragment: bool
    # The bundle's payload is an administrative record
    payload_admin_rec: bool
    # The bundle must not be fragmented
    no_fragment: bool
    # Acknowledgment by the user application is requested
    request_ack: bool
    # Status time is requested in all status reports
    request_status_time: bool

    # Flags requesting types of status reports:
    # Request reporting of bundle reception
    request_report_reception: bool
    # Request reporting of bundle forwarding
    request_report_forwarding: bool
    # Request reporting of bundle delivery
    request_report_delivery: bool
    # Request reporting of bundle deletion
    request_report_deletion: bool

    init_flags: int

    def __init__(self, flags: int):
        self.init_flags = flags
        self.request_report_deletion = bool(flags // 262144)
        flags %= 262144
        self.request_report_delivery = bool(flags // 131072)
        flags %= 131072
        self.request_report_forwarding = bool(flags // 65536)
        flags %= 65536
        self.request_report_reception = bool(flags // 16384)
        flags %= 16384

        self.request_status_time = bool(flags // 64)
        flags %= 64
        self.request_ack = bool(flags // 32)
        flags %= 32
        self.no_fragment = bool(flags // 4)
        flags %= 4
        self.payload_admin_rec = bool(flags // 2)
        flags %= 2
        self.is_fragment = bool(flags)

    def __repr__(self):
        res: int = 1 * self.is_fragment
        res += 2 * self.payload_admin_rec
        res += 4 * self.no_fragment
        res += 32 * self.request_ack
        res += 64 * self.request_status_time
        res += 16384 * self.request_report_reception
        res += 65536 * self.request_report_forwarding
        res += 131072 * self.request_report_delivery
        res += 262144 * self.request_report_deletion
        return hex(res)


class _BlockProcCtrlFlags:
    must_be_replicated: bool
    process_unable_status_report: bool
    process_unable_delete: bool
    process_unable_discard: bool

    init_flags: int

    def __init__(self, flags: int):
        self.init_flags = flags
        self.process_unable_discard = bool(flags // 16)
        flags %= 16
        self.process_unable_delete = bool(flags // 4)
        flags %= 4
        self.process_unable_status_report = bool(flags // 2)
        flags %= 2
        self.must_be_replicated = bool(flags)

    def __repr__(self):
        res: int = 1 * self.must_be_replicated
        res += 2 * self.process_unable_status_report
        res += 4 * self.process_unable_delete
        res += 16 * self.process_unable_discard
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

    _version: int
    _bundle_proc_ctrl_flags: _BundleProcCtrlFlags
    _crc_type: CRCTypeEnum
    _destination: str
    _source: str
    _report_to: str
    _timestamp: int
    _datetime: datetime
    _sequence_number: int
    _lifetime: int
    _fragment_offset: Optional[int]
    _total_adu_length: int
    _crc: Optional[str]

    def __init__(
        self,
        destination: str,
        source: str,
        bundle_proc_control_flags: _BundleProcCtrlFlags,
        timestamp: int,
        sequence_number: int,
        report_to: Optional[str] = None,
        lifetime: int = 1000 * 3600 * 24,
    ):
        self._version = 7
        self._bundle_proc_ctrl_flags = bundle_proc_control_flags
        self._crc_type = CRCTypeEnum.NOCRC
        self._destination = destination
        self._source = source
        self._report_to = source if report_to is None else report_to
        self._timestamp = timestamp
        self._datetime = from_dtn_timestamp(timestamp)
        self._sequence_number = sequence_number
        self._lifetime = lifetime
        self._fragment_offset = None
        self._total_adu_length = 0
        self._crc = None

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
    def destination(self):
        return self._destination

    @property
    def source(self):
        return self._source

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def sequence_number(self):
        return self._sequence_number

    @property
    def dt(self):
        return self._datetime

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
            f' {self._crc_type.name}, "{self._destination}", "{self._source}",'
            f' "{self._report_to}", "{self._report_to}, {self._datetime.isoformat()}"]>'
        )


class _CanonicalBlock(_Block, ABC):
    _block_type: int
    _block_number: int
    _block_proc_ctrl_flags: _BlockProcCtrlFlags
    _crc_type: CRCTypeEnum
    _data: bytes
    _crc: Optional[str]

    def __init__(
        self,
        block_proc_control_flags: _BlockProcCtrlFlags,
        data: bytes,
        block_number: int = 0,
        crc_type: CRCTypeEnum = CRCTypeEnum.NOCRC,
        crc: Optional[str] = None,
    ):
        self._block_type = -1
        self._block_number = block_number
        self._block_proc_ctrl_flags = block_proc_control_flags
        self._crc_type = crc_type
        self._data = data
        self._crc = crc

    @property
    def block_type(self) -> int:
        return self._block_type

    @property
    def block_number(self) -> int:
        return self._block_number

    @property
    def block_proc_ctrl_flags(self) -> _BlockProcCtrlFlags:
        return self._block_proc_ctrl_flags

    @property
    def crc_type(self) -> CRCTypeEnum:
        return self._crc_type

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def crc(self) -> Optional[str]:
        return self._crc

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}: [{self._block_number}, {self._block_proc_ctrl_flags},"
            f" {self._crc_type.name}, {self._data}>"
        )


class _PayloadBlock(_CanonicalBlock):
    def __init__(
        self,
        block_proc_control_flags: _BlockProcCtrlFlags,
        data: bytes,
        block_number: int = 0,
        crc_type: CRCTypeEnum = CRCTypeEnum.NOCRC,
        crc: Optional[str] = None,
    ):
        super().__init__(block_proc_control_flags, data, block_number, crc_type, crc)
        self._block_type = 1


class _PreviousNodeBlock(_CanonicalBlock):
    _block_type = 6
    forwarder_id: str = ""


class _BundleAgeBlock(_CanonicalBlock):
    _block_type = 7
    age: int = 0


class _HopCountBlock(_CanonicalBlock):
    _block_type = 10
    hop_limit: int = 0
    hop_count: int = 0


class Bundle:
    _primary_block: _PrimaryBlock
    _canonical_blocks: List[_CanonicalBlock]
    _data: Optional[bytes]

    def __init__(
        self,
        primary_block: _PrimaryBlock,
        canonical_blocks: List[_CanonicalBlock],
        data: Optional[bytes] = None,
    ):
        self._primary_block = primary_block
        self._canonical_blocks = canonical_blocks
        self._data = data

    @staticmethod
    def from_cbor(data: Optional[bytes]) -> Bundle:
        """
        Create a new Bundle object from valid CBOR data
        :param data: bundle data as CBOR encoded object
        :return: a bundle object constructed from the passed data
        """

        """ RFC 9171, 4.1
        […] The first block in the sequence (the first item of the array) MUST be a primary bundle
        block in CBOR encoding as described below; the bundle MUST have exactly one primary bundle
        block. […] Every block following the primary block SHALL be the CBOR encoding of a canonical
        block. The last such block MUST be a payload block; the bundle MUST have exactly one payload
        block.
        """
        blocks: List[list] = cbor2.loads(data)
        primary_block_data: list = blocks[0]

        # parse primary block
        try:
            bpcf: int = primary_block_data[1]
            crct: int = primary_block_data[2]  # noqa F841
            dst: str = primary_block_data[3][1]
            src: str = primary_block_data[4][1]
            rpt: str = primary_block_data[5][1]
            tst: int = primary_block_data[6][0]
            seq: int = primary_block_data[6][1]
            lft: int = primary_block_data[7]
        except IndexError as e:
            raise IndexError(f"Passed CBOR data is not a valid bundle: {e}")

        prim_blk: _PrimaryBlock = _PrimaryBlock(
            source=src,
            destination=dst,
            bundle_proc_control_flags=_BundleProcCtrlFlags(bpcf),
            timestamp=tst,
            sequence_number=seq,
            report_to=rpt,
            lifetime=lft,
        )

        can_blks: List[_CanonicalBlock] = []
        for blk_data in blocks[1:]:
            parsed_block_type: Type[_CanonicalBlock]
            try:
                blt: int = blk_data[0]
                blnr = blk_data[1]
                bpcf = blk_data[2]
                crct = blk_data[3]  # noqa F841
                data = blk_data[4]
                crc: Optional[str] = None  # noqa F841
            except IndexError as e:
                raise IndexError(f"Passed CBOR data is not a valid bundle: {e}")

            if blt == 1:
                parsed_block_class = _PayloadBlock
            elif blt == 6:
                parsed_block_class = _PreviousNodeBlock
            elif blt == 7:
                parsed_block_class = _BundleAgeBlock
            elif blt == 10:
                parsed_block_class = _HopCountBlock
            elif 10 < blt < 192:
                raise ValueError("Block types 11 to 191 are unassigned (RFC 9171, 9.1")
            else:
                raise NotImplementedError(f"Block type {blt} not yet supported.")

            can_blks.append(
                parsed_block_class(
                    block_number=blnr,
                    block_proc_control_flags=_BlockProcCtrlFlags(bpcf),
                    data=data,
                )
            )

        return Bundle(
            primary_block=prim_blk,
            canonical_blocks=can_blks,
            data=data,
        )

    @property
    def payload_block(self):
        return self._canonical_blocks[-1]

    @property
    def primary_block(self):
        return self._primary_block

    @property
    def bundle_id(self):
        return f"dtn:{self._primary_block.source}-{self._primary_block.timestamp}-{self._primary_block.sequence_number}"

    @property
    def source(self):
        return self._primary_block.source

    @property
    def destination(self):
        return self._primary_block.destination

    @property
    def timestamp(self):
        return self._primary_block.timestamp

    @property
    def sequence_number(self):
        return self._primary_block.sequence_number

    @staticmethod
    def to_cbor(bundle: Bundle) -> bytes:
        """
        Returns the valid CBOR representation of a Bundle object
        :param bundle: the bundle to encode
        :return: a CBOR byte-string of the passed Bundle object
        """
        raise NotImplementedError(
            "Since I'm still a little undecided on the implementation details."
        )

    def add_block_type(self, block_type: int):
        if block_type == 1:
            raise ValueError("Only exactly 1 payload block allowed in bundle (RFC 9171, 4.1)")
        elif block_type == 6:
            if self._has_block(_PreviousNodeBlock):
                raise ValueError(
                    "Only exactly 1 previous node block allowed in bundle (RFC 9171, 4.4.1)"
                )
            self.canonical_blocks.append(_PreviousNodeBlock())
        elif block_type == 7:
            if self._has_block(_BundleAgeBlock):
                raise ValueError(
                    "Only exactly 1 bundle age block allowed in bundle (RFC 9171, 4.4.2)"
                )
            self.canonical_blocks.append(_BundleAgeBlock())
        elif block_type == 10:
            if self._has_block(_HopCountBlock):
                raise ValueError(
                    "Only exactly 1 hop-count block allowed in bundle (RFC 9171, 4.4.3)"
                )
            self.canonical_blocks.append(_HopCountBlock())
        elif 10 < block_type < 192:
            raise ValueError("Block types 11 to 191 are unassigned (RFC 9171, 9.1")
        else:
            raise NotImplementedError(f"Block type {block_type} not yet supported.")

    def _has_block(self, block_type: Type[_CanonicalBlock]):
        return any([isinstance(block, block_type) for block in self.canonical_blocks])

    def __repr__(self) -> str:
        ret: List[_Block] = [self._primary_block]
        return str(ret + self._canonical_blocks)
