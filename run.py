#!/usr/bin/env python3

import sys
import os
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

from src.logger import setup_logger
from src.utils import read_env

def main():
    logger = setup_logger()
    
    env_path = Path(".env.yml")
    if not env_path.exists():
        logger.fatal(".env file not found in root directory")
        logger.fatal("run create_env.py first and setup environment variables")
        sys.exit(-1)
    
    env_vars = read_env()
    # load_dotenv()
    # host = os.getenv("APP_HOST")
    # port = int(os.getenv("APP_PORT"))
    
    host = env_vars['host']
    port= env_vars['port']
    
    uvicorn.run("server:app", host=host, port=port, reload=True)
     

if __name__ == "__main__":
    main()
