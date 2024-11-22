#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import tempfile
import unittest

def parse_args():
    parser = argparse.ArgumentParser(description='Git Dependency Graph Visualizer')
    parser.add_argument('viz_tool', help='Path to graph visualization program')
    parser.add_argument('repo_path', help='Path to the git repository to analyze')
    parser.add_argument('--max-commits', type=int, help='Maximum number of commits to display')
    parser.add_argument('--since', help='Show commits more recent than a specific date')
    parser.add_argument('--until', help='Show commits older than a specific date')
    return parser.parse_args()

def get_commits(repo_path, max_commits=None, since=None, until=None):
    """
    Returns a list of commit hashes in the repository.
    """
    cmd = ['git', '-C', repo_path, 'rev-list', '--all']
    if since:
        cmd.extend(['--since', since])
    if until:
        cmd.extend(['--until', until])
    if max_commits:
        cmd.extend(['-n', str(max_commits)])
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error getting commits: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    commits = result.stdout.strip().split('\n')
    return commits

def get_parents(repo_path, commit):
    """
    Returns a list of parent commits for the given commit.
    """
    cmd = ['git', '-C', repo_path, 'rev-list', '--parents', '-n', '1', commit]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error getting parents of commit {commit}: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    parts = result.stdout.strip().split()
    return parts[1:]  # The first hash is the commit itself

def get_files_and_folders(repo_path, commit):
    """
    Returns a set of files and folders in the given commit.
    """
    # Get the tree of the commit
    cmd = ['git', '-C', repo_path, 'ls-tree', '-r', '--name-only', commit]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error getting files for commit {commit}: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    files = result.stdout.strip().split('\n')
    folders = {os.path.dirname(file) for file in files if os.path.dirname(file)}
    return set(files).union(folders)

def build_dependency_graph(repo_path, max_commits=None, since=None, until=None):
    """
    Builds the dependency graph of commits.
    """
    commits = get_commits(repo_path, max_commits, since, until)
    graph = {}
    for commit in commits:
        parents = get_parents(repo_path, commit)
        files_and_folders = get_files_and_folders(repo_path, commit)
        graph[commit] = {
            'parents': parents,
            'files_folders': files_and_folders
        }
    return graph

def generate_plantuml(graph):
    """
    Generates PlantUML code for the given graph.
    """
    uml = [
        '@startuml',
        'digraph G {',
        'node [shape=box];',
        'skinparam dpi 150',  # Adjust DPI for better readability
        'skinparam defaultFontSize 12',  # Adjust font size if needed
    ]
    for commit, data in graph.items():
        label = f"Commit: {commit[:7]}\\nFiles/Folders:\\n" + "\\n".join(sorted(data['files_folders']))
        # Escape double quotes in label
        label = label.replace('"', '\\"')
        uml.append(f'"{commit}" [label="{label}"];')
        for parent in data['parents']:
            if parent in graph:
                uml.append(f'"{parent}" -> "{commit}";')
    uml.append('}')
    uml.append('@enduml')
    return '\n'.join(uml)

def visualize_graph(plantuml_code, viz_tool):
    """
    Saves the PlantUML code to a file in the script's directory, invokes the visualization tool, and displays the graph.
    """
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the filename for the PlantUML file and the output image
    uml_filename = os.path.join(script_dir, 'dependency_graph.uml')

    # Write the PlantUML code to the file
    with open(uml_filename, 'w') as f:
        f.write(plantuml_code)

    # Run the visualization tool to generate the SVG image
    result = subprocess.run([viz_tool, '-tsvg', uml_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error generating SVG image: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Determine the output image filename (.svg extension)
    image_filename = uml_filename[:-4] + '.svg'  # Replace .uml with .svg

    # Check if the image was generated
    if os.path.exists(image_filename):
        print(f"SVG image generated at: {image_filename}")
        print("You can open it in a web browser or vector graphics editor to zoom without loss of quality.")
    else:
        print("Failed to generate SVG image.")

class TestDependencyGraph(unittest.TestCase):

    def setUp(self):
        # Set up a temporary git repository for testing
        self.tmp_repo = tempfile.TemporaryDirectory()
        subprocess.run(['git', 'init'], cwd=self.tmp_repo.name)
        # Create some commits
        with open(os.path.join(self.tmp_repo.name, 'file1.txt'), 'w') as f:
            f.write('Hello World')
        subprocess.run(['git', 'add', 'file1.txt'], cwd=self.tmp_repo.name)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=self.tmp_repo.name)
        with open(os.path.join(self.tmp_repo.name, 'file2.txt'), 'w') as f:
            f.write('Another file')
        subprocess.run(['git', 'add', 'file2.txt'], cwd=self.tmp_repo.name)
        subprocess.run(['git', 'commit', '-m', 'Second commit'], cwd=self.tmp_repo.name)

    def tearDown(self):
        # Clean up the temporary repository
        self.tmp_repo.cleanup()

    def test_get_commits(self):
        commits = get_commits(self.tmp_repo.name)
        self.assertEqual(len(commits), 2)

    def test_get_parents(self):
        commits = get_commits(self.tmp_repo.name)
        parents = get_parents(self.tmp_repo.name, commits[0])
        self.assertEqual(parents, [])
        parents = get_parents(self.tmp_repo.name, commits[1])
        self.assertEqual(len(parents), 1)

    def test_get_files_and_folders(self):
        commits = get_commits(self.tmp_repo.name)
        files_folders = get_files_and_folders(self.tmp_repo.name, commits[0])
        self.assertIn('file1.txt', files_folders)
        files_folders = get_files_and_folders(self.tmp_repo.name, commits[1])
        self.assertIn('file1.txt', files_folders)
        self.assertIn('file2.txt', files_folders)

    def test_build_dependency_graph(self):
        graph = build_dependency_graph(self.tmp_repo.name)
        self.assertEqual(len(graph), 2)
        for commit, data in graph.items():
            self.assertIn('parents', data)
            self.assertIn('files_folders', data)

    def test_generate_plantuml(self):
        graph = build_dependency_graph(self.tmp_repo.name)
        uml_code = generate_plantuml(graph)
        self.assertIn('@startuml', uml_code)
        self.assertIn('@enduml', uml_code)

if __name__ == '__main__':
    args = parse_args()
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        unittest.main(argv=sys.argv[:1])
    else:
        dependency_graph = build_dependency_graph(args.repo_path, args.max_commits, args.since, args.until)
        plantuml_code = generate_plantuml(dependency_graph)
        visualize_graph(plantuml_code, args.viz_tool)