**usage:**
`emul.py [-h] [--username USERNAME] [--hostname HOSTNAME] [--zip-path ZIP_PATH.zip] [--log-path LOG_PATH.log]'`

Описание вашей программы

options:
  -h, --help           show this help message and exit
  --username USERNAME  Имя пользователя
  --hostname HOSTNAME  Имя хоста
  --zip-path ZIP_PATH  Путь к zip-файлу
  --log-path LOG_PATH  Путь к файлу логов

default: user1 my_pc virtual_fs.zip emulator.log

------------------------------------------------------------------------------------------------------------

test:

run: `cuwuvaa@HP:/mnt/c/users/ivank/desktop/УНИК/config/DZ1$`
`python3 test_emulator.py`

output:

`'Error: directory not found.
file4.txt
folder1
folder2
.Directory is empty.
.file1.txt
subfolder1
.Directory 'empty_folder' has been removed.
.Error: directory 'folder1' is not empty. Remove all files inside first.
.Error: directory not found.`

----------------------------------------------------------------------
`Ran 13 tests in 0.248s`
OK
