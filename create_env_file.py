import sys
import os
import argparse
from pathlib import Path
import yaml
from src.process_result import StatusCodes

def get_parser():
    parser = argparse.ArgumentParser(prog="fnodthandler", description="Automatically process DICOM data")
    
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument("-n", "--new", action="store_true", help="Create new .env file")
    command_group.add_argument("-a", "--append", action="store_true", help="Append to existing .env file")
    
    # main arguments for fully creating new .env file
    parser.add_argument("--host", type=str, default="127.0.0.1", help="host address to bind the server to (default: 127.0.0.1 (localhost))")
    parser.add_argument("--port", type=int, default=8000, help="port to run the server on (default: 8000)")
    parser.add_argument("--env", type=str, choices=["dev", "test", "prod"], default="dev", help="environment to run application in (default: dev)")
    parser.add_argument("--debug", action="store_true", help="enable debug mode, eg. uvicorn --reload (default: False)")
    parser.add_argument("--aet", type=str, help="AE title of calling station")
    parser.add_argument("--store-port", type=int, help="port of AET calling station")
    parser.add_argument("--email", type=str, default="fnodthandlerdev@gmail.com", help="email for fnodthandler to send messages from (default: fnodthandlerdev@gmail.com)")
    parser.add_argument("--email-pw", type=str, help="password to fnodthandler's email in quotes (ex. \"email pass word\")")

    # append argument for appending algorithm paths to existing .env file
    parser.add_argument("-algs", "--algorithms", type=str, nargs='+', help="Add algorithm to append paths in .env")
    return parser


def create_env_file(args: argparse.Namespace, env_path):
    content = args.__dict__
    content.pop('append', None)
    content.pop('new', None)
    
    if content['algorithms']:
        
        content['algorithms'] = {
            algo: {
                'exec_path': '',
                'script_path': ''
            } for algo in content['algorithms']
        }
        
        print(f"fill in paths for {len(content['algorithms'])} algorithm keys: {', '.join(content['algorithms'])}")

    with open(env_path, 'w', encoding="utf-8") as fenv:
        yaml.dump(content, fenv, sort_keys=False)
        
    print("created .env file")


def append_algorithms(env_path: Path, algorithms: list[str]):

    with open(env_path, 'r', encoding="utf-8") as fenv:
        content = yaml.safe_load(fenv)
            
    for algo in algorithms:
        content['algorithms'][algo] = {
            'exec_path': '',
            'script_path': '',
        }

    with open(env_path, 'w', encoding="utf-8") as fenv:
        yaml.dump(content, fenv, sort_keys=False)
    
    print(f"fill in paths for {len(algorithms)} appended algorithm keys")


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    env_path = Path(".env.yml")
    
    if args.new:
        create_env_file(args, env_path)
    elif args.append:
        if not env_path.exists():
            raise FileNotFoundError(StatusCodes.FILE_ERROR, f".env file not found at {env_path}")
        if args.algorithms is None:
            parser.error("using --append (-a) option requires --algorithms (-algs)")
            sys.exit(StatusCodes.FILE_ERROR)
        append_algorithms(env_path, args.algorithms)