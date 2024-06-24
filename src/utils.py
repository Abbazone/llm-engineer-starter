import yaml
import re


def read_yaml(path: str) -> dict[str, any]:
    try:
        with open(path, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise ValueError(f"Yaml loading failed due to: {e}")


def has_numbers(input_string):
    return bool(re.search(r'\d\d', input_string))

