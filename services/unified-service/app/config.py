import os
from dotenv import load_dotenv
load_dotenv()

STT_MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "small")
STT_DEVICE = os.getenv("STT_DEVICE", "auto")
STT_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))

# NEW:
PRODUCT_FINDER_URL = os.getenv("PRODUCT_FINDER_URL", "http://localhost:8003")
