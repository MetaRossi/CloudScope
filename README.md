# Lambda Labs Availability Monitor

## Overview

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

## Requirements

- Python 3.12 (Although it may work with older versions)
- Pip
- Pipenv

## Setup 

1. **Clone the Repository**
   - Clone the repository to your local machine:
     ```bash
     git clone https://github.com/MetaRossi/LambdaLabsAvailability.git
     ```
2. **Change Directory**
   - Change to the project directory:
     ```bash
     cd LambdaLabsAvailability
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

## Configuration

1. **TOML Configuration File**
   - Create a TOML configuration file in the location of your choosing (e.g., `config.toml`) 
     with the following structure:
     ```toml
     [default]
     api_key = "your_api_key_here"
     sleep_interval_ms = 1000
     log_dir = "__logs"
     ```
   - Adjust the `api_key`, `sleep_interval_ms`, and `log_dir` as per your requirements.
   - Lambda Labs will rate limit requests to the API if polled at less than one request per second.
     If this occurs, you will see HTML in the console output.

2. **Logging Directory**
   - If the logging directory does not exist, it will be created when the application is run.

## Usage

1. **Run the Application**
   - Execute the main script with the configuration file and the namespace:
     ```bash
     python main.py <path to config file> <TOML namespace; 'default' in the example>
     ```
   - The application will start monitoring based on the settings in the specified namespace and log information accordingly.

2. **Monitor Console and Logs**
   - The application logs the status of the instances to both the console and log files.
   - Log files are stored in the directory specified in the configuration file.
   - Log files are named based on the date and time at the start of the application.

3. **Command Line Arguments**
   - `config_file`: Required. Specifies the path to the TOML configuration file.
   - `namespace`: Required. Specifies the namespace within the configuration file.
   - `--help`: Optional. Displays the help message.

## License

MIT license. See the LICENSE file.
