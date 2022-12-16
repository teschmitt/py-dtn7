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


class Flags:
    def __init__(self, flags: int):
        self.flags = flags

    def get_flag(self, bit: int) -> bool:
        return bool((self.flags >> bit) & 1)

    def set_flag(self, bit: int):
        self.flags |= 1 << bit

    def unset_flag(self, bit: int):
        self.flags &= ~(1 << bit)

    def __repr__(self):
        return hex(self.flags)


class BundleProcessingControlFlags(Flags):
    """
    4.2.3. Bundle Processing Control Flags
    Bundle processing control flags assert properties of the bundle as a whole rather than of any
    particular block of the bundle. They are conveyed in the primary block of the bundle.
    """

    def __init__(self, flags: int):
        super().__init__(flags)

    @property
    def is_fragment(self) -> bool:
        """
        :return: True if the bundle is a fragment
        """
        return self.get_flag(0)

    @property
    def payload_is_admin_record(self) -> bool:
        """
        :return: True if the bundle's payload is an administrative record
        """
        return self.get_flag(1)

    @property
    def do_not_fragment(self) -> bool:
        """
        :return: True if the bundle must not be fragmented
        """
        return self.get_flag(2)

    @property
    def reserved_3_to_4(self) -> int:
        """
        :return: shift to zero of bits 3 and 4 that are reserved for future use
        """
        return (self.flags >> 3) & 3

    @property
    def acknowledgement_is_requested(self) -> bool:
        """
        :return: True if acknowledgment by the user application is requested
        """
        return self.get_flag(5)

    @property
    def status_time_is_requested(self) -> bool:
        """
        :return: True if status time is requested in all status reports
        """
        return self.get_flag(6)

    @property
    def reserved_7_to_13(self) -> int:
        """
        :return: shift to zero of bits 7 to 13 that are reserved for future use
        """
        return (self.flags >> 7) & 127

    @property
    def status_of_report_reception_is_requested(self) -> bool:
        """
        :return: True if status reporting of bundle reception is requested
        """
        return self.get_flag(14)

    @property
    def reserved_15(self) -> bool:
        """
        :return: value of bit 15 that is reserved for future use
        """
        return self.get_flag(15)

    @property
    def status_of_report_forwarding_is_requested(self) -> bool:
        """
        :return: True if status reporting of bundle forwarding is requested
        """
        return self.get_flag(16)

    @property
    def status_of_report_delivery_is_requested(self) -> bool:
        """
        :return: True if status reporting of bundle delivery is requested
        """
        return self.get_flag(17)

    @property
    def status_of_report_deletion_is_requested(self) -> bool:
        """
        :return: True if status reporting of bundle deletion is requested
        """
        return self.get_flag(18)

    @property
    def reserved_19_to_20(self) -> int:
        """
        :return: shift to zero of bits 19 and 20 that are reserved for future use
        """
        return (self.flags >> 19) & 3

    @property
    def unassigned_21_to_63(self) -> int:
        """
        :return: shift to zero of bits 21 to 63 that are unassigned
        (shifted because hardware with resource constraints may only support 32bit integers)
        """
        return self.flags >> 21


class BlockProcessingControlFlags(Flags):

    def __init__(self, flags: int):
        super().__init__(flags)

    @property
    def block_must_be_replicated(self) -> bool:
        """
        :return: True if block must be replicated in every fragment
        """
        return self.get_flag(0)

    @property
    def report_status_if_block_cant_be_processed(self) -> bool:
        """
        :return: True if status report must be transmitted if block can't be processed
        """
        return self.get_flag(1)

    @property
    def delete_bundle_if_block_cant_be_processed(self) -> bool:
        """
        :return: True if bundle shall be deleted if block can't be processed
        """
        return self.get_flag(2)

    @property
    def reserved_3(self) -> bool:
        """
        :return: value of bit 3 that is reserved for future use
        """
        return self.get_flag(3)

    @property
    def discard_block_if_block_cant_be_processed(self) -> bool:
        """
        :return: True if block shall be discarded of block can't be processed
        """
        return self.get_flag(4)

    @property
    def reserved_5_to_6(self) -> int:
        """
        :return: value of bits 5 and 6 that are reserved for future use
        """
        return (self.flags >> 5) & 3

    @property
    def unassigned_7_to_63(self) -> int:
        """
        :return: value of bits 7 to 63 that are unassigned
        """
        return self.flags >> 7


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
            bundle_processing_control_flags: BundleProcessingControlFlags,
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
        self.bundle_processing_control_flags = bundle_processing_control_flags
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

    def __repr__(self) -> str:
        return '<PrimaryBlock: [{}, {}, {}, [{}, "{}"], [{}, "{}"], [{}, "{}"], {}, {}, {}]>'.format(
            self.version,
            self.bundle_processing_control_flags,
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
                bundle_processing_control_flags=BundleProcessingControlFlags(primary_block[1]),
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

    @property
    def bundle_creation_time_datetime(self):
        return from_dtn_timestamp(self.bundle_creation_time)


class CanonicalBlock(Block, ABC):
    _block_type: int
    _block_number: int
    _crc_type: int
    _data: bytes
    _crc: Optional[str]

    def __init__(
        self,
        block_processing_control_flags: BlockProcessingControlFlags,
        data: bytes,
        block_number: int = 0,
        crc_type: int = CRC_TYPE_NOCRC,
        crc: Optional[str] = None,
    ):
        self._block_type = -1
        self._block_number = block_number
        self.block_processing_control_flags = block_processing_control_flags
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
            self.__class__.__name__, self._block_number, self.block_processing_control_flags, self._crc_type, self._data
        )


class PayloadBlock(CanonicalBlock):
    def __init__(
        self,
        block_processing_control_flags: BlockProcessingControlFlags,
        data: bytes,
        block_number: int = 0,
        crc_type: int = CRC_TYPE_NOCRC,
        crc: Optional[str] = None,
    ):
        super().__init__(block_processing_control_flags, data, block_number, crc_type, crc)
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
                bundle_processing_control_flags = blk_data[2]
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
                    block_processing_control_flags=BlockProcessingControlFlags(bundle_processing_control_flags),
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
