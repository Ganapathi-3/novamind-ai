import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-insecure-default')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('TOKEN_EXPIRE_MINUTES', '480'))
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
VECTOR_STORE_PATH = os.getenv('VECTOR_STORE_PATH', str(Path(__file__).parent.parent / 'vector_store'))
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '4'))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./enterprise_ai.db')
UPLOAD_DIR = os.getenv('UPLOAD_DIR', str(Path(__file__).parent.parent / 'data' / 'documents'))