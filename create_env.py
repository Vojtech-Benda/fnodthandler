import os
import argparse
from dotenv import load_dotenv

parser = argparse.ArgumentParser(prog="fnodthandler", 
                                 description="automatically process DICOM data")

parser.add_argument("--host", type=str, default="127.0.0.1", help="host address to bind the server to (default: 127.0.0.1 (localhost))")
parser.add_argument("--port", type=int, default=8000, help="port to run the server on (default: 8000)")
parser.add_argument("--env", type=str, choices=["dev", "test", "prod"], default="dev", help="environment to run application in (default: dev)")
parser.add_argument("--debug", action="store_true", help="enable debug mode, eg. uvicorn --reload (default: False)")
parser.add_argument("--aet", type=str, required=True, help="AE title of calling station")
parser.add_argument("--store-port", type=int, required=True, help="port of AET calling station")
parser.add_argument("--email", type=str, default="fnodthandlerdev@gmail.com", help="email for fnodthandler to send messages from (default: fnodthandlerdev@gmail.com)")
parser.add_argument("--email-pw", type=str, required=True, help="password to fnodthandler's email in quotes (ex. \"email pass word\")")
args = parser.parse_args()

with open(".env", "w", encoding="utf-8") as fenv:
    content = f"""
# project variables
APP_HOST={args.host}
APP_PORT={args.port}
DEBUG={args.debug}

# project paths
ROOT_DIR =.
SRC_DIR =./src
ALGORITHMS_DIR =./src/algorithms

# movescu variables
RECEIVER_AE_TITLE={args.aet}
RECEIVER_STORE_PORT={args.store_port}

# email variables
SENDER_EMAIL_ADDRESS={args.email}
SENDER_EMAIL_PASSWORD={args.email_pw}
"""
    
    fenv.write(content)
    print(f"created .env in root directory")

env_vars = ["RECEIVER_AE_TITLE", "RECEIVER_STORE_PORT", "SENDER_EMAIL_PASSWORD"]

# sanity check all required env variables have values
load_dotenv()
missing_vars = [var for var in env_vars if not os.getenv(var)]

if missing_vars:
    print(f"environment variables without values: {', '.join(missing_vars)}")
