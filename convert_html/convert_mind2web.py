import json
import os
from convert_html import convert
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--json", type=str, default="/mnt/c/Users/Sean/Downloads/html_to_trees/train_10.json")
args = parser.parse_args()

web2mind_json_path = args.json
out_path = web2mind_json_path.split(".")[0]
os.makedirs(out_path, exist_ok=True)
web2mind_json = None
solution_tag = "__SOLUTION__BEGINS__HERE__"


def dump_html(html, solution_id, save_path):
    html = html.replace("<textarea", "<input").replace("</textarea>", "</input>")
    solution_idx = html.find(f'backend_node_id="{solution_id}"')
    left_idx = solution_idx
    while html[left_idx] != "<":
        left_idx -= 1

    html = html[:left_idx] + solution_tag + html[left_idx:]
    with open(save_path, "w") as f:
        f.write(html)

    delete_callback = lambda _: os.remove(save_path)
    return delete_callback


with open(web2mind_json_path, "r") as f:
    web2mind_json = json.load(f)

results = []

for task_idx, task in enumerate(web2mind_json):
    print("\n", task_idx, ">", task["confirmed_task"])
    for action_idx, action in enumerate(task["actions"]):
        solutions = action["pos_candidates"]
        if len(solutions) != 1:
            continue
        solution = solutions[0]
        solution_id = solution["backend_node_id"]
        html = action["raw_html"]
        save_path = f"{out_path}/tmp_{task_idx}_{action_idx}.html"
        delete_callback = dump_html(html, solution_id, save_path)
        tree, info = convert(f"file://{save_path}")
        # tree, info = convert(f"file://{save_path}", f"{out_path}/{task_idx}_{action_idx}")

        solution_idx, i = -1, 0
        while i < len(tree):
            if len(tree[i]) > 5000:
                solution_idx = -1
                print("Tree element too long, skipping! Length: ", len(tree[i]))
                break
            if solution_tag in tree[i]:
                solution_idx = i
                if tree[i].strip().endswith(f" '{solution_tag}'"):
                    tree.pop(solution_idx)
                    i -= 1
                else:
                    tree[i] = tree[i].replace(solution_tag, "")
            i += 1

        if solution_idx < 0 or solution_idx >= len(tree):
            print("Solution not found!")
            continue

        print(tree[solution_idx])
        webarena_solution_node_id = re.findall(r"\[\s*(\d+)\]", tree[solution_idx])[0]

        results.append(
            {
                "task_idx": task_idx,
                "action_idx": action_idx,
                "task_objective": task["confirmed_task"],
                "task_subdomain": task["subdomain"],
                "task_domain": task["domain"],
                "task_website": task["website"],
                "task_high_level_plan": task["action_reprs"],
                "action_operation": action["operation"],
                "solution_id": webarena_solution_node_id,
                "tree": "\n".join(tree),
                "info": info,
            }
        )
        delete_callback(None)


with open(f"{out_path}/results.json", "w") as f:
    f.write(json.dumps(results, indent=4))
