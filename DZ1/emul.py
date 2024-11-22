import os
import zipfile
import tkinter as tk
from tkinter import scrolledtext


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
        self.current_directory = 'virtual_fs'  # Текущая директория (начинаем с корня '/')
        self.zip_path = zip_path
        self.log_path = log_path
        self.file_system = {}  # Словарь для хранения распакованных файлов и папок
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
                for file in zip_ref.namelist():
                    # Удаляем начальные / для удобства работы с файлами
                    normalized_path = file.lstrip('/')
                    self.file_system[normalized_path] = True  # Добавляем файлы и папки в словарь
        else:
            print("Error: provided file is not a ZIP archive.")

    def ls(self, directory=None):
        """
        Команда 'ls' выводит список файлов и папок в указанной директории (или текущей, если аргумент не передан).
        """
        if directory:
            path = os.path.join(self.current_directory, directory).lstrip('/')
        else:
            path = self.current_directory.lstrip('/')

        output = []
        found_files = False
        for file in self.file_system:
            if file.startswith(path):
                relative_path = file[len(path):].strip('/')
                if '/' not in relative_path:
                    output.append(relative_path)
                    found_files = True

        if not found_files:
            output.append("Directory is empty.")

        # Печатаем и возвращаем результат команды
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
            if self.current_directory != '/':
                self.current_directory = os.path.dirname(self.current_directory.rstrip('/')) + '/'
        else:
            # Переход в указанную директорию
            new_directory = os.path.join(self.current_directory, path).lstrip('/')
            if any(f.startswith(new_directory) for f in self.file_system):
                self.current_directory = new_directory.rstrip('/') + '/'
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

        full_path = os.path.join(self.current_directory, path).rstrip('/') + '/'

        # Проверяем, есть ли в директории другие файлы
        has_files = any(f.startswith(full_path) and f != full_path for f in self.file_system)

        if has_files:
            response = f"Error: directory '{path}' is not empty. Remove all files inside first."
        elif full_path in self.file_system:
            del self.file_system[full_path]  # Удаляем директорию из виртуальной файловой системы
            self._remove_from_zip(full_path)  # Удаляем директорию из ZIP-архива
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
                    if not item.filename.startswith(file_to_remove):
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
        self.host_display = tk.Label(self.window, text=f"current directory: {emulator.username}@{emulator.hostname}:{emulator._get_prompt_directory()}$",
                                     bg="black", fg="green", font=("Consolas", 12), anchor="w")
        self.host_display.grid(row=2, column=0, sticky='w', padx=10, pady=5)

        # Поле для ввода команд
        self.command_entry = tk.Entry(self.window, width=80, bg="black", fg="green", font=("Consolas", 12))
        self.command_entry.grid(row=1, column=0, padx=10, pady=5)

        # Привязываем событие нажатия Enter
        self.command_entry.bind('<Return>', self.run_command)

        # Запуск основного цикла окна
        self.window.mainloop()

    def run_command(self, event):
        """Обработчик ввода команды и её выполнения."""
        command = self.command_entry.get()
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, f"{emulator.username}@{emulator.hostname}:{emulator._get_prompt_directory()}$ {command}\n")
        self.output_text.config(state='disabled')
        with open(emulator.log_path, 'a') as log_file:
            # Записываем ввод команды с текущим местоположением пользователя
            log_file.write(f"{emulator.username}@{emulator.hostname}:{emulator._get_prompt_directory()}$ {command}\n")
        self.command_entry.delete(0, tk.END)  # Очищаем поле ввода

        # Получаем результат команды из эмулятора
        output = self.execute_command(command)
        with open(emulator.log_path, 'a') as log_file:
            log_file.write(f"{output}\n")
        # Обновляем область вывода

        self.host_display.config(text=f"current directory: {emulator.username}@{emulator.hostname}:{emulator._get_prompt_directory()}$")
        self.host_display.update()
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, f"{output}\n")
        self.output_text.config(state='disabled')
        self.output_text.yview(tk.END)  # Прокрутка вниз

    def execute_command(self, command):
        """Метод для выполнения команд через эмулятор."""
        if command.startswith("ls"):
            args = command.split(" ")
            if len(args) == 2:
                return self.emulator.ls(args[1])
            else:
                return self.emulator.ls()
        elif command.startswith("cd "):
            return self.emulator.cd(command.split(" ")[1])
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


# Основной код
if __name__ == "__main__":
    username = "user1"
    hostname = "my_pc"
    zip_path = "virtual_fs.zip"
    log_path = "emulator.log"

    # Создаем объект эмулятора
    emulator = Emulator(username, hostname, zip_path, log_path)

    # Запускаем графический интерфейс
    gui = EmulatorGUI(emulator)
