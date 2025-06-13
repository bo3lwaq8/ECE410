import os
import unittest
from io import StringIO
from unittest.mock import patch

# Import functions from your main file. Adjust the module name if needed.
from cryptography import transform_text, main

class TestCryptoAlgorithm(unittest.TestCase):
    def test_transform_text(self):
        # Expected behavior: preserving case.
        self.assertEqual(transform_text("Hello"), "Vmhhq")
        self.assertEqual(transform_text("World"), "Oqzhj")
        # For a punctuation test: '!' becomes '?' as per our mapping.
        self.assertEqual(transform_text("Hello World!"), "Vmhhq Oqzhj?")

    @patch('builtins.input', side_effect=["Test Input", "n"])  # 'n' for no disassembly output
    def test_main_creates_crypted_file(self, mock_input):
        # Ensure the file doesn't already exist.
        if os.path.exists("crypted.txt"):
            os.remove("crypted.txt")
        # Run the main function.
        main()
        # Check that crypted.txt was created.
        self.assertTrue(os.path.exists("crypted.txt"))
        with open("crypted.txt", "r") as f:
            content = f.read()
        # Check that file contains both the original and encrypted text.
        self.assertIn("Original: Test Input", content)
        self.assertIn("Encrypted: " + transform_text("Test Input"), content)
        # Clean up.
        os.remove("crypted.txt")

    @patch('builtins.input', side_effect=["Test", "y"])  # 'y' to produce disassembled.txt
    def test_main_creates_disassembled_file(self, mock_input):
        # Clean up any existing files.
        for filename in ("crypted.txt", "disassembled.txt"):
            if os.path.exists(filename):
                os.remove(filename)
        # Run the main function.
        main()
        # Verify that disassembled.txt was created.
        self.assertTrue(os.path.exists("disassembled.txt"))
        with open("disassembled.txt", "r") as f:
            disassembled_content = f.read()
        # Check for a common opcode in the disassembly.
        self.assertIn("LOAD_CONST", disassembled_content)
        # Clean up.
        for filename in ("crypted.txt", "disassembled.txt"):
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == '__main__':
    unittest.main()
