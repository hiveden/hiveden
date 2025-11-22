import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import subprocess
import configparser
from hiveden.shares.smb import SMBManager, SMB_CONF_PATH

class TestSMBManager(unittest.TestCase):

    @patch('hiveden.shares.smb.shutil.which')
    def test_check_installed(self, mock_which):
        manager = SMBManager()
        
        mock_which.return_value = '/usr/bin/smbd'
        self.assertTrue(manager.check_installed())
        
        mock_which.return_value = None
        self.assertFalse(manager.check_installed())

    @patch('hiveden.shares.smb.get_package_manager')
    @patch('hiveden.shares.smb.shutil.which')
    def test_install(self, mock_which, mock_get_pm):
        manager = SMBManager()
        
        # Case 1: Already installed
        mock_which.return_value = '/usr/bin/smbd'
        manager.install()
        mock_get_pm.assert_not_called()
        
        # Case 2: Not installed
        mock_which.return_value = None
        mock_pm = MagicMock()
        mock_get_pm.return_value = mock_pm
        manager.install()
        mock_pm.install.assert_called_with("samba")

    @patch('os.path.exists')
    def test_list_shares_no_file(self, mock_exists):
        mock_exists.return_value = False
        manager = SMBManager()
        self.assertEqual(manager.list_shares(), [])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[global]\nworkgroup=WORKGROUP\n[share1]\npath=/tmp\ncomment=Test Share\n")
    def test_list_shares(self, mock_file, mock_exists):
        mock_exists.return_value = True
        manager = SMBManager()
        shares = manager.list_shares()
        self.assertEqual(len(shares), 1)
        self.assertEqual(shares[0]['name'], 'share1')
        self.assertEqual(shares[0]['path'], '/tmp')
        self.assertEqual(shares[0]['comment'], 'Test Share')

    @patch('hiveden.shares.smb.subprocess.run')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[global]\nworkgroup=WORKGROUP\n")
    def test_create_share(self, mock_file, mock_exists, mock_subprocess):
        mock_exists.return_value = True
        manager = SMBManager()
        
        manager.create_share("newshare", "/data", "New Share")
        
        # Verify write was called
        handle = mock_file()
        self.assertTrue(handle.write.called)
        
        # Verify reload
        mock_subprocess.assert_called()

    @patch('hiveden.shares.smb.subprocess.run')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="[global]\nworkgroup=WORKGROUP\n[todelete]\npath=/tmp\n")
    def test_delete_share(self, mock_file, mock_exists, mock_subprocess):
        mock_exists.return_value = True
        manager = SMBManager()
        
        manager.delete_share("todelete")
        
        handle = mock_file()
        self.assertTrue(handle.write.called)
        mock_subprocess.assert_called()

    @patch('hiveden.shares.smb.subprocess.run')
    def test_manage_service(self, mock_subprocess):
        manager = SMBManager()
        
        manager.start_service()
        mock_subprocess.assert_called_with(["systemctl", "start", "smbd"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        manager.stop_service()
        mock_subprocess.assert_called_with(["systemctl", "stop", "smbd"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        manager.restart_service()
        mock_subprocess.assert_called_with(["systemctl", "restart", "smbd"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @patch('hiveden.shares.smb.subprocess.run')
    def test_get_status(self, mock_subprocess):
        manager = SMBManager()
        
        # Mock active status
        mock_subprocess.return_value.stdout = "active"
        mock_subprocess.return_value.returncode = 0
        status = manager.get_status()
        self.assertEqual(status, "active")
        
        # Mock inactive status
        mock_subprocess.return_value.stdout = "inactive"
        mock_subprocess.return_value.returncode = 3
        status = manager.get_status()
        self.assertEqual(status, "inactive")
