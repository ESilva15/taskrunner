import os
import unittest
from unittest.mock import patch
from playbook import ActionRegistrar, ActionRegistrarYAMLReader
from playbook.action_registry import ActionRegistry


CDIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(CDIR, "test_data")


class TestActionRegistrar(unittest.TestCase):
    @patch.object(ActionRegistrarYAMLReader, '_load_registries_from_file')
    def test_reading_action_registry(self, mock_load):
        mock_reg1 = ActionRegistry("docker_reg")
        mock_reg2 = ActionRegistry("restic_reg")
        mock_load.side_effect = [[mock_reg1], [mock_reg2]]

        yaml_data = {
            "registries": ["docker.py", "restic.py"]
        }

        expected_size = 2
        expected_manifest = {
            "registrar_manifest": [
                {"registry_name": "docker_reg", "functions": {}},
                {"registry_name": "restic_reg", "functions": {}}
            ]
        } 

        reg: ActionRegistrar = ActionRegistrarYAMLReader.read(yaml_data)

        self.assertEqual(expected_manifest, reg.manifest())
        self.assertEqual(expected_size, reg.size())

        pass

    # def test_creating_action_registry(self):
    #     yaml_data = {
    #         "registries": ["docker.py", "restic.py"]
    #     }
    #
    #     expected_size = 2
    #     expected_manifest = {
    #         "registrar_manifest": []
    #     }
    #
    #     reg: ActionRegistrar = ActionRegistrarYAMLReader.read(
    #         yaml_data, base_dir=os.path.join(TEST_DATA, "registries")
    #     )
    #
    #     self.assertEqual(expected_manifest, reg.manifest())
    #     self.assertEqual(expected_size, reg.size())
