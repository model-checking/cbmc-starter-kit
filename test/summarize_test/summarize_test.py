# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import unittest
import unittest.mock

import pathlib
import sys

sys.path.append("../../src/cbmc_starter_kit/template-for-repository/proofs/lib")
import summarize


class TestSummarizeResults(unittest.TestCase):
    def setUp(self):
        self.run_file = pathlib.Path().cwd() / "sample_run.json"


    @unittest.mock.patch('builtins.print')
    def test_print_proof_results(self, mock):
        summarize.print_proof_results(self.run_file)
        expected_calls = [
            unittest.mock.call(
                "| Status  | Count |\n"
                "|---------|-------|\n"
                "| Fail    | 1     |\n"
                "| Success | 1     |\n"
                "\n"),
            unittest.mock.call(
                "| Proof             | Status  |\n"
                "|-------------------|---------|\n"
                "| pipe-will-fail    | Fail    |\n"
                "| pipe-will-succeed | Success |\n"
                "\n")
        ]
        self.assertEqual(expected_calls, mock.call_args_list)


if __name__ == '__main__':
    unittest.main()
