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
            self.assertRaises(IndexError, PrimaryBlock.from_block_data, [0 for _ in range(ell)])

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
        mock_from_full_uri.return_value = (1, 2)
        self.primary_block.full_source_uri = 1337
        self.assertTrue(mock_from_full_uri.called)
        self.assertEqual(mock_from_full_uri.call_args[0][0], 1337)
        mock_from_full_uri.stop()

    @mock.patch.object(PrimaryBlock, "from_full_uri", return_value=(3, 4))
    def test_full_destination_uri_setter(self, mock_from_full_uri):
        mock_from_full_uri.return_value = (3, 4)
        self.primary_block.full_destination_uri = 1337
        self.assertTrue(mock_from_full_uri.called)
        self.assertEqual(mock_from_full_uri.call_args[0][0], 1337)
        mock_from_full_uri.stop()

    @mock.patch.object(PrimaryBlock, "from_full_uri", return_value=(5, 6))
    def test_full_report_to_uri_setter(self, mock_from_full_uri):
        self.primary_block.full_report_to_uri = 1337
        self.assertTrue(mock_from_full_uri.called)
        self.assertEqual(mock_from_full_uri.call_args[0][0], 1337)
