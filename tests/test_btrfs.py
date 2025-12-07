import unittest
from unittest.mock import patch, MagicMock
from hiveden.shares.btrfs import BtrfsManager
import os

class TestBtrfsManager(unittest.TestCase):
    @patch('psutil.disk_partitions')
    def test_list_volumes(self, mock_partitions):
        mock_part = MagicMock()
        mock_part.fstype = 'btrfs'
        mock_part.device = '/dev/sda1'
        mock_part.mountpoint = '/mnt/data'
        mock_partitions.return_value = [mock_part]

        manager = BtrfsManager()
        volumes = manager.list_volumes()
        
        self.assertEqual(len(volumes), 1)
        self.assertEqual(volumes[0].device, '/dev/sda1')
        self.assertEqual(volumes[0].mountpoint, '/mnt/data')

    @patch('hiveden.shares.btrfs.BtrfsManager._is_btrfs')
    @patch('hiveden.shares.btrfs.BtrfsManager._get_device_for_path')
    @patch('hiveden.shares.btrfs.BtrfsManager._get_uuid_for_device')
    @patch('hiveden.shares.btrfs.BtrfsManager._get_subvol_id')
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_create_share(self, mock_open, mock_makedirs, mock_run, mock_get_id, mock_get_uuid, mock_get_dev, mock_is_btrfs):
        mock_is_btrfs.return_value = True
        mock_get_dev.return_value = '/dev/sda1'
        mock_get_uuid.return_value = '1234-5678'
        mock_get_id.return_value = '257'
        
        manager = BtrfsManager()
        manager.create_share('/mnt/data', 'myshare', '/shares/myshare')

        # Verify subvolume create
        mock_run.assert_any_call(['btrfs', 'subvolume', 'create', '/mnt/data/myshare'], check=True)
        
        # Verify mount
        mock_run.assert_any_call(['mount', '-o', 'subvolid=257', '/dev/sda1', '/shares/myshare'], check=True)
        
        # Verify fstab write
        mock_open.assert_called_with('/etc/fstab', 'a')
        mock_open().write.assert_called_with('UUID=1234-5678 /shares/myshare btrfs subvolid=257,defaults 0 0\n')
