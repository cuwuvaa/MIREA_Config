import os
import zipfile
import argparse
import sys
import tkinter as tk
from tkinter import scrolledtext
from pathlib import PurePosixPath as Path


class Emulator:
    def __init__(self, username, hostname, zip_path, log_path):
        """
        Конструктор класса Emulator. Инициализирует пользователя, ПК, путь к архиву файловой системы и файл лога.

        :param username: Имя пользователя
        :param hostname: Имя компьютера
        :param zip_path: Путь к архиву файловой системы (ZIP)
        :param log_path: Путь к файлу лога
        """
        self.username = username
        self.hostname = hostname
        self.current_directory = '/'  # Текущая директория (начинаем с корня '/')
        self.zip_path = zip_path
        self.log_path = log_path
        self.file_system = {}  # Словарь для хранения распакованных файлов и папок
        self.directories = set()  # Множество директорий
        self.files = set()  # Множество файлов
        self._load_file_system()  # Распаковываем архив в память

    def _log(self, command, output):
        """
        Метод для записи команды пользователя и вывода программы в лог-файл.

        :param command: Ввод пользователя
        :param output: Вывод программы
        """
        with open(self.log_path, 'a') as log_file:
            # Записываем ввод команды с текущим местоположением пользователя
            log_file.write(f"{self.username}@{self.hostname}:{self._get_prompt_directory()}$ {command}\n")
            # Записываем результат команды
            if output:
                log_file.write(f"{output}\n")

    def _get_prompt_directory(self):
        """Метод для получения текущей директории для отображения в prompt."""
        return self.current_directory if self.current_directory != '/' else '/'

    def _load_file_system(self):
        """
        Метод для распаковки ZIP архива в виртуальную файловую систему.
        """
        if zipfile.is_zipfile(self.zip_path):
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                self.file_system = {}
                self.directories = set()
                self.files = set()
                self.directories.add('/')  # Добавляем корневую директорию

                for file in zip_ref.namelist():
                    # Удаляем начальные / для удобства работы с файлами
                    file = file.lstrip('/')
                    normalized_path = '/' + file

                    self.file_system[normalized_path] = True

                    path_obj = Path(normalized_path)

                    if normalized_path.endswith('/'):
                        # Это директория
                        self.directories.add(str(path_obj))
                    else:
                        # Это файл
                        self.files.add(str(path_obj))

                        # Добавляем все родительские директории
                        for parent in path_obj.parents:
                            self.directories.add(str(parent))
        else:
            print("Error: provided file is not a ZIP archive.")

    def ls(self, directory=None):
        """
        Команда 'ls' выводит список файлов и папок в указанной директории (или текущей, если аргумент не передан).
        """
        if directory:
            path_obj = Path(directory)
            if path_obj.is_absolute():
                path = path_obj
            else:
                path = (Path(self.current_directory) / path_obj)
        else:
            path = Path(self.current_directory)

        str_path = str(path)
        if str_path == '':
            str_path = '/'

        entries = set()
        dir_prefix = str_path if str_path != '/' else ''
        dir_prefix += '/'

        len_prefix = len(dir_prefix)
        # Ищем непосредственных потомков в директориях
        for d in self.directories:
            if d.startswith(dir_prefix):
                rest = d[len_prefix:]
                if '/' not in rest and rest != '':
                    entries.add(rest)
        # Ищем файлы
        for f in self.files:
            if f.startswith(dir_prefix):
                rest = f[len_prefix:]
                if '/' not in rest:
                    entries.add(rest)

        if entries:
            output = sorted(entries)
        else:
            output = ["Directory is empty."]

        response = '\n'.join(output)
        print(response)
        return response

    def cd(self, path):
        """
        Команда 'cd' позволяет перемещаться между директориями.

        :param path: Путь к новой директории
        """
        if path == "..":
            # Переход на уровень выше
            new_directory = Path(self.current_directory).parent
            if str(new_directory) == '':
                new_directory = Path('/')
        else:
            # Переход в указанную директорию
            path_obj = Path(path)
            if path_obj.is_absolute():
                new_directory = path_obj
            else:
                new_directory = Path(self.current_directory) / path_obj

        # Нормализуем путь
        new_directory = new_directory

        str_new_directory = str(new_directory)
        if str_new_directory == '':
            str_new_directory = '/'

        if str_new_directory in self.directories:
            self.current_directory = str_new_directory
        else:
            response = "Error: directory not found."
            print(response)
            return response
        return ""

    def rmdir(self, path=None):
        """
        Команда 'rmdir' удаляет директорию, если она пуста.
        Если в директории есть файлы, будет выбита ошибка.
        Если аргумент не передан, выводится сообщение об ошибке.
        """
        if path is None:
            response = "Error: rmdir command requires an argument."
            print(response)
            return response

        full_path = (Path(self.current_directory) / path).resolve()
        str_full_path = str(full_path)
        if str_full_path == '':
            str_full_path = '/'

        # Проверяем, есть ли в директории другие файлы или директории
        has_entries = any(
            f != str_full_path and f.startswith(str_full_path + '/')
            for f in self.files.union(self.directories)
        )

        if has_entries:
            response = f"Error: directory '{path}' is not empty. Remove all files inside first."
        elif str_full_path in self.directories:
            self.directories.remove(str_full_path)
            self._remove_from_zip(str_full_path)  # Удаляем директорию из ZIP-архива
            response = f"Directory '{path}' has been removed."
        else:
            response = "Error: directory not found."

        print(response)
        return response

    def _remove_from_zip(self, file_to_remove):
        """
        Метод для удаления файла или директории из ZIP архива.
        """
        temp_zip = self.zip_path + '.temp'  # Временный файл для нового архива
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            with zipfile.ZipFile(temp_zip, 'w') as new_zip:
                for item in zip_ref.infolist():
                    # Проверяем, что файл или папка не совпадают с удаляемым
                    normalized_item = '/' + item.filename.lstrip('/')
                    if not normalized_item.startswith(file_to_remove + '/'):
                        new_zip.writestr(item, zip_ref.read(item.filename))
        # Заменяем старый архив новым
        os.replace(temp_zip, self.zip_path)

    def uname(self, args=None):
        """
        Команда 'uname' выводит информацию о системе. Поддерживаются флаги: -s, -n, -v
        """
        kernel_name = "Linux"
        node_name = self.hostname
        version = "1.0.0-custom"

        if args is None:
            return kernel_name
        elif args == "-s":
            return kernel_name
        elif args == "-n":
            return node_name
        elif args == "-v":
            return version
        else:
            return "Unknown option"

    def exit_emulator(self):
        """
        Метод выхода из эмулятора. Вносим изменения прямо в архив.
        """
        print("All changes saved to the archive.")
        exit()


class EmulatorGUI:
    def __init__(self, emulator):
        self.emulator = emulator

        # Создаем главное окно
        self.window = tk.Tk()
        self.window.title("Linux Emulator")
        self.window.configure(bg="black")  # Темная тема

        # Создаем область вывода
        self.output_text = scrolledtext.ScrolledText(self.window, width=80, height=20, bg="black", fg="green",
                                                     state='disabled', font=("Consolas", 12))
        self.output_text.grid(row=0, column=0, padx=10, pady=10)

        # Область для отображения текущего хоста и директории (нередактируемая)
        self.host_display = tk.Label(self.window,
                                     text=f"{emulator.username}@{emulator.hostname}:{emulator._get_prompt_directory()}$",
                                     bg="black", fg="green", font=("Consolas", 12), anchor="w")
        self.host_display.grid(row=2, column=0, sticky='w', padx=10, pady=5)

        # Поле для ввода команд
        self.command_entry = tk.Entry(self.window, width=80, bg="black", fg="green", font=("Consolas", 12))
        self.command_entry.grid(row=1, column=0, padx=10, pady=5)
        self.command_entry.focus_set()  # Фокус на поле ввода

        # Привязываем событие нажатия Enter
        self.command_entry.bind('<Return>', self.run_command)

        # Запуск основного цикла окна
        self.window.mainloop()

    def run_command(self, event):
        """Обработчик ввода команды и её выполнения."""
        command = self.command_entry.get()
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END,
                                f"{self.emulator.username}@{self.emulator.hostname}:{self.emulator._get_prompt_directory()}$ {command}\n")
        self.output_text.config(state='disabled')
        with open(self.emulator.log_path, 'a') as log_file:
            # Записываем ввод команды с текущим местоположением пользователя
            log_file.write(
                f"{self.emulator.username}@{self.emulator.hostname}:{self.emulator._get_prompt_directory()}$ {command}\n")
        self.command_entry.delete(0, tk.END)  # Очищаем поле ввода

        # Получаем результат команды из эмулятора
        output = self.execute_command(command)
        with open(self.emulator.log_path, 'a') as log_file:
            log_file.write(f"{output}\n")
        # Обновляем область вывода

        self.host_display.config(
            text=f"{self.emulator.username}@{self.emulator.hostname}:{self.emulator._get_prompt_directory()}$")
        self.host_display.update()
        self.output_text.config(state='normal')
        if output:
            self.output_text.insert(tk.END, f"{output}\n")
        self.output_text.config(state='disabled')
        self.output_text.yview(tk.END)  # Прокрутка вниз

    def execute_command(self, command):
        """Метод для выполнения команд через эмулятор."""
        command = command.strip()
        if command.startswith("ls"):
            args = command.split(" ")
            if len(args) == 2:
                return self.emulator.ls(args[1])
            else:
                return self.emulator.ls()
        elif command.startswith("cd "):
            return self.emulator.cd(command.split(" ")[1])
        elif command == "cd":
            return self.emulator.cd('/')
        elif command.startswith("rmdir"):
            args = command.split(" ")
            if len(args) == 2:
                return self.emulator.rmdir(args[1])
            else:
                return self.emulator.rmdir()
        elif command.startswith("uname"):
            args = command.split(" ")
            if len(args) == 2:
                return self.emulator.uname(args[1])
            else:
                return self.emulator.uname()
        elif command == "exit":
            self.window.destroy()
            return "Exiting emulator..."
        else:
            return "Unknown command."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Описание вашей программы')

    parser.add_argument('--username', type=str, default='user1', help='Имя пользователя')
    parser.add_argument('--hostname', type=str, default='my_pc', help='Имя хоста')
    parser.add_argument('--zip-path', type=str, default='virtual_fs.zip', help='Путь к zip-файлу')
    parser.add_argument('--log-path', type=str, default='emulator.log', help='Путь к файлу логов')

    args = parser.parse_args()

    username = args.username
    hostname = args.hostname
    zip_path = args.zip_path
    log_path = args.log_path

    # Создаем объект эмулятора
    emulator = Emulator(username, hostname, zip_path, log_path)

    # Запускаем графический интерфейс
    gui = EmulatorGUI(emulator)