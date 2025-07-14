#!/usr/bin/env python3

import sys
import uvicorn
from pathlib import Path

# from src.logger import setup_logger
import logging
from src.utils import read_env

logger = logging.getLogger("uvicorn")

def main():
    # logger = setup_logger()
    
    env_path = Path(".env.yml")
    if not env_path.exists():
        logger.error(f"{env_path} not found in root directory")
        logger.error("run create_env.py first and setup environment variables")
        sys.exit(-1)
    
    env_vars = read_env()
    
    host = env_vars['host']
    port = env_vars['port']
    
    uvicorn.run("server:app", host=host, port=port, reload=True)
     

if __name__ == "__main__":
    main()
