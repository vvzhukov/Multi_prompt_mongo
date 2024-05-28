# MongoDB LLM Worker

This script processes multiple  LLM requests from MongoDB in parallel and writes the responses back to MongoDB. It is designed to run multiple workers in parallel with an "at least once" safety guarantee.

## Highlights / Acceptance Criteria

1. **MongoDB Connection**: Establish a connection to MongoDB using `mongo_connection_string`.
2. **Fetch Requests**: Fetch `batch_size` LLM requests from a MongoDB collection.
3. **Process Requests**: Use a language model (default `roneneldan/TinyStories-33M`) to process each request.
4. **Write Responses**: Write the processed responses back to the MongoDB collection, including the batch start processing and completion times.
5. **Parallel Processing**: Process the requests in parallel to improve efficiency.
6. **Multiple Workers**: Ensure multiple workers can run in parallel without interfering with each other.
7. **At Least Once Guarantee**: Ensure that each request is processed at least once.
8. **Logging**: Implement logging for tracking and debugging.
9. **Configuration**: Allow configuration of parameters such as the number of requests to process, MongoDB connection details through arguments or environment variables.
10. **Graceful Shutdown**: Ensure the worker can shut down gracefully.
11. **Timeout Handling**: Implement a timeout for LLM processing.
12. **Template Integration**: Use the specified template `phi3.template` for responses generation.

## Requirements

- Python 3.9+
- libraries `pymongo`, `transformers`, `concurrent`, `os`, `logging`, `agrparse`

## Usage

1. Install the required libraries:
   ```bash
   pip install pymongo transformers
   ``` 
2. Check Mongo DB connection and input data. You may use extra tools:  
   - `db_pymongo_json_gen.py` generate .json file 
   - `db_init_content.json` pre-generated data file 
   - `db_pymongo_init.py` populate data from json to the DB 
     
3. Review script parameters:
   ```bash
   python model_worker.py --help                                                                                                                                            
   usage: model_worker.py [-h] [--parallel PARALLEL] [--model MODEL] [--mongo_connection_string MONGO_CONNECTION_STRING] [--template TEMPLATE] [--db_name DB_NAME] [--requests_collection REQUESTS_COLLECTION] [--batch_size BATCH_SIZE]
                          [--timeout TIMEOUT] [--min_len MIN_LEN] [--max_len MAX_LEN]
   
   Process LLM requests from MongoDB.
   
   optional arguments:
     -h, --help            show this help message and exit
     --parallel PARALLEL   Number of workers
     --model MODEL         Model name
     --mongo_connection_string MONGO_CONNECTION_STRING
                           MongoDB connection string
     --template TEMPLATE   Template name
     --db_name DB_NAME     Database name
     --requests_collection REQUESTS_COLLECTION
                           Requests collection name
     --batch_size BATCH_SIZE
                           Batch size (to feed the workers)
     --timeout TIMEOUT     Worker prompt timeout
     --min_len MIN_LEN     Prompt generation parameters, output min length
     --max_len MAX_LEN     Prompt generation parameters, output max length
   ```
   
4. Set environment variables (optional):
   ```bash
   export DB_URI="mongodb+srv://user:password@cluster0.ycbqnn4.mongodb.net/")
   export DB_NAME="prompt_multiproc"
   export REQUESTS_COLLECTION="mongorequests"
   export BATCH_SIZE=10
   export WORKER_CNT=5
   export TIMEOUT=15
   export MIN_LEN=5
   export MAX_LEN=200
   export MODEL_NAME="roneneldan/TinyStories-33M"
   export TEMPLATE="phi3.template"
   ```


5. Run the script:
   ```bash
   python model_worker.py --parallel 5 --model roneneldan/TinyStories-33M --mongo_connection_string mongodb+srv://user:pwd@cluster0.ycbqnn4.mongodb.net/ --template phi3.template