import unittest
from unittest.mock import patch, MagicMock
from hiveden.systemd.manager import SystemdManager
from hiveden.systemd.models import SystemdServiceStatus

class TestSystemdManager(unittest.TestCase):
    def setUp(self):
        self.manager = SystemdManager()

    @patch('subprocess.run')
    def test_list_services(self, mock_run):
        # We need to handle multiple calls:
        # 1. _resolve_service_name -> systemctl show -p LoadState ...
        # 2. get_service_status -> systemctl show ...
        
        def side_effect(args, **kwargs):
            cmd_str = " ".join(args)
            result = MagicMock()
            result.returncode = 0
            
            if "show -p LoadState" in cmd_str:
                result.stdout = "LoadState=loaded"
            elif "show --no-pager" in cmd_str:
                result.stdout = """
LoadState=loaded
ActiveState=active
SubState=running
UnitFileState=enabled
Description=Samba SMB Daemon
MainPID=1234
ActiveEnterTimestamp=Mon 2023-01-01 10:00:00 UTC
"""
            elif "is-enabled" in cmd_str:
                result.stdout = "enabled"
            else:
                result.stdout = ""
            return result

        mock_run.side_effect = side_effect

        services = self.manager.list_services()
        
        self.assertTrue(len(services) >= 1)
        samba = next((s for s in services if s.name == 'samba'), None)
        self.assertIsNotNone(samba)
        self.assertEqual(samba.active_state, 'active')

    @patch('subprocess.run')
    def test_manage_service(self, mock_run):
        # Mocking for _resolve_service_name, the action command, and get_service_status
        def side_effect(args, **kwargs):
            cmd_str = " ".join(args)
            result = MagicMock()
            result.returncode = 0
            
            if "show -p LoadState" in cmd_str:
                result.stdout = "LoadState=loaded"
            elif "systemctl restart" in cmd_str:
                return result # Success
            elif "show --no-pager" in cmd_str:
                result.stdout = "LoadState=loaded\nActiveState=active\nSubState=running"
            elif "is-enabled" in cmd_str:
                result.stdout = "enabled"
            return result

        mock_run.side_effect = side_effect
        
        # We also need to patch get_service_status to return a proper object because manage_service returns it
        # Actually, if we mock subprocess correctly, get_service_status logic will run and return object.
        # Let's rely on that since we improved the side_effect.
        
        result = self.manager.manage_service('samba', 'restart')
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, SystemdServiceStatus)
        self.assertEqual(result.active_state, 'active')

if __name__ == '__main__':
    unittest.main()