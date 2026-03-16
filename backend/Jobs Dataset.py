from datasets import load_dataset
import json
import os

BASE_PATH = "/Users/aditya/Downloads/Antigravity/backend/app/data"
DATASET_DIR = os.path.join(BASE_PATH, "job_skill_dataset")
JSON_OUTPUT = os.path.join(BASE_PATH, "job_skill_dataset.json")

def main():
    # Ensure directory exists
    os.makedirs(BASE_PATH, exist_ok=True)

    # Download dataset
    dataset = load_dataset("batuhanmtl/job-skill-set")
    dataset.save_to_disk(DATASET_DIR)

    # Convert to valid JSON array
    data = dataset["train"].to_list()
    with open(JSON_OUTPUT, "w") as f:
        json.dump(data, f, indent=4)

    print("Dataset and JSON saved successfully")

if __name__ == "__main__":
    main()
