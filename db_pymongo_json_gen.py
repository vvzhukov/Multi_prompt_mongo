import json
import random
from datetime import datetime, timedelta


def generate_json_records(num_records):
    """Generate records for model_worker.py testing"""

    base_date = datetime.utcnow()
    locations = ["house", "castle", "barn", "forest", "mountain", "village", "city", "cave", "river", "lake"]
    records = []

    for i in range(1, num_records + 1):
        record = {
            "_id": i,
            "system": "Continue the tale",
            "question": f"Once upon a time in a {random.choice(locations)}",
            "status": "new",
            "response": "",
            "time_added": (base_date +
                           timedelta(seconds=random.randint(0, 86400))).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "time_started": "",
            "time_completed": ""
        }
        records.append(record)

    return records


# Generate 1000 records
records = generate_json_records(1000)

# Write the list of records to a JSON file
with open('db_init_content.json', 'w') as file:
    json.dump(records, file, indent=2)

print("JSON records have been written to 'records.json'")
