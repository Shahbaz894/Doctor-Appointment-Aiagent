import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq  # Correct import for Groq
from logger.logging import logger  # Assuming your logger is set up correctly

load_dotenv()

# Load the GROQ API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set in the environment.")
    raise ValueError("GROQ_API_KEY is not set in the environment.")

# Set the key in the environment
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
logger.info("GROQ_API_KEY loaded successfully.")

class LLMModel:
    def __init__(self, model_name='mixtral-8x7b-32768'):
        if not model_name:
            logger.error("Model name is not defined.")
            raise ValueError("Model name is not defined.")

        self.model_name = model_name
        logger.info(f"Initializing LLM model: {self.model_name}")

        try:
            self.groq_model = ChatGroq(model=self.model_name, api_key=GROQ_API_KEY)
            logger.info(f"Groq model '{self.model_name}' initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize Groq model.")
            raise e
        
    def get_model(self):
        logger.debug("Returning Groq model instance.")
        return self.groq_model
