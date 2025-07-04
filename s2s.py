import os
import sys
import argparse
import time
import re
import logging
import subprocess
from getpass import getpass
from dotenv import load_dotenv

import splunklib.client as client
import splunklib.binding as binding


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_credentials():
    load_dotenv() # Load environment variables from .env file
    username = os.getenv("SPLUNK_USER")
    password = os.getenv("SPLUNK_PASS")

    if not username:
        username = input("Enter Splunk username: ")
    if not password:
        password = getpass("Enter Splunk password: ")
    return username, password

def validate_cron(timer):
    parts = timer.strip().split()
    if len(parts) != 5:
        raise argparse.ArgumentTypeError("Cron timer must have exactly 5 fields (e.g. '*/30 * * * *')")
    cron_pattern = re.compile(r'^(\*|\d+|\*/\d+|\d+(,\d+)*|\d+-\d+)$')

    for part in parts:
        if not cron_pattern.match(part):
            raise argparse.ArgumentTypeError(f"Invalid cron field: '{part}'")
    return timer

def validate_host_port(host_string):
    parts = host_string.split(':', 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Host must be in the format IP:Port (e.g., '127.0.0.1:8089').")
    ip, port_str = parts
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise argparse.ArgumentTypeError(f"Port number '{port_str}' is out of valid range (1-65535).")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Port number '{port_str}' is not a valid integer.")
    return host_string # Return the original string if valid

def connect_to_splunk(host, username, password):
    host, port = host.split(':', 1)
    try:
        service = client.connect(
            host=host,
            port=port,
            username=username,
            password=password
        )
        logging.info("Successfully connected to Splunk.")
        return service
    except (ConnectionRefusedError, TimeoutError) as e:
        logging.error(f"Connection to Splunk failed: {e}")
        sys.exit(1)
    except binding.AuthenticationError:
        logging.error("Authentication failed. Please check your credentials.")
        sys.exit(1)

def convert_sigma_to_splunk(rule_path, pipeline):
    command = ["sigma", "convert", "-t", "splunk", "-f", "default", rule_path]
    if pipeline != "--without-pipeline":
        command.extend(["-p", pipeline])
    command.append("--without-pipeline")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(f"Generated Splunk query: {result.stdout.strip()}")
        return result.stdout.strip()
    except FileNotFoundError:
        logging.error("The 'sigma' command was not found. Please ensure it's installed and in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        logging.error(f"Sigma conversion failed: {e.stderr}")
        sys.exit(1)

def create_scheduled_search(service, search_name, query, timer):
    search_query = f'search {query}'
    try:
        saved_search = service.saved_searches.create(
            name=search_name,
            search=search_query,
            cron_schedule=timer,
            is_scheduled=True,
            description="This is a scheduled search created by Sigma2Splunk Python script."
        )
        logging.info(f"Saved search '{saved_search.name}' created successfully.")
        return search_query
    except binding.HTTPError as e:
        if e.status == 409:
            logging.error(f"A saved search with the name '{search_name}' already exists.")
        else:
            logging.error(f"Failed to create saved search: {e}")
        sys.exit(1)

def delete_saved_search(service, search_name):
    try:
        service.saved_searches.delete(search_name)
        logging.info(f"Saved search '{search_name}' deleted successfully.")
    except KeyError:
        logging.error(f"Saved search '{search_name}' not found.")
        sys.exit(1)

def execute_search(service, query):
    job = service.jobs.create(query)
    logging.info("Search job created. Waiting for results...")

    while not job.is_ready():
        time.sleep(2)

    stats = {
        "isDone": job["isDone"],
        "doneProgress": float(job["doneProgress"]) * 100,
        "scanCount": int(job["scanCount"]),
        "eventCount": int(job["eventCount"]),
        "resultCount": int(job["resultCount"]),
    }

    logging.info(
        f"{stats['doneProgress']:.1f}% done | "
        f"{stats['scanCount']} scanned | "
        f"{stats['eventCount']} matched | "
        f"{stats['resultCount']} results"
    )

    if stats["isDone"] == "1":
        logging.info("Search completed.")

def main():
    parser = argparse.ArgumentParser(description='A script to convert Sigma rules to Splunk saved searches.')
    parser.add_argument('-n', '--name', required=True, help='Name of the saved search.')
    parser.add_argument(
        '--host',
        type=validate_host_port,
        default='127.0.0.1:8089',
        help='Splunk API host and port (default: 127.0.0.1:8089).'
    )
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-r', '--rule', help='Path to the Sigma rule file (.yml).')
    action_group.add_argument('-d', '--delete', action='store_true', help='Delete a saved search.')
    parser.add_argument('-t', '--timer', type=validate_cron, default='*/30 * * * *', help='Cron timer for the saved search (default: "*/30 * * * *").')
    parser.add_argument('-p', '--pipeline', default='--without-pipeline', help='Sigma-cli pipeline (default: --without-pipeline).')
    args = parser.parse_args()

    username, password = get_credentials()
    service = connect_to_splunk(args.host, username, password)
    if args.delete:
        delete_saved_search(service, args.name)
    elif args.rule:
        splunk_query = convert_sigma_to_splunk(args.rule, args.pipeline)
        search_query = create_scheduled_search(service, args.name, splunk_query, args.timer)
        execute_search(service, search_query)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user.")
        sys.exit(1)