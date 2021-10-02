import yaml
import re
import sys
import os
import requests
import markdown
import utils
import asyncio
import jinja2
import os
from jinja2 import Environment, BaseLoader
Template = Environment(loader=BaseLoader, block_start_string="@%", block_end_string="@%",variable_start_string="@[", variable_end_string="@]")


url = sys.argv[1]
file = sys.argv[2]
folder = sys.argv[3]
os.chdir(folder)

def main():
    global url
    global file

    r = requests.get(url + "/" + file)
    metadata = yaml.load(r.text)
    nodes = metadata["tangle"]

    for key, node in nodes.items():
        if node.get("from", None):
            r = requests.get(url + "/" + node["from"]["file"])
            root = r.text
            nodes_recurse = yaml.load(root)["tangle"]
            nodes[key]["text"] = nodes_recurse[key]["text"]

    for mangle_node in metadata["mangle"]:
        file_name = mangle_node["file"]
        nodes_to_dump = []
        for snippet_ref in mangle_node["snippet_refs"]:
            nodes_to_dump.append(nodes[snippet_ref])

        with open(file_name, 'w') as a_writer:
            final_code = ""
            for n in nodes_to_dump:
                final_code += n["text"]
            code = Template.from_string(final_code).render(_=nodes)
            code = Template.from_string(code).render(_=code)
            a_writer.write(code)

        if "post" in mangle_node:
            exec(mangle_node["post"])

if __name__ == '__main__':
    main()

