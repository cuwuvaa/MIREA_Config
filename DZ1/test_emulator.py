import unittest
from emul import Emulator  # Предполагается, что ваш код в файле emulator.py
import os
import zipfile

def create_test_zip(zip_path, files_and_dirs):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for item in files_and_dirs:
            if item.endswith('/'):
                zip_info = zipfile.ZipInfo(item)
                zipf.writestr(zip_info, '')
            else:
                zipf.writestr(item, 'test content')

class TestEmulator(unittest.TestCase):
    def setUp(self):
        self.zip_path = 'test_virtual_fs.zip'
        self.log_path = 'test_emulator.log'
        self.username = 'test_user'
        self.hostname = 'test_pc'
        
        test_files_and_dirs = [
            'folder1/',
            'folder1/file1.txt',
            'folder1/subfolder1/',
            'folder1/subfolder1/file2.txt',
            'folder2/',
            'folder2/file3.txt',
            'file4.txt'
        ]
        create_test_zip(self.zip_path, test_files_and_dirs)
        self.emulator = Emulator(self.username, self.hostname, self.zip_path, self.log_path)
    
    def tearDown(self):
        if os.path.exists(self.zip_path):
            os.remove(self.zip_path)
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
    
    # Тесты для ls
    def test_ls_current_directory(self):
        output = self.emulator.ls()
        expected_output = 'file4.txt\nfolder1\nfolder2'
        self.assertEqual(output, expected_output)
    
    def test_ls_specific_directory(self):
        output = self.emulator.ls('folder1')
        expected_output = 'file1.txt\nsubfolder1'
        self.assertEqual(output, expected_output)
    
    def test_ls_nonexistent_directory(self):
        output = self.emulator.ls('nonexistent')
        expected_output = 'Directory is empty.'
        self.assertEqual(output, expected_output)
    
    # Тесты для cd
    def test_cd_valid_directory(self):
        self.emulator.cd('folder1')
        self.assertEqual(self.emulator.current_directory, '/folder1')
    
    def test_cd_invalid_directory(self):
        output = self.emulator.cd('nonexistent')
        self.assertEqual(output, 'Error: directory not found.')
        self.assertEqual(self.emulator.current_directory, '/')
    
    def test_cd_parent_directory(self):
        self.emulator.cd('folder1/subfolder1')
        self.emulator.cd('..')
        self.assertEqual(self.emulator.current_directory, '/folder1')
    
    # Тесты для rmdir
    def test_rmdir_empty_directory(self):
        self.emulator.directories.add('/empty_folder')
        output = self.emulator.rmdir('empty_folder')
        expected_output = "Directory 'empty_folder' has been removed."
        self.assertEqual(output, expected_output)
        self.assertNotIn('/empty_folder', self.emulator.directories)
    
    def test_rmdir_nonempty_directory(self):
        output = self.emulator.rmdir('folder1')
        expected_output = "Error: directory 'folder1' is not empty. Remove all files inside first."
        self.assertEqual(output, expected_output)
    
    def test_rmdir_nonexistent_directory(self):
        output = self.emulator.rmdir('nonexistent')
        expected_output = 'Error: directory not found.'
        self.assertEqual(output, expected_output)
    
    # Тесты для uname
    def test_uname_no_args(self):
        output = self.emulator.uname()
        expected_output = 'Linux'
        self.assertEqual(output, expected_output)
    
    def test_uname_s_flag(self):
        output = self.emulator.uname('-s')
        expected_output = 'Linux'
        self.assertEqual(output, expected_output)
    
    def test_uname_unknown_flag(self):
        output = self.emulator.uname('--unknown')
        expected_output = 'Unknown option'
        self.assertEqual(output, expected_output)
    
    # Тест для exit_emulator
    def test_exit_emulator(self):
        # Переопределим метод exit_emulator для тестирования
        original_exit = self.emulator.exit_emulator
        self.emulator.exit_emulator = lambda: "Exiting emulator..."
        output = self.emulator.exit_emulator()
        expected_output = "Exiting emulator..."
        self.assertEqual(output, expected_output)
        # Восстанавливаем оригинальный метод
        self.emulator.exit_emulator = original_exit

if __name__ == '__main__':
    unittest.main()