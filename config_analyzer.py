#!/usr/bin/env python3

import glob
import os
import subprocess

DEBUG = False


class Tree:
    class __Node:
        def __init__(self, key):
            self.key = key
            self.children = set()

    def __init__(self):
        self.nodes = {}

    def add_node(self, key: str):
        self.nodes[key] = __Node(key)

    def add_edge(self, key_of_source: str, key_of_dest: str):
        if DEBUG:
            print(f"adding edge from {key_of_source} to {key_of_dest}")
        if key_of_source not in self.nodes:
            self.nodes[key_of_source] = Tree.__Node(key_of_source)
        self.nodes[key_of_dest] = Tree.__Node(key_of_dest)
        self.nodes[key_of_source].children.add(key_of_dest)

    def dump_tree(self):
        for key in self.nodes.keys():
            print(key)

    def dump_tree_to_graphviz(self, path: str):
        with open(path, "w") as dot_file:
            dot_file.write("digraph D {\n")
            for key in self.nodes.keys():
                count = 0
                size = len(self.nodes[key].children)
                if size:
                    # ignore node without children
                    dot_file.write("\t" + key + " -> {\n")
                    for child in self.nodes[key].children:
                        count += 1
                        dot_file.write("\t\t" + child)
                        if count < size:
                            dot_file.write(",")
                        dot_file.write("\n")
                    dot_file.write("\t}\n\n")
            dot_file.write("}")


class ConfigAnalyzer:
    def __init__(self):
        self.REPO_ROOT = (
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"])
            .decode("utf8")
            .strip()
        )
        self.INCLUDE = "#include"
        self.ignored_list = ["third-party", "submodules"]

    def __get_key(self, full_path: str):
        return '"' + os.path.relpath(full_path, self.REPO_ROOT) + '"'

    def __is_ignored(self, full_path: str):
        for item in self.ignored_list:
            if item in full_path:
                return True
        return False

    def analyze_repo(self):
        tree = Tree()
        config_files = glob.glob(self.REPO_ROOT + "/**/*.xcconfig", recursive=True)

        for config_file in config_files:
            if self.__is_ignored(config_file):
                continue
            key = self.__get_key(config_file)
            script_dir = os.path.dirname(config_file)
            os.chdir(script_dir)
            with open(config_file) as f:
                for line in f:
                    line = line.rstrip()
                    if self.INCLUDE in line:
                        if DEBUG:
                            print(line)
                        relative_path = (
                            line.split(self.INCLUDE)[1]
                            # pretty ugly
                            .strip("?")
                            .strip()
                            .split('"')[1]
                            .strip()
                        )
                        key_of_parent = self.__get_key(os.path.abspath(relative_path))
                        tree.add_edge(key_of_parent, key)
        tree.dump_tree()
        tree.dump_tree_to_graphviz(self.REPO_ROOT + "/config.dot")


def __main():
    config_analyzer = ConfigAnalyzer()
    config_analyzer.analyze_repo()


if __name__ == "__main__":
    __main()
