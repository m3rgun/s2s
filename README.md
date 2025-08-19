
# Sigma2Splunk

Sigma2Splunk is a Python script that converts Sigma rules into Splunk searches and creates scheduled searches in a Splunk instance. It simplifies the process of integrating Sigma rules for threat detection into your Splunk environment.

## Features

- **Sigma to Splunk Conversion:** Converts Sigma rules (in .yml format) into Splunk Processing Language (SPL) queries.
- **Scheduled Search Creation:** Creates scheduled searches in Splunk based on the converted queries.
- **Customizable Scheduling:** Allows you to specify a cron schedule for the created searches.
- **Search Deletion:** Provides an option to delete existing saved searches.
- **Direct Search Execution:** Executes the generated Splunk query and displays the results.

## Prerequisites

Before using Sigma2Splunk, ensure you have the following installed:

- [Python 3.x](https://www.python.org/downloads/)
- The [sigma-cli](https://github.com/SigmaHQ/sigma-cli) tool and [splunk-sdk](https://github.com/splunk/splunk-sdk-python).

- The required Python libraries, which can be installed from the `requirements.txt` file:
  ```bash
  pip install -r requirements.txt
  ```

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/m3rgun/s2s.git
   cd s2s
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install splunk backend plugin:**
   ```bash
   sigma plugin install splunk
   ```

4. **(Optional) Install sysmon pipeline plugin:**
   ```bash
   sigma plugin install sysmon
   ```

5. **(Optional) Create a `.env` file:**
   For ease of use, you can create a `.env` file in the project's root directory to store your Splunk credentials. This avoids having to enter them every time you run the script.

   ```
   SPLUNK_USER=your_splunk_username
   SPLUNK_PASS=your_splunk_password
   ```

   **Note:** If you don't create a `.env` file, the script will prompt you to enter your credentials.

## Usage

### Creating a Scheduled Search

To convert a Sigma rule and create a scheduled search in Splunk, use the following command:

```bash
python s2s.py -n <search_name> -r <path_to_sigma_rule.yml> [options]
```

**Arguments:**

- `-n`, `--name`: (Required) The name of the saved search to be created in Splunk.
- `-r`, `--rule`: (Required) The path to the Sigma rule file (.yml) you want to convert.

**Options:**

- `--host`: The Splunk API host and port (default: `127.0.0.1:8089`).
- `-t`, `--timer`: The cron timer for the scheduled search (default: `*/30 * * * *`).
- `-p`, `--pipeline`: The `sigma-cli` pipeline to use for conversion (default: `--without-pipeline`).

**Example-1:** Default case.

```bash
python s2s.py -n "Suspicious Certutil Download" -r sigmarules/proc_creation_win_certutil_download.yml
```

**Example-2:** Using host and timer options.
```bash
python s2s.py -n "Suspicious Certutil Download" -r sigmarules/proc_creation_win_certutil_download.yml --host "192.168.1.100:8089" -t "*/5 * * * *"
``` 

**Example-3:** Using a pipeline. To show all available pipelines , `sigma list pipelines`.
```bash
python s2s.py -n "Suspicious Certutil Download" -r sigmarules/proc_creation_win_certutil_download.yml -p splunk_windows
```

### Deleting a Saved Search

To delete a saved search from Splunk, use the `-d` or `--delete` flag:

```bash
python s2s.py -d -n <search_name>
```




**Example:**

```bash
python s2s.py -d -n "Suspicious Certutil Download"
```

This command will delete the saved search named "Suspicious Certutil Download" from your Splunk instance.


## Sigma Rules

This project does not include any sigma rules. You can test the functionality with your own rules, or you can check [SigmaHQ](https://github.com/SigmaHQ/sigma/tree/master/rules) rules page.

