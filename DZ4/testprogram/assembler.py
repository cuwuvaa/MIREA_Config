import sys
import yaml

def assemble_instruction(line):
    # Убираем комментарии и лишние пробелы
    line = line.split('#')[0].strip()
    if not line:
        return None, None  # Пустая строка или комментарий

    parts = line.split()
    instruction = parts[0].upper()
    operands = parts[1:] if len(parts) > 1 else []

    A = 0
    B = 0

    if instruction == 'LOAD_CONST':
        A = 1
        if len(operands) != 1:
            raise ValueError(f"LOAD_CONST требует 1 операнд, получено {len(operands)}")
        B = int(operands[0])
        # Поле B занимает биты 3-10 (8 бит)
        if not -128 <= B <= 127:
            raise ValueError(f"Константа {B} выходит за пределы диапазона [-128, 127]")
        B &= 0xFF  # Приводим к 8 битам
    elif instruction == 'READ_MEM':
        A = 3
        if operands:
            raise ValueError(f"READ_MEM не требует операндов, получено {len(operands)}")
    elif instruction == 'WRITE_MEM':
        A = 0
        if len(operands) != 1:
            raise ValueError(f"WRITE_MEM требует 1 операнд, получено {len(operands)}")
        B = int(operands[0])
        # Поле B занимает биты 3-26 (24 бита)
        if not 0 <= B <= 0xFFFFFF:
            raise ValueError(f"Адрес {B} выходит за пределы диапазона [0, {0xFFFFFF}]")
    elif instruction == 'UNARY_SGN':
        A = 2
        if operands:
            raise ValueError(f"UNARY_SGN не требует операндов, получено {len(operands)}")
    else:
        raise ValueError(f"Неизвестная инструкция '{instruction}'")

    # Формируем 32-битное слово команды
    instruction_word = (B << 3) | A  # Сдвигаем B на 3 бита влево и добавляем A

    # Преобразуем в байты (младший байт первый)
    instruction_bytes = instruction_word.to_bytes(4, byteorder='little', signed=False)

    # Формируем запись для лога
    log_entry = {
        'instruction': instruction,
        'A': A,
        'B': B if instruction != 'LOAD_CONST' or B <= 127 else B - 256,  # Для отображения знакового B в логе
        'bytes': list(instruction_bytes)
    }

    return instruction_bytes, log_entry

def assemble_file(source_path, binary_path, log_path):
    with open(source_path, 'r') as source_file:
        lines = source_file.readlines()

    binary_code = bytearray()
    log_entries = []

    for line_number, line in enumerate(lines, start=1):
        try:
            instruction_bytes, log_entry = assemble_instruction(line)
            if instruction_bytes:
                binary_code.extend(instruction_bytes)
                log_entries.append(log_entry)
        except ValueError as e:
            print(f"Ошибка в строке {line_number}: {e}")
            sys.exit(1)

    # Записываем бинарный файл
    with open(binary_path, 'wb') as binary_file:
        binary_file.write(binary_code)

    # Записываем лог в YAML-файл
    with open(log_path, 'w') as log_file:
        yaml.dump(log_entries, log_file, allow_unicode=True)

def main():
    if len(sys.argv) != 4:
        print("Использование: python assembler.py <source_file> <binary_file> <log_file>")
        sys.exit(1)

    source_path = sys.argv[1]
    binary_path = sys.argv[2]
    log_path = sys.argv[3]

    assemble_file(source_path, binary_path, log_path)

if __name__ == '__main__':
    main()
