import os
import unittest
from a import ActionRegistry


CDIR = os.path.dirname(__file__)


class TestActionRegistry(unittest.TestCase):
    def test_creating_action_registry(self):
        reg: ActionRegistry = ActionRegistry("test_registry")

        self.assertEqual(reg.name, "test_registry")
