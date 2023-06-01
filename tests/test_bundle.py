from copy import deepcopy
from unittest import TestCase

from py_dtn7.bundle import *

BUNDLE_CREATION_TIME: int = (3600 * 24 * 31 + 3600 * 9) * 1000  # 2000-01-31 09:00:00 +0000 (UTC)
BUNDLE_LIFETIME: int = 3600 * 24 * 1000  # one day


class TestFlags(TestCase):

    all_true = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

    def test_get_all_false_flags(self):
        f = Flags(0)
        self.assertFalse(any([f.get_flag(bit) for bit in range(128)]))

    def test_get_all_true_flags(self):
        f = Flags(self.all_true)
        self.assertTrue(all([f.get_flag(bit) for bit in range(128)]))

    def test_set_all_flags(self):
        f = Flags(0)
        for bit in range(128):
            f.set_flag(bit)
        self.assertEqual(f.flags, self.all_true)

    def test_unset_all_flags(self):
        f = Flags(self.all_true)
        for bit in range(128):
            f.unset_flag(bit)
        self.assertEqual(f.flags, 0)


class TestPrimaryBlock(TestCase):

    primary_block: PrimaryBlock = PrimaryBlock(
        version=7,
        bundle_processing_control_flags=BundleProcessingControlFlags(flags=0),
        crc_type=CRC_TYPE_NOCRC,
        destination_scheme=URI_SCHEME_DTN_ENCODED,
        destination_specific_part="",
        source_scheme=URI_SCHEME_DTN_ENCODED,
        source_specific_part="",
        report_to_scheme=URI_SCHEME_DTN_ENCODED,
        report_to_specific_part="",
        bundle_creation_time=BUNDLE_CREATION_TIME,
        sequence_number=0,
        lifetime=BUNDLE_LIFETIME,
    )

    # Tests for static methods:

    def test_primary_block_from_block_data(self):
        pb_ut = PrimaryBlock.from_block_data(
            (
                7,
                0,
                CRC_TYPE_NOCRC,
                (URI_SCHEME_DTN_ENCODED, ""),
                (URI_SCHEME_DTN_ENCODED, ""),
                (URI_SCHEME_DTN_ENCODED, ""),
                (BUNDLE_CREATION_TIME, 0),
                BUNDLE_LIFETIME,
            )
        )
        self.assertEqual(pb_ut, self.primary_block)

    def test_version_is_7_check(self):
        pb_ut = (
            1337,
            0,
            CRC_TYPE_NOCRC,
            (URI_SCHEME_DTN_ENCODED, ""),
            (URI_SCHEME_DTN_ENCODED, ""),
            (URI_SCHEME_DTN_ENCODED, ""),
            (BUNDLE_CREATION_TIME, 0),
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

    # TODO: invalid IPN specifiv parts: negative number, too many numbers

    # Tests for instance methods ##################################################################

    def test_false_control_flags(self):
        self.assertFalse(
            any(
                [
                    self.primary_block.bundle_processing_control_flags.is_fragment,
                    self.primary_block.bundle_processing_control_flags.payload_is_admin_record,
                    self.primary_block.bundle_processing_control_flags.do_not_fragment,
                    self.primary_block.bundle_processing_control_flags.acknowledgement_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_time_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_reception_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_forwarding_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_delivery_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_deletion_is_requested,
                ]
            )
        )

    def test_true_control_flags(self):
        old_flags = self.primary_block.bundle_processing_control_flags.flags
        # 0x7FFFF sets bits 0..18 to true
        self.primary_block.bundle_processing_control_flags.flags = int(0x7FFFF)
        self.assertTrue(
            all(
                [
                    self.primary_block.bundle_processing_control_flags.is_fragment,
                    self.primary_block.bundle_processing_control_flags.payload_is_admin_record,
                    self.primary_block.bundle_processing_control_flags.do_not_fragment,
                    self.primary_block.bundle_processing_control_flags.acknowledgement_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_time_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_reception_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_forwarding_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_delivery_is_requested,
                    self.primary_block.bundle_processing_control_flags.status_of_report_deletion_is_requested,
                ]
            )
        )
        # self.primary_block.bundle_processing_control_flags.flags = old_flags

    def test_eq_operator(self):
        pb = deepcopy(self.primary_block)
        self.assertEqual(pb, self.primary_block)

    def test_primary_block_to_block_data(self):
        pb_ut = (
            7,
            0,
            CRC_TYPE_NOCRC,
            (URI_SCHEME_DTN_ENCODED, ""),
            (URI_SCHEME_DTN_ENCODED, ""),
            (URI_SCHEME_DTN_ENCODED, ""),
            ((3600 * 24 * 31 + 3600 * 9) * 1000, 0),
            3600 * 24 * 1000,
        )
        self.assertEqual(pb_ut, self.primary_block.to_block_data())

    def test_bundle_creation_time_datetime(self):
        # check if we're calling the correct function. Correctness of that function is tested in its own unit test
        self.assertEqual(
            self.primary_block.bundle_creation_time_datetime,
            from_dtn_timestamp(BUNDLE_CREATION_TIME),
        )
