# for postponed evaluation of annotation of Bundle.from_cbor()
# more info: https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABC
from typing import Optional, Type, List

try:
    from cbor2 import loads
except ImportError:
    from cbor import loads

from py_dtn7.utils import from_dtn_timestamp


CRC_TYPE_NOCRC = 0
CRC_TYPE_X25 = 1
CRC_TYPE_CRC32C = 2


class BundleProcCtrlFlags:
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


class BlockProcCtrlFlags:
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


class Block(ABC):
    pass


class PrimaryBlock(Block):
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

    def __init__(
            self,
            version: int,
            bundle_proc_control_flags: BundleProcCtrlFlags,
            crc_type: int,
            destination_scheme: int,
            destination_specific_part: str,
            source_scheme: int,
            source_specific_part: str,
            report_to_scheme: int,
            report_to_specific_part: str,
            bundle_creation_time: int,
            sequence_number: int,
            lifetime: int = 1000 * 3600 * 24,
            fragment_offset: int = None,
            total_application_data_unit_length: int = None,
            crc=None
    ):
        self.version = version
        self.bundle_proc_ctrl_flags = bundle_proc_control_flags
        self.crc_type = crc_type
        self.destination_scheme = destination_scheme
        self.destination_specific_part = destination_specific_part
        self.source_scheme = source_scheme
        self.source_specific_part = source_specific_part
        self.report_to_scheme = report_to_scheme
        self.report_to_specific_part = report_to_specific_part
        self.bundle_creation_time = bundle_creation_time
        self.sequence_number = sequence_number
        self.lifetime = lifetime

        self.bundle_creation_time_datetime = from_dtn_timestamp(bundle_creation_time)

    def __repr__(self) -> str:
        return '<PrimaryBlock: [{}, {}, {}, [{}, "{}"], [{}, "{}"], [{}, "{}"], {}, {}, {}]>'.format(
            self.version,
            self.bundle_proc_ctrl_flags,
            self.crc_type,
            self.destination_scheme,
            self.destination_specific_part,
            self.source_scheme,
            self.source_specific_part,
            self.report_to_scheme,
            self.report_to_specific_part,
            self.bundle_creation_time,
            self.sequence_number,
            self.lifetime
        )

    @staticmethod
    def from_block_data(primary_block: list) -> PrimaryBlock:
        try:
            return PrimaryBlock(
                version=primary_block[0],
                bundle_proc_control_flags=BundleProcCtrlFlags(primary_block[1]),
                crc_type=primary_block[2],
                destination_scheme=primary_block[3][0],
                destination_specific_part=primary_block[3][1],
                source_scheme=primary_block[4][0],
                source_specific_part=primary_block[4][1],
                report_to_scheme=primary_block[5][0],
                report_to_specific_part=primary_block[5][1],
                bundle_creation_time=primary_block[6][0],
                sequence_number=primary_block[6][1],
                lifetime=primary_block[7]
            )
        except IndexError as e:
            raise IndexError('Passed CBOR data is not a valid bundle: {}'.format(e))


class CanonicalBlock(Block, ABC):
    _block_type: int
    _block_number: int
    _block_proc_ctrl_flags: BlockProcCtrlFlags
    _crc_type: int
    _data: bytes
    _crc: Optional[str]

    def __init__(
        self,
        block_proc_control_flags: BlockProcCtrlFlags,
        data: bytes,
        block_number: int = 0,
        crc_type: int = CRC_TYPE_NOCRC,
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
    def block_proc_ctrl_flags(self) -> BlockProcCtrlFlags:
        return self._block_proc_ctrl_flags

    @property
    def crc_type(self) -> int:
        return self._crc_type

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def crc(self) -> Optional[str]:
        return self._crc

    def __repr__(self) -> str:
        return '<{}: [{}, {}, {}, {}]>'.format(
            self.__class__.__name__, self._block_number, self._block_proc_ctrl_flags, self._crc_type, self._data
        )


class PayloadBlock(CanonicalBlock):
    def __init__(
        self,
        block_proc_control_flags: BlockProcCtrlFlags,
        data: bytes,
        block_number: int = 0,
        crc_type: int = CRC_TYPE_NOCRC,
        crc: Optional[str] = None,
    ):
        super().__init__(block_proc_control_flags, data, block_number, crc_type, crc)
        self._block_type = 1


class PreviousNodeBlock(CanonicalBlock):
    _block_type = 6
    forwarder_id: str = ""


class BundleAgeBlock(CanonicalBlock):
    _block_type = 7
    age: int = 0


class HopCountBlock(CanonicalBlock):
    _block_type = 10
    hop_limit: int = 0
    hop_count: int = 0


class Bundle:
    _primary_block: PrimaryBlock
    _canonical_blocks: List[CanonicalBlock]
    _data: Optional[bytes]

    def __init__(
        self,
        primary_block: PrimaryBlock,
        canonical_blocks: List[CanonicalBlock],
        data: Optional[bytes] = None,
    ):
        self._primary_block = primary_block
        self._canonical_blocks = canonical_blocks
        self._data = data

    @staticmethod
    def from_cbor(data: bytes):
        blocks: List[list] = loads(data)
        return Bundle.from_block_data(blocks)

    @staticmethod
    def from_block_data(blocks: list) -> Bundle:
        """
        Create a new Bundle object from valid CBOR data
        :param blocks: bundle data as CBOR decoded block list
        :return: a bundle object constructed from the passed data
        """

        """ RFC 9171, 4.1
        […] The first block in the sequence (the first item of the array) MUST be a primary bundle
        block in CBOR encoding as described below; the bundle MUST have exactly one primary bundle
        block. […] Every block following the primary block SHALL be the CBOR encoding of a canonical
        block. The last such block MUST be a payload block; the bundle MUST have exactly one payload
        block.
        """
        prim_blk: PrimaryBlock = PrimaryBlock.from_block_data(blocks[0])

        data = None

        can_blks: List[CanonicalBlock] = []
        for blk_data in blocks[1:]:
            parsed_block_type: Type[CanonicalBlock]
            try:
                blt: int = blk_data[0]
                blnr = blk_data[1]
                bundle_proc_control_flags = blk_data[2]
                crct = blk_data[3]  # noqa F841
                data = blk_data[4]
                crc: Optional[str] = None  # noqa F841
            except IndexError as e:
                raise IndexError(f"Passed CBOR data is not a valid bundle: {e}")

            if blt == 1:
                parsed_block_class = PayloadBlock
            elif blt == 6:
                parsed_block_class = PreviousNodeBlock
            elif blt == 7:
                parsed_block_class = BundleAgeBlock
            elif blt == 10:
                parsed_block_class = HopCountBlock
            elif 10 < blt < 192:
                raise ValueError("Block types 11 to 191 are unassigned (RFC 9171, 9.1")
            else:
                raise NotImplementedError(f"Block type {blt} not yet supported.")

            can_blks.append(
                parsed_block_class(
                    block_number=blnr,
                    block_proc_control_flags=BlockProcCtrlFlags(bundle_proc_control_flags),
                    data=data,
                )
            )

        return Bundle(
            primary_block=prim_blk,
            canonical_blocks=can_blks,
            data=data,
        )

    @property
    def payload_block(self) -> CanonicalBlock:
        """
        :return: the payload block of the bundle
        """
        return self._canonical_blocks[-1]

    @property
    def primary_block(self) -> PrimaryBlock:
        """
        :return: the primary block of the bundle
        """
        return self._primary_block

    @property
    def bundle_id(self) -> str:
        """
        :return: the bundle ID of the bundle
        """
        return f"dtn:{self._primary_block.source_specific_part}-{self._primary_block.bundle_creation_time}-{self._primary_block.sequence_number}"

    @property
    def source(self) -> str:
        """
        :return: the source field of the bundle (from the primary block)
        """
        return self._primary_block.source_specific_part

    @property
    def destination(self) -> str:
        """
        :return: the destination field of the bundle (from the primary block)
        """
        return self._primary_block.destination_specific_part

    @property
    def timestamp(self) -> int:
        """
        :return: the DTN timestamp of the bundle (from the primary block)
        """
        return self._primary_block.bundle_creation_time

    @property
    def sequence_number(self) -> int:
        """
        :return: the sequence number of the bundle (from the primary block)
        """
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

    def add_block_type(self, block_type: int) -> None:
        """
        Adds and empty block of the following types to the bundle:

             6: Previous Node Block
             7: Bundle Age Block
            10: Hop Count Block

        :param block_type: the type of block to add (see RFC 9171)
        :return: None
        """
        if block_type == 1:
            raise ValueError("Only exactly 1 payload block allowed in bundle (RFC 9171, 4.1)")
        elif block_type == 6:
            if self._has_block(PreviousNodeBlock):
                raise ValueError(
                    "Only exactly 1 previous node block allowed in bundle (RFC 9171, 4.4.1)"
                )
            self._canonical_blocks.append(PreviousNodeBlock())
        elif block_type == 7:
            if self._has_block(BundleAgeBlock):
                raise ValueError(
                    "Only exactly 1 bundle age block allowed in bundle (RFC 9171, 4.4.2)"
                )
            self._canonical_blocks.append(BundleAgeBlock())
        elif block_type == 10:
            if self._has_block(HopCountBlock):
                raise ValueError(
                    "Only exactly 1 hop-count block allowed in bundle (RFC 9171, 4.4.3)"
                )
            self._canonical_blocks.append(HopCountBlock())
        elif 10 < block_type < 192:
            raise ValueError("Block types 11 to 191 are unassigned (RFC 9171, 9.1")
        else:
            raise NotImplementedError(f"Block type {block_type} not yet supported.")

    def _has_block(self, block_type: Type[CanonicalBlock]) -> bool:
        """
        Returns true if a block of `block_type` is contained in Bundle
        :param block_type: type of block
        :return: boolean
        """
        return any([isinstance(block, block_type) for block in self._canonical_blocks])

    def __repr__(self) -> str:
        ret: List[Block] = [self._primary_block]
        return str(ret + self._canonical_blocks)
