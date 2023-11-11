import argparse
from browser_env.envs import ScriptBrowserEnv
import json
import os
import re
import random


path_of_this_file = os.path.dirname(os.path.realpath(__file__))


env = ScriptBrowserEnv(
    headless=True,
    slow_mo=0,
    observation_type="accessibility_tree",
    current_viewport_only=False,
    viewport_size={
        "width": 1280,
        "height": 720,
    },
    save_trace_enabled=False,
    sleep_after_execution=0.0,
)


def convert(url, save_path_no_ext=None):
    random_id = random.randint(0, 10000000000)
    with open(f"{path_of_this_file}/tmp_config_{random_id}.json", "w") as f:
        f.write(
            f"""
                {{
                    "storage_state": null,
                    "start_url": "{url}",
                    "geolocation": null
                }}
            """
        )

    obs, info = env.reset(options={"config_file": f"{path_of_this_file}/tmp_config_{random_id}.json"})

    # remove tmp_config_{random_id}.json
    os.remove(f"{path_of_this_file}/tmp_config_{random_id}.json")

    pattern = re.compile(r"[a-zA-Z0-9]")

    new_tree = []

    for line in obs["text"].split("\n"):
        content = " ".join(line.split("'")[1:])
        if bool(pattern.search(content)):
            new_tree.append(line)

    if not save_path_no_ext is None:
        with open(f"{save_path_no_ext}.tree", "w") as f:
            f.write("\n".join(new_tree))

        with open(f"{save_path_no_ext}.json", "w") as f:
            json.dump(info["observation_metadata"], f, indent=4)

    return new_tree, info["observation_metadata"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default="https://www.amazon.com")
    args = parser.parse_args()

    clean_url = (
        args.url.replace("https://", "")
        .replace("http://", "")
        .replace("file://", "")
        .replace("/", "_")
        .replace(".", "_")
        .replace(":", "_")
        .replace("?", "_")
        .replace("=", "_")
        .replace("&", "_")
        .replace("%", "_")
        .replace("#", "_")
    )
    path_out_no_ext = f"{path_of_this_file}/{clean_url}"
    convert(args.url, path_out_no_ext)
