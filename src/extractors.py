from openai import OpenAI
import dateparser
import dotenv

from src.utils import read_yaml


dotenv.load_dotenv()


client = OpenAI()


def extract_encounter_indices_from_chunk(lines):
    """
    Takes text chunks with line numbers and returns the indices of lines indicating an encounter.
    """
    template = read_yaml("./src/prompts/encounter_index.yaml")
    system_instructions = template["system"]
    user_instructions = template['user'].format(DOC_TEXT="\n".join(lines))
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=[
            {"role": "system",
             "content": system_instructions},
            {"role": "user",
             "content": user_instructions}
        ]
    )

    indices = []
    for i, line in enumerate(completion.choices[0].message.content.strip().splitlines()):
        indices.append(int(line))

    return indices


def extract_encounter_indices(lines, chunk_size=100):
    """
    Takes text with line numbers and returns the indices of lines indicating an encounter
    """
    indices = []
    for i in range(0, len(lines), chunk_size):
        chunk_indices = extract_encounter_indices_from_chunk(lines[i: i + chunk_size])
        indices.extend(chunk_indices)

    return indices


def extract_timestamp_from_encounter_chunk(lines):
    """
    Takes encounter based text chunk and returns timestamp for this encounter
    """
    template = read_yaml("./src/prompts/encounter_timestamp.yaml")
    system_instructions = template["system"]
    user_instructions = template['user'].format(DOC_TEXT="\n".join(lines))
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=[
            {"role": "system",
             "content": system_instructions},
            {"role": "user",
             "content": user_instructions}
        ]
    )

    timestamp = dateparser.parse(completion.choices[0].message.content.strip())

    return timestamp


def extract_findings_from_encounter_chunk(lines):
    """
    Takes encounter based text chunk and returns medical findings in this encounter
    """
    template = read_yaml("./src/prompts/medical_findings.yaml")
    system_instructions = template["system"]
    user_instructions = template['user'].format(DOC_TEXT="\n".join(lines))
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=[
            {"role": "system",
             "content": system_instructions},
            {"role": "user",
             "content": user_instructions}
        ]
    )

    findings = completion.choices[0].message.content.strip().splitlines()

    return findings


def extract_info_from_encounter_chunk(lines: list):
    """
    Takes encounter based text chunk and returns useful info such as timestamp and medical findings
    """
    timestamp = extract_timestamp_from_encounter_chunk(lines)
    findings = extract_findings_from_encounter_chunk(lines)

    return {'timestamp': timestamp,
            'findings': findings,
            'lines': lines
            }
