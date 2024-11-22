import os
import sys
import argparse
import subprocess
import tempfile

def get_last_commit(repo_path):
    """
    Получает хэш последнего коммита из репозитория.
    """
    head_path = os.path.join(repo_path, '.git', 'HEAD')
    if not os.path.exists(head_path):
        print(f"Не удалось найти файл HEAD по пути {head_path}")
        return None
    with open(head_path, 'r') as f:
        ref = f.readline().strip()
    if ref.startswith('ref:'):
        ref_path = os.path.join(repo_path, '.git', *ref[5:].split('/'))
        if not os.path.exists(ref_path):
            print(f"Не удалось найти файл ссылки по пути {ref_path}")
            return None
        with open(ref_path, 'r') as f:
            commit_hash = f.readline().strip()
            return commit_hash
    else:
        # Detached HEAD
        return ref

def parse_object(object_hash, repo_path):
    """
    Извлекает информацию из git-объекта по его хэшу, используя 'git cat-file'.
    """
    try:
        # Получаем тип объекта
        obj_type_proc = subprocess.run(['git', '-C', repo_path, 'cat-file', '-t', object_hash],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        obj_type = obj_type_proc.stdout.strip()

        # Получаем содержимое объекта
        obj_content_proc = subprocess.run(['git', '-C', repo_path, 'cat-file', '-p', object_hash],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        raw_data = obj_content_proc.stdout

        if obj_type == 'commit':
            return parse_commit(raw_data, repo_path, object_hash)
        elif obj_type == 'tree':
            return parse_tree(raw_data.encode('utf-8'), repo_path, object_hash)
        elif obj_type == 'blob':
            return parse_blob(raw_data.encode('utf-8'), object_hash)
        else:
            print(f"Неизвестный тип объекта: {obj_type}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Не удалось получить объект {object_hash}: {e.stderr}")
        return None

def parse_commit(content, repo_path, object_hash):
    """
    Парсит объект коммита.
    """
    commit_info = {}
    lines = content.split('\n')
    i = 0
    commit_info['parents'] = []
    while i < len(lines):
        line = lines[i]
        if line == '':
            # Начало сообщения коммита
            i += 1
            break
        parts = line.split(' ', 1)
        if parts[0] == 'tree':
            commit_info['tree'] = parts[1]
        elif parts[0] == 'parent':
            commit_info['parents'].append(parts[1])
        i += 1
    commit_info['type'] = 'commit'
    commit_info['hash'] = object_hash
    # Парсим дерево
    tree = parse_object(commit_info['tree'], repo_path)
    commit_info['files'] = tree['files'] if tree and 'files' in tree else []
    return commit_info

def parse_tree(content, repo_path, object_hash):
    """
    Парсит объект дерева.
    """
    tree_entries = []
    files = []
    idx = 0
    content_bytes = content
    while idx < len(content_bytes):
        # режим доступа заканчивается пробелом
        end_idx = content_bytes.find(b' ', idx)
        mode = content_bytes[idx:end_idx]
        idx = end_idx + 1
        # имя файла заканчивается нулевым байтом
        end_idx = content_bytes.find(b'\x00', idx)
        name = content_bytes[idx:end_idx]
        idx = end_idx + 1
        # SHA1 хэш объекта - 20 байт
        sha = content_bytes[idx:idx+20]
        idx += 20
        sha_hex = sha.hex()
        tree_entries.append({
            'mode': mode.decode('utf-8'),
            'name': name.decode('utf-8', 'replace'),
            'sha': sha_hex,
        })
        # Рекурсивно парсим объекты
        child_obj = parse_object(sha_hex, repo_path)
        if child_obj:
            if child_obj['type'] == 'blob':
                files.append(name.decode('utf-8', 'replace'))
            elif child_obj['type'] == 'tree':
                files.extend(child_obj['files'])
    tree_info = {
        'type': 'tree',
        'entries': tree_entries,
        'files': files,
        'hash': object_hash,
    }
    return tree_info

def parse_blob(content, object_hash):
    """
    Парсит объект блоба.
    """
    blob_info = {
        'type': 'blob',
        'size': len(content),
        'hash': object_hash,
    }
    return blob_info

def build_graph(commit_hash, repo_path, graph, visited=None):
    """
    Строит граф зависимостей коммитов.
    """
    if visited is None:
        visited = set()
    if commit_hash in visited:
        return
    visited.add(commit_hash)
    commit_obj = parse_object(commit_hash, repo_path)
    if not commit_obj:
        return
    graph[commit_hash] = {
        'label': f"Коммит {commit_hash[:7]}",
        'files': commit_obj.get('files', []),
        'parents': commit_obj.get('parents', []),
    }
    # Рекурсивно обрабатываем родителей
    for parent_hash in commit_obj.get('parents', []):
        build_graph(parent_hash, repo_path, graph, visited)

def generate_plantuml(graph):
    """
    Генерирует описание графа зависимостей в формате PlantUML.
    """
    lines = ['@startuml', 'skinparam linetype ortho']
    node_labels = {}
    for commit_hash, data in graph.items():
        label = data['label']
        if data['files']:
            files_str = '\\n'.join(data['files'])
            label += f'\\n{files_str}'
        node_name = f"Node_{commit_hash[:7]}"
        node_labels[commit_hash] = node_name
        lines.append(f'[{label}] as {node_name}')
    # Добавляем связи
    for commit_hash, data in graph.items():
        for parent_hash in data['parents']:
            if parent_hash in node_labels:
                lines.append(f'{node_labels[commit_hash]} --> {node_labels[parent_hash]}')
    lines.append('@enduml')
    return '\n'.join(lines)

def visualize_graph(plantuml_content, visualization_program):
    """
    Выводит граф на экран с помощью программы визуализации.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.uml', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(plantuml_content)
        uml_filename = temp_file.name

    output_filename = os.path.splitext(uml_filename)[0] + '.png'

    try:
        # Разбиваем команду на список, если это строка
        if isinstance(visualization_program, str):
            visualization_command = visualization_program.split()
        else:
            visualization_command = visualization_program

        # Формируем команду для PlantUML
        visualization_command.extend(['-tpng', uml_filename])

        print(f"Выполняется команда: {' '.join(visualization_command)}")
        subprocess.run(visualization_command, check=True)

        # Проверяем, что файл изображения создан
        if os.path.exists(output_filename):
            print(f"Изображение графа сохранено в файл: {output_filename}")
            # Открываем изображение средствами ОС
            if os.name == 'nt':  # Для Windows
                os.startfile(output_filename)
            elif sys.platform == 'darwin':  # Для macOS
                subprocess.run(['open', output_filename])
            elif sys.platform.startswith('linux'):  # Для Linux
                subprocess.run(['xdg-open', output_filename])
            else:
                print(f"Пожалуйста, откройте файл {output_filename} вручную")
        else:
            print("Не удалось найти сгенерированный файл изображения.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды визуализации: {e}")
    finally:
        # Удаляем временный файл .uml
        os.unlink(uml_filename)

def main():
    parser = argparse.ArgumentParser(description='Визуализатор графа зависимостей Git-репозитория.')
    parser.add_argument('visualization_program', help='Путь к программе для визуализации графов.')
    parser.add_argument('repository_path', help='Путь к анализируемому репозиторию.')
    args = parser.parse_args()
    repo_path = args.repository_path
    visualization_program = args.visualization_program

    last_commit_hash = get_last_commit(repo_path)
    if not last_commit_hash:
        print("Не удалось получить последний коммит.")
        sys.exit(1)
    graph = {}
    build_graph(last_commit_hash, repo_path, graph)
    plantuml_content = generate_plantuml(graph)
    visualize_graph(plantuml_content, visualization_program)

if __name__ == '__main__':
    main()
