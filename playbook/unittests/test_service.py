import os
import unittest
from Service import Service

CDIR = os.path.dirname(__file__)


class TestService(unittest.TestCase):
    def test_service_init(self):
        name: str = "jellyfin"

        newService: Service = Service(name)

        self.assertEqual(newService.name, name)
