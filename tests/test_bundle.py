from copy import deepcopy
from unittest import TestCase

from py_dtn7.bundle import *


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
        bundle_creation_time=(3600 * 24 * 31 + 3600 * 9) * 1000,  # 2000-01-31 09:00:00 +0000 (UTC)
        sequence_number=0,
        lifetime=3600 * 24 * 1000,  # one day
    )

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
        self.primary_block.bundle_processing_control_flags.flags = old_flags

    def test_eq_operator(self):
        pb = deepcopy(self.primary_block)
        self.assertEqual(pb, self.primary_block)

    def test_primary_block_from_block_data(self):
        pb_ut = PrimaryBlock.from_block_data(
            (
                7,
                0,
                CRC_TYPE_NOCRC,
                (URI_SCHEME_DTN_ENCODED, ""),
                (URI_SCHEME_DTN_ENCODED, ""),
                (URI_SCHEME_DTN_ENCODED, ""),
                ((3600 * 24 * 31 + 3600 * 9) * 1000, 0),
                3600 * 24 * 1000,
            )
        )
        self.assertEqual(pb_ut, self.primary_block)

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

    def test_version_is_7_check(self):
        pb_ut = (
            1337,
            0,
            CRC_TYPE_NOCRC,
            (URI_SCHEME_DTN_ENCODED, ""),
            (URI_SCHEME_DTN_ENCODED, ""),
            (URI_SCHEME_DTN_ENCODED, ""),
            ((3600 * 24 * 31 + 3600 * 9) * 1000, 0),
            3600 * 24 * 1000,
        )
        self.assertRaises(NotImplementedError, PrimaryBlock.from_block_data, pb_ut)

    def test_invalid_length_of_block_data(self):
        # better safe than sorry:
        lengths = [0, 1, 2, 3, 4, 5, 6, 7, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        for ell in lengths:
            self.assertRaises(IndexError, PrimaryBlock.from_block_data, [0 for _ in range(ell)])
