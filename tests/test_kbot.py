import unittest
import kbot

class TestSlackbot(unittest.TestCase):
    def test_handle_command(self):
        "Tests the handle command functions inputs"
        self.assertEqual(
            kbot.handle_command('choc', "DCR9ET3FD"),
            None)
    


if __name__ == '__main__':
    unittest.main()