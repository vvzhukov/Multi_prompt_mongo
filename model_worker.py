from transformers import pipeline, AutoTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from pymongo import MongoClient, ReturnDocument
from datetime import datetime
import os
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure
DB_URI = os.getenv("MONGO_URI", "mongodb+srv://usr:pwd@cluster0.ycbqnn4.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "prompt_multiproc")
REQUESTS_COLLECTION = os.getenv("REQUESTS_COLLECTION", "mongorequests")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 10))
WORKER_CNT = int(os.getenv("WORKER_CNT", 5))
TIMEOUT = int(os.getenv("TIMEOUT", 15))
MIN_LEN = int(os.getenv("MIN_LEN", 5))
MAX_LEN = int(os.getenv("MAX_LEN", 200))
MODEL_NAME = str(os.getenv("MODEL_NAME", "roneneldan/TinyStories-33M"))
TEMPLATE = str(os.getenv("TEMPLATE", "phi3.template"))

# Init LLM
tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
# TODO model settings (custom tokenizer, parameters, and etc.)
llm_pipeline = pipeline("text-generation",
                        model=MODEL_NAME)


def read_template(template_file):
    """Read prompt template from file"""

    try:
        with open(template_file, 'r') as file:
            template = file.read()
        return template
    except Exception as e:
        logging.error(f"Error reading template file {template_file}: {e}")
        exit(1)


def apply_template(system, question):
    """Apply template to transform the prompt"""

    template = read_template(TEMPLATE)
    # TODO deal with user and assistant
    return template.replace("{{ system }}", system).replace("{{ question }}", question)


def process_prompt(request):
    """Process request using reformatted template"""

    try:
        formatted_input = apply_template(request.get('system', ''), request.get('question', ''))
        response = llm_pipeline(formatted_input,
                                min_length=MIN_LEN,
                                max_length=MAX_LEN,
                                truncation=True,
                                pad_token_id=llm_pipeline.tokenizer.eos_token_id)[0]["generated_text"]
        completion_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return request["_id"], response, completion_time
    except Exception as e:
        logging.error(f"Error processing request {request['_id']}: {e}")
        return request["_id"], None, None


def worker_mgr():
    """Worker manager: connects to DB, creates workers, updates DB"""

    # Connect to MONGO
    try:
        client = MongoClient(DB_URI)
        db = client[DB_NAME]
        req_coll = db[REQUESTS_COLLECTION]
    except Exception as e:
        logging.error(f"Error connecting to DB: {DB_URI}: {e}")
        exit(1)

    while True:
        # Fetch BATCH_SIZE records from MongoDB
        requests = list(req_coll.find({"status": "new"}).limit(BATCH_SIZE))
        id_list = [rec['_id'] for rec in requests]

        if requests:
            logging.info(f"Processing records: {id_list}.")
        else:
            logging.info("No more requests to process.")
            break

        # Set batch processing start time
        start_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        req_coll.update_many(
            {"_id": {"$in": id_list}},
            {"$set": {"time_started": start_time}}
        )


        # Create workers for the retrieved batch of the data
        with ThreadPoolExecutor(max_workers=WORKER_CNT) as executor:
            futures = {executor.submit(process_prompt, req): req for req in requests}
            try:
                for future in as_completed(futures, timeout=TIMEOUT):
                    request_id, response, completion_time = future.result()
                    if response:
                        # Update the request collection when prompt processed
                        req_coll.find_one_and_update(
                            {"_id": request_id},
                            {"$set": {"status": "processed",
                                      "response": response,
                                      "time_completed": completion_time}},
                            return_document=ReturnDocument.AFTER
                        )
            # TODO: Better error handling
            except Exception as e:
                if e == TimeoutError:
                    logging.error(f"Processing records {[rec['_id'] for rec in requests]} timed out.")
                    # Mark records as not being processed
                else:
                    logging.error(f"Error processing request {[rec['_id'] for rec in requests]}: {e}")
    # Close DB connection
    client.close()


if __name__ == '__main__':
    # arguments given by specification
    parser = argparse.ArgumentParser(description="Process LLM requests from MongoDB.")
    parser.add_argument('--parallel', type=int, default=WORKER_CNT, help='Number of workers')
    parser.add_argument('--model', type=str, default=MODEL_NAME, help='Model name')
    parser.add_argument('--mongo_connection_string', type=str, default=DB_URI, help='MongoDB connection string')
    parser.add_argument('--template', type=str, default=TEMPLATE, help='Template name')
    # extra arguments
    parser.add_argument('--db_name', type=str, default=DB_NAME, help='Database name')
    parser.add_argument('--requests_collection', type=str, default=REQUESTS_COLLECTION, help='Requests collection name')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE, help='Batch size (to feed the workers)')
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='Worker prompt timeout')
    parser.add_argument('--min_len', type=int, default=MIN_LEN, help='Prompt generation parameters')
    parser.add_argument('--max_len', type=int, default=MAX_LEN, help='Prompt generation parameters')

    # TODO Sanity check for parameters (num of workers, batch size, etc.)

    args = parser.parse_args()
    WORKER_COUNT = args.parallel
    MODEL_NAME = args.model
    DB_URI = args.mongo_connection_string
    TEMPLATE = args.template
    # extra arguments
    DB_NAME = args.db_name
    REQUESTS_COLLECTION = args.requests_collection
    BATCH_SIZE = args.batch_size
    TIMEOUT = args.timeout
    MIN_LEN = args.min_len
    MAX_LEN = args.max_len

    logging.info(f"Starting with {WORKER_COUNT} workers and batch size of {BATCH_SIZE}...")
    worker_mgr()
    logging.info("Workers finished.")