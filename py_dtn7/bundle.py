# for postponed evaluation of annotation of Bundle.from_cbor()
# more info: https://stackoverflow.com/a/33533514
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Self, Tuple, Union

from py_dtn7.utils import from_dtn_timestamp, RUNNING_MICROPYTHON

if not RUNNING_MICROPYTHON:
    from cbor2 import dumps, loads
else:
    from cbor import dumps, loads

CRC_TYPE_NOCRC = 0
CRC_TYPE_X25 = 1
CRC_TYPE_CRC32C = 2

URI_SCHEME_DTN_NAME = "dtn"
URI_SCHEME_DTN_ENCODED = 1
URI_SCHEME_IPN_NAME = "ipn"
URI_SCHEME_IPN_ENCODED = 2

NONE_ENDPOINT_SPECIFIC_PART_NAME = "//none"
NONE_ENDPOINT_SPECIFIC_PART_ENCODED = 0

ENCODING = "utf-8"


class Flags:
    flags: int = 0  # repr ignores all class attributes, so flags also needs to be one

    def __init__(self, flags: int = 0):
        if not isinstance(flags, int):
            raise TypeError
        self.flags = flags

    def get_flag(self, bit: int) -> bool:
        return bool((self.flags >> bit) & 1)

    def set_flag(self, bit: int):
        self.flags |= 1 << bit

    def unset_flag(self, bit: int):
        self.flags &= ~(1 << bit)

    def __repr__(self) -> str:  # pragma: no cover
        return hex(self.flags)

    def __str__(self) -> str:  # pragma: no cover
        if type(self) is Flags:
            return "[__str__ of generic 'Flags' class should not be used]"
        result = "<{}: [".format(self.__class__.__name__)

        attributes_to_ignore = dir(Flags)

        for attribute in dir(self):
            if attribute not in attributes_to_ignore:
                result += "{}: {}, ".format(attribute, getattr(self, attribute))

        return result[:-2] + "]>"

    def __eq__(self, other: Flags) -> bool:
        if not isinstance(other, Flags):
            return NotImplemented
        return self.flags == other.flags


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
        destination_specific_part: Union[str, int, List[int]],
        source_scheme: int,
        source_specific_part: Union[str, int, List[int]],
        report_to_scheme: int,
        report_to_specific_part: Union[str, int, List[int]],
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

    def __repr__(self) -> str:  # pragma: no cover
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

    def __eq__(self, other: PrimaryBlock) -> bool:
        if not isinstance(other, PrimaryBlock):
            return NotImplemented
        attrs = [
            "version",
            "bundle_processing_control_flags",
            "crc_type",
            "destination_scheme",
            "destination_specific_part",
            "source_scheme",
            "source_specific_part",
            "report_to_scheme",
            "report_to_specific_part",
            "bundle_creation_time",
            "sequence_number",
            "lifetime",
        ]
        return all([self.__getattribute__(attr) == other.__getattribute__(attr) for attr in attrs])

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
            raise ValueError(
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
            raise ValueError("Passed CBOR data is not a valid bundle: {}".format(e))

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
        full_destination_uri: str,
        full_source_uri: str = "dtn://none",
        full_report_to_uri: str = "dtn://none",
        bundle_processing_control_flags: BundleProcessingControlFlags = BundleProcessingControlFlags(
            0
        ),
        bundle_creation_time: int = 0,
        sequence_number: int = 0,
        lifetime: int = 3600 * 24 * 1000,
    ):
        primary_block = PrimaryBlock(
            version=7,
            bundle_processing_control_flags=bundle_processing_control_flags,
            crc_type=0,
            destination_scheme=URI_SCHEME_DTN_ENCODED,
            destination_specific_part="",
            source_scheme=URI_SCHEME_DTN_ENCODED,
            source_specific_part="",
            report_to_scheme=URI_SCHEME_DTN_ENCODED,
            report_to_specific_part="",
            bundle_creation_time=bundle_creation_time,
            sequence_number=sequence_number,
            lifetime=lifetime,
        )

        primary_block.full_destination_uri = full_destination_uri
        primary_block.full_source_uri = full_source_uri
        primary_block.full_report_to_uri = full_report_to_uri

        return primary_block

    @property
    def bundle_creation_time_datetime(self) -> datetime:
        return from_dtn_timestamp(self.bundle_creation_time)

    @staticmethod
    def check_uri_scheme(scheme: int) -> None:
        if scheme < 0:
            raise ValueError("bundle scheme code must be an unsigned integer")
        elif scheme == 0:
            raise ValueError("bundle uses reserved uri scheme 0")
        elif 3 <= scheme <= 254:
            raise ValueError("bundle uses unassigned uri scheme {}".format(scheme))
        elif 255 <= scheme <= 65535:
            raise ValueError("bundle uses reserved uri scheme {}".format(scheme))
        elif scheme > 65535:
            raise ValueError("bundle uses unknown private uri scheme {}".format(scheme))

    @staticmethod
    def from_full_uri(full_uri: str) -> Tuple[int, Union[str, int, List[int]]]:
        scheme, specific_part = full_uri.split(sep=":", maxsplit=1)

        if scheme == URI_SCHEME_DTN_NAME:
            if specific_part == NONE_ENDPOINT_SPECIFIC_PART_NAME:
                specific_part = NONE_ENDPOINT_SPECIFIC_PART_ENCODED

            return URI_SCHEME_DTN_ENCODED, specific_part
        elif scheme == URI_SCHEME_IPN_NAME:
            if specific_part == NONE_ENDPOINT_SPECIFIC_PART_NAME:
                specific_part = NONE_ENDPOINT_SPECIFIC_PART_ENCODED
            else:
                specific_part = tuple(int(x) for x in specific_part[2:].split("."))
                if len(specific_part) != 2 or any([x < 0 for x in specific_part]):
                    raise ValueError(
                        "IPN scheme only allows pairs of unsigned integers as endpoint IDs"
                    )
            return URI_SCHEME_IPN_ENCODED, specific_part
        else:
            raise ValueError("Invalid URI scheme name: {}".format(scheme))

    @staticmethod
    def to_full_uri(scheme: int, specific_part: Union[str, int, List[int]]) -> str:
        if scheme == URI_SCHEME_DTN_ENCODED:
            if specific_part == NONE_ENDPOINT_SPECIFIC_PART_ENCODED:
                specific_part = NONE_ENDPOINT_SPECIFIC_PART_NAME

            return "{}:{}".format(URI_SCHEME_DTN_NAME, specific_part)
        elif scheme == URI_SCHEME_IPN_ENCODED:
            if specific_part == NONE_ENDPOINT_SPECIFIC_PART_ENCODED:
                specific_part = NONE_ENDPOINT_SPECIFIC_PART_NAME
            else:
                if len(specific_part) != 2 or any([x < 0 for x in specific_part]):
                    raise ValueError(
                        "IPN scheme only allows pairs of unsigned integers as endpoint IDs"
                    )
                specific_part = "//" + ".".join(str(x) for x in specific_part)

            return "{}:{}".format(URI_SCHEME_IPN_NAME, specific_part)
        else:
            raise ValueError("Invalid URI scheme code: {}".format(scheme))

    @property
    def full_source_uri(self) -> str:
        return self.to_full_uri(self.source_scheme, self.source_specific_part)

    @full_source_uri.setter
    def full_source_uri(self, value) -> None:
        self.source_scheme, self.source_specific_part = self.from_full_uri(value)

    @property
    def full_destination_uri(self) -> str:
        return self.to_full_uri(self.destination_scheme, self.destination_specific_part)

    @full_destination_uri.setter
    def full_destination_uri(self, value) -> None:
        self.destination_scheme, self.destination_specific_part = self.from_full_uri(value)

    @property
    def full_report_to_uri(self) -> str:
        return self.to_full_uri(self.report_to_scheme, self.report_to_specific_part)

    @full_report_to_uri.setter
    def full_report_to_uri(self, value) -> None:
        self.report_to_scheme, self.report_to_specific_part = self.from_full_uri(value)


class CanonicalBlock:
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

    def __repr__(self) -> str:  # pragma: no cover
        return "<{}: [{}, {}, {}, {}, {}]>".format(
            self.__class__.__name__,
            self.block_type_code,
            self.block_number,
            repr(self.block_processing_control_flags),
            self.crc_type,
            self.data,
        )

    def __eq__(self, other: CanonicalBlock) -> bool:
        if not isinstance(other, CanonicalBlock):
            return NotImplemented
        if self.__class__ is not other.__class__:
            return False
        attrs = [
            "block_type_code",
            "block_number",
            "block_processing_control_flags",
            "crc_type",
            "data",
        ]
        return all([self.__getattribute__(attr) == other.__getattribute__(attr) for attr in attrs])

    @classmethod
    def from_block_data(cls, block: list) -> CanonicalBlock:
        # todo: move checks to init

        """
        length of the array may be:
            5 if the block has no CRC
            6 if the block has CRC
        """
        if len(block) < 5 or len(block) > 6:
            raise ValueError(
                "block has invalid number of items: {}, should be in [5, 6]".format(len(block))
            )
        if len(block) == 6:
            raise NotImplementedError("Canonical blocks with CRC are not implemented yet")

        block_type = block[0]

        if block_type == 1:
            if cls is not CanonicalBlock and cls is not PayloadBlock:
                raise ValueError("'block_type_code' 1 not correct for instantiating {}".format(cls))
            cls = PayloadBlock
        elif block_type == 6:
            if cls is not CanonicalBlock and cls is not PreviousNodeBlock:
                raise ValueError("'block_type_code' 6 not correct for instantiating {}".format(cls))
            cls = PreviousNodeBlock
        elif block_type == 7:
            if cls is not CanonicalBlock and cls is not BundleAgeBlock:
                raise ValueError("'block_type_code' 7 not correct for instantiating {}".format(cls))
            cls = BundleAgeBlock
        elif block_type == 10:
            if cls is not CanonicalBlock and cls is not HopCountBlock:
                raise ValueError(
                    "'block_type_code' 10 not correct for instantiating {}".format(cls)
                )
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
    def previous_node_id(self) -> Tuple[int, Union[str, int, List[int]]]:
        """
        :return: the node-id of the previous node as string
        """
        return loads(self.data)

    @staticmethod
    def from_objects(
        full_node_uri: str,
        block_processing_control_flags: BlockProcessingControlFlags = BlockProcessingControlFlags(
            0
        ),
    ):
        return PreviousNodeBlock(
            block_type_code=6,
            block_number=1,
            block_processing_control_flags=block_processing_control_flags,
            crc_type=0,
            data=dumps(PrimaryBlock.from_full_uri(full_node_uri)),
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

    def __repr__(self) -> str:  # pragma: no cover
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
    """
    Standard BP7 Bundle implementation.

    This implementation is not thread-safe!
    """

    def __init__(
        self,
        primary_block: PrimaryBlock,
        previous_node_block: Optional[PreviousNodeBlock] = None,
        bundle_age_block: Optional[BundleAgeBlock] = None,
        hop_count_block: Optional[HopCountBlock] = None,
        payload_block: Optional[PayloadBlock] = None,
        other_blocks: Optional[List[CanonicalBlock]] = [],
    ):
        self.primary_block = primary_block
        self.previous_node_block: Optional[PreviousNodeBlock] = None
        self.bundle_age_block: Optional[BundleAgeBlock] = None
        self.hop_count_block: Optional[HopCountBlock] = None
        self.payload_block: Optional[PayloadBlock] = None
        self.other_blocks: Optional[List[CanonicalBlock]] = []

        self._cur_block_number = 2
        self._block_type_dict = {
            PreviousNodeBlock: "previous_node_block",
            BundleAgeBlock: "bundle_age_block",
            HopCountBlock: "hop_count_block",
            PayloadBlock: "payload_block",
            CanonicalBlock: "other_blocks",
        }

        for block in [
            previous_node_block,
            bundle_age_block,
            hop_count_block,
            payload_block,
            *other_blocks,
        ]:
            if block is not None:
                self.insert_canonical_block(block)

        if self.primary_block.bundle_creation_time == 0 and self.bundle_age_block is None:
            raise ValueError("No bundle age block given, although creation time is zero")

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

        oblocks = [CanonicalBlock.from_block_data(block) for block in blocks[1:]]
        return Bundle(
            primary_block,
            other_blocks=oblocks,  # noqa
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
        # overwrite block number with correct value
        if isinstance(block, PayloadBlock):
            block.block_number = 1
        else:
            block.block_number = self._cur_block_number
            self._cur_block_number += 1  # TBD: make this thread-safe

        # assign block to appropriate field
        block_type = type(block)  # returns exact type
        try:
            block_field = self._block_type_dict[block_type]
        except KeyError:
            raise ValueError("Unknown block type '{}'.".format(block_type.__name__))
        if block_type is not CanonicalBlock:
            if getattr(self, block_field) is None:
                setattr(self, block_field, block)
            else:
                raise ValueError(format("{} already present in this bundle", block_type.__name__))
        else:
            try:
                self.other_blocks.append(block)
            except AttributeError:  # self.other_blocks is probably None
                self.other_blocks = [block]

    def remove_block(self, block):
        if self.primary_block == block:
            self.primary_block = None
        elif self.previous_node_block == block:
            self.previous_node_block = None
        elif self.bundle_age_block == block:
            self.bundle_age_block = None
        elif self.hop_count_block == block:
            self.hop_count_block = None
        elif self.payload_block == block:
            self.payload_block = None
        elif block in self.other_blocks:
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

    def __repr__(self) -> str:  # pragma: no cover
        return "<{}: {}>".format(
            self.__class__.__name__,
            [self.primary_block] + list(self._get_all_used_canonical_blocks()),
        )  # noqa

    def __eq__(self, other: Bundle) -> bool:
        if self.__class__ is not other.__class__:
            return False
        attrs = [
            "primary_block",
            "previous_node_block",
            "bundle_age_block",
            "hop_count_block",
            "payload_block",
            # other_blocks needs to be handled seperately
        ]
        # other_blocks have to be the same but not in the same order
        other_equal = all(b in other.other_blocks for b in self.other_blocks) and all(
            b in self.other_blocks for b in other.other_blocks
        )
        return other_equal and all(
            [self.__getattribute__(attr) == other.__getattribute__(attr) for attr in attrs]
        )

    def _get_all_used_canonical_blocks(self):
        all_canonical_blocks = (
            self.previous_node_block,
            self.bundle_age_block,
            self.hop_count_block,
            self.payload_block,
        )
        all_canonical_blocks += tuple(self.other_blocks)

        return (block for block in all_canonical_blocks if block is not None)
