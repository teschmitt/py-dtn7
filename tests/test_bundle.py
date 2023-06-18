from copy import deepcopy
import mock
from unittest import TestCase

from py_dtn7.bundle import *

BUNDLE_CREATION_TIME: int = (3600 * 24 * 31 + 3600 * 9) * 1000  # 2000-01-31 09:00:00 +0000 (UTC)
BUNDLE_LIFETIME: int = 1337 * 1000  # 1337 seconds
CONTROL_FLAGS = 42
DESTINATION_SPECIFIC_PART: str = "//node1/incoming"
SEQ_NUMBER = 99
SOURCE_SPECIFIC_PART: str = "//uav1/sink"
REPORT_TO_SPECIFIC_PART: str = "//statistics/messages"


class TestFlags(TestCase):
    def setUp(self):
        self.f_all_true = Flags(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        self.f_all_false = Flags(0)

    def test_get_all_false_flags(self):
        self.assertFalse(any([self.f_all_false.get_flag(bit) for bit in range(128)]))

    def test_get_all_true_flags(self):
        self.assertTrue(all([self.f_all_true.get_flag(bit) for bit in range(128)]))

    def test_invalid_argument(self):
        self.assertRaises(TypeError, Flags, Flags(0))
        self.assertRaises(TypeError, Flags, "1")
        self.assertRaises(TypeError, Flags, 3.14159265)

    def test_set_all_flags(self):
        f = deepcopy(self.f_all_false)
        for bit in range(128):
            f.set_flag(bit)
        self.assertEqual(f.flags, self.f_all_true.flags)

    def test_unset_all_flags(self):
        f = deepcopy(self.f_all_true)
        for bit in range(128):
            f.unset_flag(bit)
        self.assertEqual(f.flags, self.f_all_false.flags)

    def test_eq_true_same_type(self):
        f = deepcopy(self.f_all_true)
        self.assertEqual(self.f_all_true, f)

    def test_eq_false_same_type(self):
        f = deepcopy(self.f_all_false)
        self.assertEqual(f, self.f_all_false)
        f.set_flag(5)
        self.assertNotEqual(f, self.f_all_false)
        self.assertNotEqual(f, self.f_all_true)

    def test_eq_wrong_type(self):
        self.assertEqual(self.f_all_false.__eq__(0), NotImplemented)


class TestBundleProcessingControlFlags(TestCase):
    def setUp(self):
        # 0x7FFFF sets bits 18..0 to true
        self.f_all_true = BundleProcessingControlFlags(flags=0x7FFFF)
        self.f_all_false = BundleProcessingControlFlags(flags=0)

    def test_false_control_flags(self):
        self.assertFalse(
            any(
                [
                    self.f_all_false.is_fragment,
                    self.f_all_false.payload_is_admin_record,
                    self.f_all_false.do_not_fragment,
                    self.f_all_false.acknowledgement_is_requested,
                    self.f_all_false.status_time_is_requested,
                    self.f_all_false.status_of_report_reception_is_requested,
                    self.f_all_false.status_of_report_forwarding_is_requested,
                    self.f_all_false.status_of_report_delivery_is_requested,
                    self.f_all_false.status_of_report_deletion_is_requested,
                ]
            )
        )

    def test_true_control_flags(self):
        self.assertTrue(
            all(
                [
                    self.f_all_true.is_fragment,
                    self.f_all_true.payload_is_admin_record,
                    self.f_all_true.do_not_fragment,
                    self.f_all_true.acknowledgement_is_requested,
                    self.f_all_true.status_time_is_requested,
                    self.f_all_true.status_of_report_reception_is_requested,
                    self.f_all_true.status_of_report_forwarding_is_requested,
                    self.f_all_true.status_of_report_delivery_is_requested,
                    self.f_all_true.status_of_report_deletion_is_requested,
                ]
            )
        )


class TestBlockProcessingControlFlags(TestCase):
    def setUp(self):
        # 0x1F sets bits 4..0 to true
        self.f_all_true = BlockProcessingControlFlags(flags=0x1F)
        self.f_all_false = BlockProcessingControlFlags(flags=0)

    def test_false_control_flags(self):
        self.assertFalse(
            any(
                [
                    self.f_all_false.block_must_be_replicated,
                    self.f_all_false.report_status_if_block_cant_be_processed,
                    self.f_all_false.delete_bundle_if_block_cant_be_processed,
                    self.f_all_false.discard_block_if_block_cant_be_processed,
                ]
            )
        )

    def test_true_control_flags(self):
        self.assertTrue(
            all(
                [
                    self.f_all_true.block_must_be_replicated,
                    self.f_all_true.report_status_if_block_cant_be_processed,
                    self.f_all_true.delete_bundle_if_block_cant_be_processed,
                    self.f_all_true.discard_block_if_block_cant_be_processed,
                ]
            )
        )


class TestPrimaryBlock(TestCase):
    def setUp(self):
        self.primary_block = PrimaryBlock(
            version=7,
            bundle_processing_control_flags=BundleProcessingControlFlags(flags=CONTROL_FLAGS),
            crc_type=CRC_TYPE_NOCRC,
            destination_scheme=URI_SCHEME_DTN_ENCODED,
            destination_specific_part=DESTINATION_SPECIFIC_PART,
            source_scheme=URI_SCHEME_DTN_ENCODED,
            source_specific_part=SOURCE_SPECIFIC_PART,
            report_to_scheme=URI_SCHEME_DTN_ENCODED,
            report_to_specific_part=REPORT_TO_SPECIFIC_PART,
            bundle_creation_time=BUNDLE_CREATION_TIME,
            sequence_number=SEQ_NUMBER,
            lifetime=BUNDLE_LIFETIME,
        )

    # Tests for static methods:

    def test_from_objects(self):
        pb_ut = PrimaryBlock.from_objects(
            full_destination_uri=f"dtn:{DESTINATION_SPECIFIC_PART}",
            full_source_uri=f"dtn:{SOURCE_SPECIFIC_PART}",
            full_report_to_uri=f"dtn:{REPORT_TO_SPECIFIC_PART}",
            bundle_processing_control_flags=BundleProcessingControlFlags(flags=CONTROL_FLAGS),
            bundle_creation_time=BUNDLE_CREATION_TIME,
            sequence_number=SEQ_NUMBER,
            lifetime=BUNDLE_LIFETIME,
        )
        self.assertEqual(self.primary_block, pb_ut)

    def test_primary_block_from_block_data(self):
        pb_ut = PrimaryBlock.from_block_data(
            (
                7,
                CONTROL_FLAGS,
                CRC_TYPE_NOCRC,
                (URI_SCHEME_DTN_ENCODED, DESTINATION_SPECIFIC_PART),
                (URI_SCHEME_DTN_ENCODED, SOURCE_SPECIFIC_PART),
                (URI_SCHEME_DTN_ENCODED, REPORT_TO_SPECIFIC_PART),
                (BUNDLE_CREATION_TIME, SEQ_NUMBER),
                BUNDLE_LIFETIME,
            )
        )
        self.assertEqual(pb_ut, self.primary_block)

    def test_version_is_7_check(self):
        pb_ut = (
            1337,
            CONTROL_FLAGS,
            CRC_TYPE_NOCRC,
            (URI_SCHEME_DTN_ENCODED, DESTINATION_SPECIFIC_PART),
            (URI_SCHEME_DTN_ENCODED, SOURCE_SPECIFIC_PART),
            (URI_SCHEME_DTN_ENCODED, REPORT_TO_SPECIFIC_PART),
            (BUNDLE_CREATION_TIME, SEQ_NUMBER),
            BUNDLE_LIFETIME,
        )
        self.assertRaises(NotImplementedError, PrimaryBlock.from_block_data, pb_ut)

    def test_invalid_length_of_block_data(self):
        # better safe than sorry:
        lengths = list(range(8)) + list(range(12, 65))
        for ell in lengths:
            self.assertRaises(ValueError, PrimaryBlock.from_block_data, [0 for _ in range(ell)])

    def test_crc_and_fragments_not_implemented_error(self):
        # CRC and fragments are not supported yet, so block data with certain lengths are refused with an error
        lengths = [9, 10, 11]
        for ell in lengths:
            self.assertRaises(
                NotImplementedError, PrimaryBlock.from_block_data, [0 for _ in range(ell)]
            )

    def test_invalid_bundle_data(self):
        pb = (
            7,
            CONTROL_FLAGS,
            CRC_TYPE_NOCRC,
            [URI_SCHEME_DTN_ENCODED],  # indexing into block data will fail here
            (URI_SCHEME_DTN_ENCODED, SOURCE_SPECIFIC_PART),
            (URI_SCHEME_DTN_ENCODED, REPORT_TO_SPECIFIC_PART),
            (BUNDLE_CREATION_TIME, SEQ_NUMBER),
            BUNDLE_LIFETIME,
        )
        self.assertRaises(ValueError, PrimaryBlock.from_block_data, pb)

    def test_check_invalid_uri_schemes(self):
        # must raise a ValueError since:
        # " ... function receives an argument that has the right type but an inappropriate value"
        # https://docs.python.org/3/library/exceptions.html#ValueError
        invalid_schemes = list(range(-1000, 1)) + list(range(3, 100000))
        for scheme in invalid_schemes:
            self.assertRaises(ValueError, PrimaryBlock.check_uri_scheme, scheme)

    def test_check_valid_uri_schemes(self):
        self.assertIsNone(PrimaryBlock.check_uri_scheme(1))
        self.assertIsNone(PrimaryBlock.check_uri_scheme(2))

    def test_from_full_uri_valid_uri(self):
        self.assertEqual(PrimaryBlock.from_full_uri("dtn://hahaha/~what"), (1, "//hahaha/~what"))
        self.assertEqual(PrimaryBlock.from_full_uri("dtn://none"), (1, 0))
        self.assertEqual(PrimaryBlock.from_full_uri("ipn://none"), (2, 0))
        self.assertEqual(PrimaryBlock.from_full_uri("ipn://1234.5678"), (2, (1234, 5678)))

    def test_from_full_uri_invalid_scheme_name(self):
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "://")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "://wait/~what")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "badscheme://hahah/~what")

    def test_from_full_uri_invalid_endpoint(self):
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "ipn://")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "ipn://1")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "ipn://1.2.3")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "ipn://-1.2")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "ipn://-1.-2")
        self.assertRaises(ValueError, PrimaryBlock.from_full_uri, "ipn://1.-2")

    def test_to_full_uri_valid_input(self):
        self.assertEqual(PrimaryBlock.to_full_uri(1, "//hahaha/~what"), "dtn://hahaha/~what")
        self.assertEqual(PrimaryBlock.to_full_uri(1, 0), "dtn://none")
        self.assertEqual(PrimaryBlock.to_full_uri(2, 0), "ipn://none")
        self.assertEqual(PrimaryBlock.to_full_uri(2, [1234, 5678]), "ipn://1234.5678")

    def test_to_full_uri_invalid_endpoint(self):
        self.assertRaises(ValueError, PrimaryBlock.to_full_uri, 2, [])
        self.assertRaises(ValueError, PrimaryBlock.to_full_uri, 2, [1])
        self.assertRaises(ValueError, PrimaryBlock.to_full_uri, 2, [1, 2, 3])
        self.assertRaises(ValueError, PrimaryBlock.to_full_uri, 2, [-1, 2])
        self.assertRaises(ValueError, PrimaryBlock.to_full_uri, 2, [-1, -2])
        self.assertRaises(ValueError, PrimaryBlock.to_full_uri, 2, [1, -2])
        self.assertRaises(TypeError, PrimaryBlock.to_full_uri, 2, ["1", "2"])
        self.assertRaises(TypeError, PrimaryBlock.to_full_uri, 2, ["one", "two"])

    def test_to_full_uri_invalid_scheme_code(self):
        invalid_schemes = list(range(-1000, 1)) + list(range(3, 100000))
        for scheme in invalid_schemes:
            self.assertRaises(ValueError, PrimaryBlock.to_full_uri, scheme, 0)

    # Tests for instance methods ##################################################################

    def test_eq_operator(self):
        pb = deepcopy(self.primary_block)
        self.assertEqual(pb, self.primary_block)

    def test_primary_block_to_block_data(self):
        pb_ut = (
            7,
            CONTROL_FLAGS,
            CRC_TYPE_NOCRC,
            (URI_SCHEME_DTN_ENCODED, DESTINATION_SPECIFIC_PART),
            (URI_SCHEME_DTN_ENCODED, SOURCE_SPECIFIC_PART),
            (URI_SCHEME_DTN_ENCODED, REPORT_TO_SPECIFIC_PART),
            (BUNDLE_CREATION_TIME, SEQ_NUMBER),
            BUNDLE_LIFETIME,
        )
        self.assertEqual(pb_ut, self.primary_block.to_block_data())

    def test_bundle_creation_time_datetime(self):
        # check if we're calling the correct function. Correctness of that function is tested in its own unit test
        self.assertEqual(
            self.primary_block.bundle_creation_time_datetime,
            from_dtn_timestamp(BUNDLE_CREATION_TIME),
        )

    @mock.patch.object(PrimaryBlock, "to_full_uri")
    def test_full_source_uri(self, mock_to_full_uri):
        self.primary_block.full_source_uri
        self.assertTrue(mock_to_full_uri.called)
        self.assertEqual(mock_to_full_uri.call_args[0][0], self.primary_block.source_scheme)
        self.assertEqual(mock_to_full_uri.call_args[0][1], self.primary_block.source_specific_part)

    @mock.patch.object(PrimaryBlock, "to_full_uri")
    def test_full_destination_uri(self, mock_to_full_uri):
        self.primary_block.full_destination_uri
        self.assertTrue(mock_to_full_uri.called)
        self.assertEqual(mock_to_full_uri.call_args[0][0], self.primary_block.destination_scheme)
        self.assertEqual(
            mock_to_full_uri.call_args[0][1], self.primary_block.destination_specific_part
        )

    @mock.patch.object(PrimaryBlock, "to_full_uri")
    def test_full_report_to_uri(self, mock_to_full_uri):
        self.primary_block.full_report_to_uri
        self.assertTrue(mock_to_full_uri.called)
        self.assertEqual(mock_to_full_uri.call_args[0][0], self.primary_block.report_to_scheme)
        self.assertEqual(
            mock_to_full_uri.call_args[0][1], self.primary_block.report_to_specific_part
        )

    @mock.patch.object(PrimaryBlock, "from_full_uri", return_value=(1, 2))
    def test_full_source_uri_setter(self, mock_from_full_uri):
        self.primary_block.full_source_uri = 42
        self.assertTrue(mock_from_full_uri.called)
        self.assertEqual(mock_from_full_uri.call_args[0][0], 42)
        mock_from_full_uri.stop()

    @mock.patch.object(PrimaryBlock, "from_full_uri", return_value=(3, 4))
    def test_full_destination_uri_setter(self, mock_from_full_uri):
        self.primary_block.full_destination_uri = 42
        self.assertTrue(mock_from_full_uri.called)
        self.assertEqual(mock_from_full_uri.call_args[0][0], 42)
        mock_from_full_uri.stop()

    @mock.patch.object(PrimaryBlock, "from_full_uri", return_value=(5, 6))
    def test_full_report_to_uri_setter(self, mock_from_full_uri):
        self.primary_block.full_report_to_uri = 42
        self.assertTrue(mock_from_full_uri.called)
        self.assertEqual(mock_from_full_uri.call_args[0][0], 42)


class TestCanonicalBlock(TestCase):
    def setUp(self):
        self.block_data_plb = (1, 1, 42, 0, b"123456790")
        self.block_data_pnb = (6, 2, 42, 0, b"123456790")
        self.block_data_bab = (7, 3, 42, 0, b"123456790")
        self.block_data_hcb = (10, 4, 42, 0, b"123456790")
        self.canonical_block_plb = PayloadBlock(1, 1, Flags(42), 0, b"123456790")
        self.canonical_block_pnb = PreviousNodeBlock(6, 2, Flags(42), 0, b"123456790")
        self.canonical_block_bab = BundleAgeBlock(7, 3, Flags(42), 0, b"123456790")
        self.canonical_block_hcb = HopCountBlock(10, 4, Flags(42), 0, b"123456790")

    def test_from_block_data_returns_correct_types(self):
        self.assertTrue(
            isinstance(CanonicalBlock.from_block_data(self.block_data_plb), PayloadBlock)
        )
        self.assertTrue(
            isinstance(CanonicalBlock.from_block_data(self.block_data_pnb), PreviousNodeBlock)
        )
        self.assertTrue(
            isinstance(CanonicalBlock.from_block_data(self.block_data_bab), BundleAgeBlock)
        )
        self.assertTrue(
            isinstance(CanonicalBlock.from_block_data(self.block_data_hcb), HopCountBlock)
        )

    def test_from_block_data_returns_correct_blocks(self):
        self.assertEqual(
            CanonicalBlock.from_block_data(self.block_data_plb), self.canonical_block_plb
        )
        self.assertEqual(
            CanonicalBlock.from_block_data(self.block_data_pnb), self.canonical_block_pnb
        )
        self.assertEqual(
            CanonicalBlock.from_block_data(self.block_data_bab), self.canonical_block_bab
        )
        self.assertEqual(
            CanonicalBlock.from_block_data(self.block_data_hcb), self.canonical_block_hcb
        )

    @mock.patch("builtins.print")
    def test_from_block_data_warnings_on_other_block_types(self, mock_print):
        for block_type in range(11, 256):
            block_data = [block_type, 23, 42, 0, b"0987654321"]
            self.assertTrue(type(CanonicalBlock.from_block_data(block_data)) is CanonicalBlock)
            self.assertTrue(mock_print.called)

    def test_from_block_data_errors_on_unimplemented_block_types(self):
        for block_type in range(256, 10000):
            block_data = [block_type, 23, 42, 0, b"0987654321"]
            self.assertRaises(NotImplementedError, CanonicalBlock.from_block_data, block_data)
        for block_type in range(-10000, 1):
            block_data = [block_type, 23, 42, 0, b"0987654321"]
            self.assertRaises(NotImplementedError, CanonicalBlock.from_block_data, block_data)

    def test_from_block_data_unsupported_lengths(self):
        for ell in range(5):
            self.assertRaises(
                ValueError,
                CanonicalBlock.from_block_data,
                [0 for _ in range(ell)],
            )
        for ell in range(7, 1000):
            self.assertRaises(
                ValueError,
                CanonicalBlock.from_block_data,
                [0 for _ in range(ell)],
            )
        self.assertRaises(NotImplementedError, CanonicalBlock.from_block_data, [0] * 6)

    def test_to_block_data_returns_correct_block_data(self):
        self.assertEqual(
            CanonicalBlock.to_block_data(self.canonical_block_plb), self.block_data_plb
        )
        self.assertEqual(
            CanonicalBlock.to_block_data(self.canonical_block_pnb), self.block_data_pnb
        )
        self.assertEqual(
            CanonicalBlock.to_block_data(self.canonical_block_bab), self.block_data_bab
        )
        self.assertEqual(
            CanonicalBlock.to_block_data(self.canonical_block_hcb), self.block_data_hcb
        )


class TestPayloadBlock(TestCase):
    def setUp(self):
        self.payload_block = PayloadBlock(1, 1, Flags(42), 0, b"123456790")

    def test_from_objects_return_correct_bloc(self):
        self.assertEquals(PayloadBlock.from_objects(b"123456790", Flags(42)), self.payload_block)


class TestPreviousNodeBlock(TestCase):
    def setUp(self):
        self.uri_1 = "dtn://node1/incoming"
        self.uri_2 = "ipn://1234.5678"
        self.prev_node_1 = PreviousNodeBlock(
            6, 1, Flags(42), 0, dumps(PrimaryBlock.from_full_uri(self.uri_1))
        )
        self.prev_node_2 = PreviousNodeBlock(
            6, 1, Flags(42), 0, dumps(PrimaryBlock.from_full_uri(self.uri_2))
        )

    def test_previous_node_id_returns_correct_uri(self):
        self.assertEqual(self.prev_node_1.previous_node_id, [1, "//node1/incoming"])
        self.assertEqual(self.prev_node_2.previous_node_id, [2, [1234, 5678]])

    def test_from_objects_returns_correct_block(self):
        self.assertEqual(PreviousNodeBlock.from_objects(self.uri_1, Flags(42)), self.prev_node_1)
        self.assertEqual(PreviousNodeBlock.from_objects(self.uri_2, Flags(42)), self.prev_node_2)


class TestBundleAgeBlock(TestCase):
    def setUp(self):
        self.age = 1234567
        self.bundle_age_block = BundleAgeBlock(7, 1, Flags(42), 0, dumps(self.age))

    def test_age_milliseconds_getter(self):
        self.assertEqual(self.age, self.bundle_age_block.age_milliseconds)

    def test_age_milliseconds_setter(self):
        bab = BundleAgeBlock(7, 1, Flags(42), 0, dumps(0))
        self.assertEqual(loads(bab.data), 0)
        bab.age_milliseconds = self.age
        self.assertEqual(self.age, self.bundle_age_block.age_milliseconds)


class TestHopCountBlock(TestCase):
    def setUp(self):
        self.hop_count = (98, 76)
        self.hop_count_block = HopCountBlock(10, 1, Flags(42), 0, dumps(self.hop_count))

    def test_from_objects_returns_correct_block(self):
        self.assertEqual(self.hop_count_block, HopCountBlock.from_objects(98, 76, Flags(42)))

    def test_hop_count_setter(self):
        hcb = HopCountBlock(10, 1, Flags(42), 0, dumps((98, 0)))
        self.assertEqual(loads(hcb.data), [98, 0])
        hcb.hop_count = 76
        self.assertEqual(hcb, self.hop_count_block)

    def test_hop_count_getter(self):
        self.assertEqual(self.hop_count_block.hop_count, self.hop_count[1])

    def test_hop_limit_getter(self):
        self.assertEqual(self.hop_count_block.hop_limit, self.hop_count[0])


class TestBundle(TestCase):
    def setUp(self):
        self.canonical_block_plb = PayloadBlock(1, 0, Flags(42), 0, b"123456790")
        self.canonical_block_pnb = PreviousNodeBlock(
            6, 0, Flags(42), 0, dumps(PrimaryBlock.from_full_uri("dtn://node1/incoming"))
        )
        self.canonical_block_bab = BundleAgeBlock(7, 0, Flags(42), 0, dumps(1234567))
        self.canonical_block_hcb = HopCountBlock(10, 0, Flags(42), 0, dumps((98, 76)))
        self.primary_block = PrimaryBlock(
            version=7,
            bundle_processing_control_flags=BundleProcessingControlFlags(flags=CONTROL_FLAGS),
            crc_type=CRC_TYPE_NOCRC,
            destination_scheme=URI_SCHEME_DTN_ENCODED,
            destination_specific_part=DESTINATION_SPECIFIC_PART,
            source_scheme=URI_SCHEME_DTN_ENCODED,
            source_specific_part=SOURCE_SPECIFIC_PART,
            report_to_scheme=URI_SCHEME_DTN_ENCODED,
            report_to_specific_part=REPORT_TO_SPECIFIC_PART,
            bundle_creation_time=0,
            sequence_number=SEQ_NUMBER,
            lifetime=BUNDLE_LIFETIME,
        )
        self.full_bundle = Bundle(
            self.primary_block,
            self.canonical_block_pnb,
            self.canonical_block_bab,
            self.canonical_block_hcb,
            self.canonical_block_plb,
            [  # other_blocks
                CanonicalBlock(192, 0, Flags(37), 0, b"123123123"),
                CanonicalBlock(193, 0, Flags(38), 0, b"123123123"),
                CanonicalBlock(194, 0, Flags(39), 0, b"123123123"),
                CanonicalBlock(195, 0, Flags(40), 0, b"123123123"),
            ],
        )

    def test_correct_block_numbering_full_bundle(self):
        # https://datatracker.ietf.org/doc/html/rfc9171#section-4.1-5
        # The block number uniquely identifies the block within the bundle, enabling blocks
        # (notably Bundle Protocol Security blocks) to reference other blocks in the same bundle
        # without ambiguity. The block number of the primary block is implicitly zero; [...]
        # Block numbering is unrelated to the order in which blocks are sequenced in the bundle.
        # The block number of the payload block is always 1.
        block_nums = [
            self.full_bundle.previous_node_block.block_number,
            self.full_bundle.bundle_age_block.block_number,
            self.full_bundle.hop_count_block.block_number,
            self.full_bundle.payload_block.block_number,
            self.full_bundle.other_blocks[0].block_number,
            self.full_bundle.other_blocks[1].block_number,
            self.full_bundle.other_blocks[2].block_number,
            self.full_bundle.other_blocks[3].block_number,
        ]
        self.assertNotIn(0, block_nums)  # primary block
        self.assertEqual(self.full_bundle.payload_block.block_number, 1)  # payload always #1
        self.assertEqual(len(block_nums), len(set(block_nums)))  # all unique

    def test_bundle_age_block_must_be_present_when_creation_time_is_zero(self):
        self.assertRaises(
            ValueError,
            Bundle,
            self.primary_block,
        )

    def test_unable_to_insert_second_instance_of_block(self):
        self.assertRaises(
            ValueError, self.full_bundle.insert_canonical_block, deepcopy(self.canonical_block_bab)
        )
        self.assertRaises(
            ValueError, self.full_bundle.insert_canonical_block, deepcopy(self.canonical_block_plb)
        )
        self.assertRaises(
            ValueError, self.full_bundle.insert_canonical_block, deepcopy(self.canonical_block_pnb)
        )
        self.assertRaises(
            ValueError, self.full_bundle.insert_canonical_block, deepcopy(self.canonical_block_hcb)
        )

    def test_correct_bundle_id(self):
        self.assertEqual(
            self.full_bundle.bundle_id,
            f"{URI_SCHEME_DTN_NAME}:{SOURCE_SPECIFIC_PART}-0-{SEQ_NUMBER}",
        )

    def test_remove_present_block(self):
        self.full_bundle.remove_block(deepcopy(self.canonical_block_bab))
        self.assertIsNone(self.full_bundle.bundle_age_block)
        self.full_bundle.remove_block(deepcopy(self.canonical_block_pnb))
        self.assertIsNone(self.full_bundle.previous_node_block)
        self.full_bundle.remove_block(deepcopy(self.canonical_block_plb))
        self.assertIsNone(self.full_bundle.payload_block)
        self.full_bundle.remove_block(deepcopy(self.canonical_block_hcb))
        self.assertIsNone(self.full_bundle.hop_count_block)

        target_length = len(self.full_bundle.other_blocks) - 1
        self.full_bundle.remove_block(CanonicalBlock(192, 5, Flags(37), 0, b"123123123"))
        self.assertEqual(len(self.full_bundle.other_blocks), target_length)

    def test_remove_missing_bundle(self):
        pb = deepcopy(self.primary_block)
        pb.bundle_creation_time = 1234567
        bundle = Bundle(pb)
        bundle.remove_block(deepcopy(self.canonical_block_bab))
        self.assertIsNone(bundle.bundle_age_block)
        bundle.remove_block(deepcopy(self.canonical_block_pnb))
        self.assertIsNone(bundle.previous_node_block)
        bundle.remove_block(deepcopy(self.canonical_block_plb))
        self.assertIsNone(bundle.payload_block)
        bundle.remove_block(deepcopy(self.canonical_block_hcb))
        self.assertIsNone(bundle.hop_count_block)

        bundle.remove_block(CanonicalBlock(192, 5, Flags(37), 0, b"123123123"))
        self.assertEqual(len(bundle.other_blocks), 0)

    @mock.patch("py_dtn7.bundle.CanonicalBlock.from_block_data")
    @mock.patch("py_dtn7.bundle.PrimaryBlock.from_block_data")
    def test_from_block_data(self, mock_pb_from_block_data, mock_cb_from_block_data):
        mock_pb_from_block_data.return_value = self.primary_block
        mock_cb_from_block_data.return_value = self.canonical_block_bab

        bundle_crit = Bundle(
            primary_block=self.primary_block, bundle_age_block=self.canonical_block_bab
        )
        self.assertEqual(bundle_crit, Bundle.from_block_data([0, 0]))
