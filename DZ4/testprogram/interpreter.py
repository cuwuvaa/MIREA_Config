import sys
import yaml

MEMORY_SIZE = 1024  # Размер памяти УВМ

def sgn(value):
    if value > 0:
        return 1
    elif value < 0:
        return -1
    else:
        return 0

def interpret_file(binary_path, result_path, mem_range):
    memory = [0] * MEMORY_SIZE
    accumulator = 0

    with open(binary_path, 'rb') as binary_file:
        code = binary_file.read()

    instruction_pointer = 0
    code_size = len(code)

    while instruction_pointer < code_size:
        # Читаем 4 байта команды (младшие байты сначала)
        instruction_bytes = code[instruction_pointer:instruction_pointer+4]
        if len(instruction_bytes) < 4:
            print(f"Неполная команда в позиции {instruction_pointer}")
            break

        instruction_word = int.from_bytes(instruction_bytes, byteorder='little', signed=False)
        A = instruction_word & 0b111  # Биты 0-2

        if A == 1:  # LOAD_CONST
            # Поле B занимает биты 3-10 (8 бит)
            B = (instruction_word >> 3) & 0xFF
            # Приводим B к знаковому 8-битному числу
            if B & 0x80:
                B -= 0x100
            accumulator = B
        elif A == 3:  # READ_MEM
            address = accumulator
            if 0 <= address < MEMORY_SIZE:
                accumulator = memory[address]
            else:
                print(f"Ошибка: выход за пределы памяти при чтении из адреса {address}")
                sys.exit(1)
        elif A == 0:  # WRITE_MEM
            # Поле B занимает биты 3-26 (24 бита)
            B = (instruction_word >> 3) & 0xFFFFFF
            address = B  # Адрес беззнаковый, диапазон [0, 0xFFFFFF]
            if 0 <= address < MEMORY_SIZE:
                memory[address] = accumulator
            else:
                print(f"Ошибка: выход за пределы памяти при записи в адрес {address}")
                sys.exit(1)
        elif A == 2:  # UNARY_SGN
            address = accumulator
            if 0 <= address < MEMORY_SIZE:
                value = memory[address]
                accumulator = sgn(value)
            else:
                print(f"Ошибка: выход за пределы памяти при доступе к адресу {address}")
                sys.exit(1)
        else:
            print(f"Неизвестная команда с кодом A={A} в позиции {instruction_pointer}")
            sys.exit(1)

        instruction_pointer += 4  # Переходим к следующей команде

    # После выполнения программы сохраняем диапазон памяти в файл-результат
    start_addr, end_addr = map(int, mem_range.split(':'))
    if not (0 <= start_addr <= end_addr < MEMORY_SIZE):
        print("Некорректный диапазон памяти")
        sys.exit(1)

    memory_dump = []
    for addr in range(start_addr, end_addr + 1):
        memory_dump.append({'address': addr, 'value': memory[addr]})

    with open(result_path, 'w') as result_file:
        yaml.dump({'memory_dump': memory_dump}, result_file, allow_unicode=True)

def main():
    if len(sys.argv) != 4:
        print("Использование: python interpreter.py <binary_file> <result_file> <memory_range>")
        print("Где <memory_range> в формате start:end")
        sys.exit(1)

    binary_path = sys.argv[1]
    result_path = sys.argv[2]
    mem_range = sys.argv[3]

    interpret_file(binary_path, result_path, mem_range)

if __name__ == '__main__':
    main()

