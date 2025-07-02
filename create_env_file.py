import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
import yaml


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
    content = [
        "# project variables",
        f"APP_HOST={args.host}",
        f"APP_PORT={args.port}",
        f"DEBUG={args.debug}",
        "",
        "# project paths",
        "ROOT_DIR=.",
        "SRC_DIR=./src",
        "ALGORITHMS_DIR=./src/algorithms",
        "",
        "# movescu variables",
        f"RECEIVER_AE_TITLE={args.aet}",
        f"RECEIVER_STORE_PORT={args.store_port}",
        "",
        "# email variables",
        f"SENDER_EMAIL_ADDRESS={args.email}",
        f"SENDER_EMAIL_PASSWORD={args.email_pw}",
        "",
        "# algorithm paths"
    ]
    
    algo_paths = append_algorithms(args.algorithms)
    content.extend(algo_paths)

    with open(env_path, 'w', encoding="utf-8") as fenv:
        fenv.write("\n".join(content))
        
    print("created .env file")


def append_algorithms(algorithms: list[str], env_path: Optional[Path] = ".env"):
    if env_path:
        env_path = Path(env_path)
    
    print(f"appending paths for the following algorithms:\n{algorithms}")
    algo_paths = []
    
    if hasattr(args, "algorithms") and args.algorithms:
        for algo in args.algorithms:
            algo_exec_path = input(f"Enter {algo} python executable path: ")
            algo_script_path = input(f"Enter {algo} main .py file path: ")
            
            algo_exec_path = Path(algo_exec_path).expanduser()
            algo_script_path = Path(algo_script_path).expanduser()
            algo_paths.append(f"{algo.upper()}_EXEC_PATH={algo_exec_path}")
            algo_paths.append(f"{algo.upper()}_SCRIPT_PATH={algo_script_path}")
            
    if env_path.exists():
        with open(env_path, 'a', encoding="utf-8") as fenv:
            fenv.write("\n".join(algo_paths))
        
        print(f"appended paths for {len(args.algorithms)} algorithms")
        return
    
    return algo_paths


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    env_path = Path(".env")
    
    if args.new:
        create_env_file(args, env_path)    
    elif args.append:
        if args.algorithms is None:
            parser.error("using --append (-a) option requires --algorithms (-algs)")
            raise RuntimeError
        append_algorithms(args.algorithms, env_path)