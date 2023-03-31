# for postponed evaluation of annotation of Bundle.from_cbor()
# more info: https://stackoverflow.com/a/33533514
from __future__ import annotations

from abc import ABC
from typing import Optional, List, Tuple

from py_dtn7.utils import from_dtn_timestamp, RUNNING_MICROPYTHON

if not RUNNING_MICROPYTHON:
    from cbor2 import dumps, loads
else:
    from cbor import dumps, loads

CRC_TYPE_NOCRC = 0
CRC_TYPE_X25 = 1
CRC_TYPE_CRC32C = 2

URI_SCHEME_1 = "dtn"
URI_SCHEME_2 = "ipn"

ENCODING = "utf-8"


class Flags:
    flags: int = 0  # repr ignores all class attributes, so flags also needs to be one

    def __init__(self, flags: int = 0):
        self.flags = flags

    def get_flag(self, bit: int) -> bool:
        return bool((self.flags >> bit) & 1)

    def set_flag(self, bit: int):
        self.flags |= 1 << bit

    def unset_flag(self, bit: int):
        self.flags &= ~(1 << bit)

    def __repr__(self):
        return hex(self.flags)

    def __str__(self):
        result = "<{}: [".format(self.__class__.__name__)

        attributes_to_ignore = dir(Flags)

        for attribute in dir(self):
            if attribute not in attributes_to_ignore:
                result += "{}: {}, ".format(attribute, getattr(self, attribute))

        return result[:-2] + "]>"


class BundleProcessingControlFlags(Flags):
    """
    4.2.3. Bundle Processing Control Flags
    Bundle processing control flags assert properties of the bundle as a whole rather than of any
    particular block of the bundle. They are conveyed in the primary block of the bundle.
    """

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


class PrimaryBlock:
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
        fragment_offset: Optional[int] = None,
        total_application_data_unit_length: Optional[int] = None,
        crc=None,
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

        if version != 7:
            raise NotImplementedError(
                "bundles with other versions than 7 are currently not supported"
            )

        for scheme in (destination_scheme, source_scheme, report_to_scheme):
            self.check_uri_scheme(scheme)

    def __repr__(self) -> str:
        return (
            '<PrimaryBlock: [{}, {}, {}, [{}, "{}"], [{}, "{}"], [{}, "{}"], {}, {}, {}]>'.format(
                self.version,
                repr(self.bundle_processing_control_flags),
                self.crc_type,
                self.destination_scheme,
                self.destination_specific_part,
                self.source_scheme,
                self.source_specific_part,
                self.report_to_scheme,
                self.report_to_specific_part,
                self.bundle_creation_time,
                self.sequence_number,
                self.lifetime,
            )
        )

    @staticmethod
    def from_block_data(primary_block: list) -> PrimaryBlock:
        """
        length of array may be:
            8 if the bundle is not a fragment and has no CRC,
            9 if the bundle is not a fragment and has a CRC,
            10 if the bundle is a fragment and has no CRC,
            11 if the bundle is a fragment and has a CRC
        """
        if len(primary_block) < 8 or len(primary_block) > 11:
            raise IndexError(
                "primary block has invalid number of items: {}, should be in [8, 11]".format(
                    len(primary_block)
                )
            )
        if 9 <= len(primary_block) <= 11:
            raise NotImplementedError("bundles with CRC and fragments are not implemented yet")

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
                lifetime=primary_block[7],
            )
        except IndexError as e:
            raise IndexError("Passed CBOR data is not a valid bundle: {}".format(e))

    def to_block_data(self):
        return (
            self.version,
            self.bundle_processing_control_flags.flags,
            self.crc_type,
            (self.destination_scheme, self.destination_specific_part),
            (self.source_scheme, self.source_specific_part),
            (self.report_to_scheme, self.report_to_specific_part),
            (self.bundle_creation_time, self.sequence_number),
            self.lifetime,
        )

    @staticmethod
    def from_objects(
        bundle_processing_control_flags: BundleProcessingControlFlags = BundleProcessingControlFlags(
            0
        ),
        destination_scheme: int = 1,
        destination_specific_part: str = "",
        source_scheme: int = 1,
        source_specific_part: str = "",
        report_to_scheme: int = 1,
        report_to_specific_part: str = "",
        bundle_creation_time: int = 0,
        sequence_number: int = 0,
        lifetime: int = 3600 * 24 * 1000,
    ):
        return PrimaryBlock(
            version=7,
            bundle_processing_control_flags=bundle_processing_control_flags,
            crc_type=0,
            destination_scheme=destination_scheme,
            destination_specific_part=destination_specific_part,
            source_scheme=source_scheme,
            source_specific_part=source_specific_part,
            report_to_scheme=report_to_scheme,
            report_to_specific_part=report_to_specific_part,
            bundle_creation_time=bundle_creation_time,
            sequence_number=sequence_number,
            lifetime=lifetime,
        )

    @property
    def bundle_creation_time_datetime(self):
        return from_dtn_timestamp(self.bundle_creation_time)

    @staticmethod
    def check_uri_scheme(scheme: int):
        if scheme == 0:
            raise IndexError("bundle uses reserved uri scheme 0")
        elif 3 <= scheme <= 254:
            raise IndexError("bundle uses unassigned uri scheme {}".format(scheme))
        elif 255 <= scheme <= 65535:
            raise IndexError("bundle uses reserved uri scheme {}".format(scheme))
        elif scheme > 65535:
            raise IndexError("bundle uses unknown private uri scheme {}".format(scheme))

    @staticmethod
    def scheme_to_uri(scheme: int):
        if scheme == 1:
            return URI_SCHEME_1
        elif scheme == 2:
            return URI_SCHEME_2
        else:
            raise IndexError("unknown uri scheme {}".format(scheme))

    @property
    def full_source_uri(self):
        return "{}:{}".format(
            PrimaryBlock.scheme_to_uri(self.source_scheme), self.source_specific_part
        )

    @property
    def full_destination_uri(self):
        return "{}:{}".format(
            PrimaryBlock.scheme_to_uri(self.destination_scheme), self.destination_specific_part
        )

    @property
    def full_report_to_uri(self):
        return "{}:{}".format(
            PrimaryBlock.scheme_to_uri(self.report_to_scheme), self.report_to_specific_part
        )


class CanonicalBlock(ABC):
    def __init__(
        self,
        block_type_code: int,
        block_number: int,
        block_processing_control_flags: BlockProcessingControlFlags,
        crc_type: int,
        data: bytes,
        crc=None,
    ):
        self.block_type_code = block_type_code
        self.block_number = block_number
        self.block_processing_control_flags = block_processing_control_flags
        self.crc_type = crc_type
        self.data = data

    def __repr__(self) -> str:
        return "<{}: [{}, {}, {}, {}, {}]>".format(
            self.__class__.__name__,
            self.block_type_code,
            self.block_number,
            repr(self.block_processing_control_flags),
            self.crc_type,
            self.data,
        )

    @staticmethod
    def from_block_data(block: list) -> CanonicalBlock:
        # todo: move checks to init

        """
        length of the array may be:
            5 if the block has no CRC
            6 if the block has CRC
        """
        if len(block) < 5 or len(block) > 6:
            raise IndexError(
                "block has invalid number of items: {}, should be in [5, 6]".format(len(block))
            )
        if len(block) == 6:
            raise NotImplementedError("Canonical blocks with CRC are not implemented yet")

        block_type = block[0]

        if block_type == 1:
            cls = PayloadBlock
        elif block_type == 6:
            cls = PreviousNodeBlock
        elif block_type == 7:
            cls = BundleAgeBlock
        elif block_type == 10:
            cls = HopCountBlock
        elif 11 <= block_type <= 191:
            print(
                "warning: unassigned block type {} used without a dedicated implementation".format(
                    block_type
                )
            )
            cls = CanonicalBlock
        elif 192 <= block_type <= 255:
            print(
                "info: experimental block type {} used without a dedicated implementation".format(
                    block_type
                )
            )
            cls = CanonicalBlock
        else:
            raise NotImplementedError(
                "block type {} from another bundle protocol version is not supported".format(
                    block_type
                )
            )

        return cls(
            block_type_code=block[0],
            block_number=block[1],
            block_processing_control_flags=BlockProcessingControlFlags(block[2]),
            crc_type=block[3],
            data=block[4],
        )

    def to_block_data(self) -> tuple:
        return (
            self.block_type_code,
            self.block_number,
            self.block_processing_control_flags.flags,
            self.crc_type,
            self.data,
        )


class PayloadBlock(CanonicalBlock):
    """
    Block to simply transport the payload data.
    Provides no definition about the transported payload data.
    """

    @staticmethod
    def from_objects(
        data: bytes,
        block_processing_control_flags: BlockProcessingControlFlags = BlockProcessingControlFlags(
            0
        ),
    ):
        return PayloadBlock(
            block_type_code=1,
            block_number=1,
            block_processing_control_flags=block_processing_control_flags,
            crc_type=0,
            data=data,
            crc=None,
        )


class PreviousNodeBlock(CanonicalBlock):
    """
    Block payload-data contains the node id of the previous node that forwarded hte bundle to this node.

    Occurrences:
    Never if the local node is the source of the bundle.
    At most once in a bundle otherwise.
    """

    @property
    def previous_node_id(self) -> Tuple[int, str]:
        """
        :return: the node-id of the previous node as string
        """
        return loads(self.data)

    @staticmethod
    def from_objects(
        node_id: Tuple[int, str],
        block_processing_control_flags: BlockProcessingControlFlags = BlockProcessingControlFlags(
            0
        ),
    ):
        return PreviousNodeBlock(
            block_type_code=6,
            block_number=1,
            block_processing_control_flags=block_processing_control_flags,
            crc_type=0,
            data=dumps(node_id),
            crc=None,
        )


class BundleAgeBlock(CanonicalBlock):
    """
    Block payload-data contains an unsigned integer that represents the elapsed time (in milliseconds) between
    the time the bundle was created and the time at which it was most recently forwarded.

    Every intermediate node adds their internal processing time, as well the receiving-transmission time.
    (Although it is not defined in the standard it is my assumption that the receiving node adds the transmission time)

    Occurrences:
    Exactly once in a bundle if the creation time is zero.
    At most once in a bundle if the creation time is not zero.
    """

    @property
    def age_milliseconds(self) -> int:
        """
        :return: the transmission time in milliseconds since creation of the bundle
        """
        return loads(self.data)

    @age_milliseconds.setter
    def age_milliseconds(self, value: int):
        self.data = dumps(value)

    @staticmethod
    def from_objects(
        age_milliseconds: int = 0,
        block_processing_control_flags: BlockProcessingControlFlags = BlockProcessingControlFlags(
            0
        ),
    ):
        return BundleAgeBlock(
            block_type_code=7,
            block_number=1,
            block_processing_control_flags=block_processing_control_flags,
            crc_type=0,
            data=dumps(age_milliseconds),
            crc=None,
        )


class HopCountBlock(CanonicalBlock):
    """
    Block payload-data contains two unsigned integers representing the hop limit and current hop count of a bundle.

    The hop limit must be in range 1 to 255.
    The hop count must be increased by one before leaving a node.
    A bundle which exceeds its hop limit should be deleted for the reason "Hop limit exceeded".

    Occurrences:
    At most once in a bundle.
    """

    @property
    def hop_limit(self) -> int:
        """
        :return: the bundles hop limit represented by an unsigned integer
        """
        return loads(self.data)[0]

    @property
    def hop_count(self) -> int:
        """
        :return: the bundles current hop count up until received by this node
        """
        return loads(self.data)[1]

    @hop_count.setter
    def hop_count(self, value: int):
        arr = loads(self.data)
        arr[1] = value
        self.data = dumps(arr)

    @staticmethod
    def from_objects(
        hop_limit: int,
        hop_count: int,
        block_processing_control_flags: BlockProcessingControlFlags = BlockProcessingControlFlags(
            0
        ),
    ):
        return HopCountBlock(
            block_type_code=10,
            block_number=1,
            block_processing_control_flags=block_processing_control_flags,
            crc_type=0,
            data=dumps((hop_limit, hop_count)),
            crc=None,
        )

    def __repr__(self) -> str:
        return "<{}: [{}, {}, {}, {}, [hop-limit: {}, hop-count: {}]]>".format(
            self.__class__.__name__,
            self.block_type_code,
            self.block_number,
            repr(self.block_processing_control_flags),
            self.crc_type,
            self.hop_limit,
            self.hop_count,
        )


class Bundle:
    def __init__(
        self,
        primary_block: PrimaryBlock,
        previous_node_block: Optional[PreviousNodeBlock] = None,
        bundle_age_block: Optional[BundleAgeBlock] = None,
        hop_count_block: Optional[HopCountBlock] = None,
        payload_block: Optional[PayloadBlock] = None,
        other_blocks: Optional[List[CanonicalBlock]] = None,
    ):
        self.primary_block = primary_block
        self.previous_node_block: Optional[PreviousNodeBlock] = None
        self.bundle_age_block: Optional[BundleAgeBlock] = None
        self.hop_count_block: Optional[HopCountBlock] = None
        self.payload_block: Optional[PayloadBlock] = None
        self.other_blocks: Optional[List[CanonicalBlock]] = []

        # hacky workaround to check and set a correct node numbering if needed

        if previous_node_block is not None:
            self.insert_canonical_block(previous_node_block)
        if bundle_age_block is not None:
            self.insert_canonical_block(bundle_age_block)
        if hop_count_block is not None:
            self.insert_canonical_block(hop_count_block)
        if payload_block is not None:
            self.insert_canonical_block(payload_block)
        if other_blocks is not None:
            for block in other_blocks:
                self.insert_canonical_block(block)

        if self.primary_block.bundle_creation_time == 0 and self.bundle_age_block is None:
            raise IndexError("No bundle age block given, although creation time is zero")

    @staticmethod
    def from_cbor(data: bytes) -> Bundle:
        """
        Create a new Bundle object from valid CBOR data
        :param data: bundle data as CBOR byte-string
        :return: a bundle object constructed from the passed data
        """

        blocks = loads(data)
        return Bundle.from_block_data(blocks)

    @staticmethod
    def from_block_data(blocks: list) -> Bundle:
        """
        Create a new Bundle object from valid parsed CBOR data
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
        primary_block = PrimaryBlock.from_block_data(blocks[0])

        # We exploit that other-blocks can also contain known valid blocks,
        # as all blocks are inserted through insert_canonical_block(...).
        # This removes redundant checks in this method.

        return Bundle(
            primary_block,
            other_blocks=(CanonicalBlock.from_block_data(block) for block in blocks[1:]),  # noqa
        )

    def to_cbor(self) -> bytes:
        blocks = self.to_block_data()
        # convert outer finite array to standard-conform infinite array
        return b"\x9f" + dumps(blocks)[1:] + b"\xff"

    def to_block_data(self) -> tuple:
        primary_block_tuple = (self.primary_block.to_block_data(),)
        return primary_block_tuple + tuple(
            block.to_block_data() for block in self._get_all_used_canonical_blocks()
        )

    def insert_canonical_block(self, block: CanonicalBlock):
        used_block_numbers = tuple(
            set(b.block_number for b in self._get_all_used_canonical_blocks())
        )

        new_block_number = block.block_number

        if new_block_number in used_block_numbers:
            new_block_number = 1
            while new_block_number in used_block_numbers:
                new_block_number += 1

        block.block_number = new_block_number

        self._set_canonical_block_var(block)

    def remove_block(self, block):
        if self.primary_block == block:
            self.primary_block = None
        if self.previous_node_block == block:
            self.previous_node_block = None
        if self.bundle_age_block == block:
            self.bundle_age_block = None
        if self.hop_count_block == block:
            self.hop_count_block = None
        if self.payload_block == block:
            self.payload_block = None
        if block in self.other_blocks:
            self.other_blocks.remove(block)

    @property
    def bundle_id(self) -> str:
        """
        :return: the bundle ID of the bundle
        """
        return "{}-{}-{}".format(
            self.primary_block.full_source_uri,
            self.primary_block.bundle_creation_time,
            self.primary_block.sequence_number,
        )

    def __repr__(self) -> str:
        return "<{}: {}>".format(
            self.__class__.__name__,
            [self.primary_block] + list(self._get_all_used_canonical_blocks()),
        )  # noqa

    def _get_all_used_canonical_blocks(self):
        all_canonical_blocks = (
            self.previous_node_block,
            self.bundle_age_block,
            self.hop_count_block,
            self.payload_block,
        )
        all_canonical_blocks += tuple(self.other_blocks)

        return (block for block in all_canonical_blocks if block is not None)

    def _set_canonical_block_var(self, block: CanonicalBlock):
        if isinstance(block, PreviousNodeBlock):
            if self.previous_node_block is None:
                self.previous_node_block = block
            else:
                raise IndexError("Previous node block occurs more than once")
        elif isinstance(block, BundleAgeBlock):
            if self.bundle_age_block is None:
                self.bundle_age_block = block
            else:
                raise IndexError("Bundle age block occurs more than once")
        elif isinstance(block, HopCountBlock):
            if self.hop_count_block is None:
                self.hop_count_block = block
            else:
                raise IndexError("Hop count block occurs more than once")
        elif isinstance(block, PayloadBlock):
            if self.payload_block is None:
                self.payload_block = block
            else:
                raise IndexError("Payload block occurs more than once")
        else:
            self.other_blocks.append(block)
