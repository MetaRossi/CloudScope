# 🌐 Cloud Scope
### Lambda Labs Availability Monitor

![Cloud Scope banner](resource/image/CloudScopeBanner.png)

## 📜 Overview

This application monitors the availability of cloud instances using a configurable interval.
It sends requests to the Lambda Labs API to fetch instance availability information.
The application logs the availability information to the console and to log files.

[Lambda Labs](https://lambdalabs.com) is a cloud service that provides access to GPU-enabled cloud instances for 
machine learning and deep learning applications. 
I am not affiliated with Lambda Labs in any way, and this application is not endorsed by Lambda Labs.
As far as I know, Lambda Labs currently provides the lowest cost cloud instances with GPU support.

Lamda Labs API Documentation: https://cloud.lambdalabs.com/api/v1/docs#operation/instanceTypes

Pydantic is used in this application. 
If you are not familiar with Pydantic, the code will look weird.
You can find more information here:
https://pydantic-docs.helpmanual.io/

## 📋 Requirements

- Python 3.12 (Although it may work with older versions)
- Pip
- Pipenv

## 🛠️ Setup 

1. **Clone the Repository**
   - Clone the repository to your local machine:
     ```bash
     git clone https://github.com/MetaRossi/LambdaLabsAvailability.git
     ```
2. **Change Directory**
   - Change to the project directory:
     ```bash
     cd CloudScope
     ```
3. **Install Dependencies Using Pipenv**
   - If missing on your system, install Pipenv:
     ```bash
     pip install pipenv
     ```
   - Install the dependencies using Pipenv:
     ```bash
     pipenv install
     ```
   - Activate the virtual environment:
     ```bash
     pipenv shell
     ```
4. Get a Lambda Labs API Key
   - If you do not already have a Lambda Labs account, create one here: https://lambdalabs.com/
   - Once you have an account, you can get an API key here: https://cloud.lambdalabs.com/api-keys
   - You will need the API key to configure the application.

## ⚙️ Configuration

Create a TOML configuration file in the location of your choosing (e.g., `config.toml`).
Use the following template to configure the application.

I like well annotated configuration files, so I have included comments for each setting.

```toml
# REQUIRED: Namespace for this configuration.
[default]

# REQUIRED: The interval between API requests in milliseconds.
min_poll_delay_ms = 1500
# Lambda Labs will rate limit requests to the API if polled at less than one request per second.
# If this occurs, you will see HTML in the console managers.
# A minimum delay of 1100 ms is required by the application to add a little buffer.
 
# REQUIRED: Directory to store log files.
log_dir = "__logs"
# If the logging directory does not exist, it will be created on start.

# REQUIRED: Lambda Labs API Key
api_key = "your_api_key_here"
 
# OPTIONAL: Enable OS voice notifications for notify, launch, and new region alerts.
#           If absent, disabled by default.
enable_voice_notifications = false
# The OS will say "Instance Available", "Launch In Progress", or "New Region Detected" when an alert occurs.
# A new region will only alert once per application run.
# These alerts only exist because Lambda Labs sometimes adds new regions without notice.
# There is no way to get a list of all regions from the API.
# Currently, the region list is hardcoded in the application.
```

## 🚀 Usage

1. **Run the Application**
   - Execute the main script with required the configuration file and namespace arguments:
     ```bash
     python cloud_scope.py <path_to_config_toml> <toml_namespace_default>
     ```
   - The application will start monitoring based on the settings in the specified namespace 
     and log information accordingly.

2. **Monitor Console and Logs**
   - The application logs the status of the instances to both the console and log files.
   - Log files are stored in the directory specified in the configuration file.
   - Log files are named based on the date and time at the start of the application.

3. **Command Line Arguments**
   - `config_file`: Required. Specifies the path to the TOML configuration file.
   - `namespace`: Required. Specifies the namespace within the configuration file.
   - `--help`: Optional. Displays the help message.

## ⚖️ License

MIT license. See the LICENSE file.

## 🤖 Acknowledgements

This project received assistance from OpenAI's ChatGPT and GitHub Copilot for various tasks including: 
code snippets, unit tests, generating the header image, and documentation.
