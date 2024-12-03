import sys
import json
import re
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Парсинг конфигурационного файла и вывод в формате JSON.')
    parser.add_argument('-i', '--input', required=True, help='Путь к входному файлу.')
    parser.add_argument('-o', '--output', required=True, help='Путь к выходному файлу.')
    args = parser.parse_args()
    return args

def remove_comments(data):
    lines = data.split('\n')
    cleaned_lines = []
    in_multiline_comment = False
    for line in lines:
        stripped_line = line.strip()
        if in_multiline_comment:
            if '}}' in stripped_line:
                in_multiline_comment = False
                index = stripped_line.find('}}')
                line = stripped_line[index+2:]
                if line.strip():
                    cleaned_lines.append(line)
                continue
            else:
                continue
        if stripped_line.startswith('{{!'):
            if '}}' in stripped_line:
                in_multiline_comment = False
                index = stripped_line.find('}}')
                line = stripped_line[index+2:]
                if line.strip():
                    cleaned_lines.append(line)
            else:
                in_multiline_comment = True
            continue
        if stripped_line.startswith('*'):
            continue
        else:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)

class Parser:
    def __init__(self, lines):
        self.lines = lines
        self.variables = {}
        self.position = 0

    def current_line(self):
        if self.position < len(self.lines):
            return self.lines[self.position]
        else:
            return None

    def advance(self):
        self.position += 1

    def parse(self):
        results = []
        while self.position < len(self.lines):
            line = self.current_line().strip()
            if not line:
                self.advance()
                continue
            if line.startswith('var'):
                self.parse_variable_declaration()
            elif line == 'begin':
                result = self.parse_dict()
                results.append(result)
            else:
                self.advance()
        return results

    def parse_variable_declaration(self):
        line = self.current_line()
        match = re.match(r'^var\s+([a-z][a-z0-9_]*)\s+(.+)$', line.strip())
        if match:
            var_name = match.group(1).strip()
            var_value_str = match.group(2).strip()
            try:
                var_value = self.parse_value(var_value_str)
                self.variables[var_name] = var_value
                self.advance()
            except ValueError as e:
                raise ValueError(f"Ошибка в строке {self.position + 1}: {e}")
        else:
            raise ValueError(f"Синтаксическая ошибка в строке {self.position + 1}: {line}")

    def parse_value(self, value_str):
        value_str = value_str.strip()
        if value_str.isdigit():
            return int(value_str)
        elif value_str.startswith('#[') and value_str.endswith(']'):
            var_name = value_str[2:-1].strip()
            if var_name in self.variables:
                return self.variables[var_name]
            else:
                raise ValueError(f"Неизвестная переменная: {var_name} в строке {self.position + 1}")
        else:
            raise ValueError(f"Неправильное значение: {value_str} в строке {self.position + 1}")

    def parse_dict(self, expect_begin=True):
        result = {}
        if expect_begin:
            current_line = self.current_line().strip()
            if current_line not in ('begin', 'begin;'):
                raise ValueError(f"Ожидается 'begin' в строке {self.position + 1}")
            self.advance()
        while self.position < len(self.lines):
            line = self.current_line()
            if line is None:
                raise ValueError("Ожидается 'end', но достигнут конец файла.")
            stripped_line = line.strip()
            if stripped_line in ('end', 'end;'):
                self.advance()
                return result
            elif not stripped_line:
                self.advance()
                continue
            else:
                name, value = self.parse_assignment()
                result[name] = value
        raise ValueError("Ожидается 'end', но достигнут конец файла.")

    def parse_assignment(self):
        line = self.current_line()
        starting_position = self.position
        line = line.strip()
        # Match 'name := value' (value can be multi-line)
        assignment_match = re.match(r'^([a-z][a-z0-9_]*)\s*:=\s*(.*)$', line)
        if not assignment_match:
            raise ValueError(f"Синтаксическая ошибка в строке {starting_position + 1}: {line}")
        name = assignment_match.group(1)
        remaining_str = assignment_match.group(2).strip()
        if remaining_str.rstrip(';') in ('begin', 'begin;'):
            # Value is a dict
            if remaining_str.endswith(';'):
                self.advance()  # Move past the 'name := begin;' line
            else:
                self.advance()  # Move past the 'name := begin' line
            value = self.parse_dict(expect_begin=False)
            return name, value
        else:
            # Build up 'value_str' until we find a line ending with ';'
            value_str = remaining_str
            while not value_str.endswith(';'):
                self.advance()
                line = self.current_line()
                if line is None:
                    raise ValueError(f"Ожидается ';' в конце присваивания на строке {self.position + 1}")
                value_str += ' ' + line.strip()
            # Remove the trailing ';'
            value_str = value_str[:-1].strip()
            self.advance()  # Move past the last line of the assignment
            value = self.parse_value(value_str)
            return name, value

def main():
    args = parse_args()
    with open(args.input, 'r', encoding='utf-8') as f:
        data = f.read()
    data = remove_comments(data)
    lines = data.split('\n')
    parser = Parser(lines)
    try:
        results = parser.parse()
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    json_output = json.dumps(results, ensure_ascii=False, indent=2)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(json_output)

if __name__ == '__main__':
    main()