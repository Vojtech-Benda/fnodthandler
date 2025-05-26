import sys
import os
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

from src.logger import setup_logger


def main():
    logger = setup_logger()
    
    if not Path(".env").exists():
        logger.fatal(".env file not found in root directory")
        logger.fatal("run create_env.py first and setup environment variables")
        sys.exit(-1)
    
    load_dotenv()
    host = os.getenv("APP_HOST")
    port = int(os.getenv("APP_PORT"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
     

if __name__ == "__main__":
    main()
