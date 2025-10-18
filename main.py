from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import DoctorAppointmentAgent
from langchain_core.messages import HumanMessage, BaseMessage
import os
from logger.logging import logger  # Make sure this is properly configured

# Remove SSL certificate file if set
os.environ.pop("SSL_CERT_FILE", None)

app = FastAPI()

class UserQuery(BaseModel):
    id_number: str
    message: str

# Initialize the agent once at startup
try:
    agent = DoctorAppointmentAgent()
    logger.info("Doctor appointment agent initialized successfully.")
except Exception as e:
    logger.critical(f"Failed to initialize agent: {e}")
    raise RuntimeError("Agent initialization failed. Check dependencies and configuration.")

@app.post("/execute")
def execute_agent(user_input: UserQuery):
    try:
        # Log incoming request
        logger.info(f"Received request with ID Number: {user_input.id_number}")
        logger.debug(f"User Message: {user_input.message}")

        # Get the agent workflow
        try:
            app_graph = agent.workflow()
        except Exception as wf_error:
            logger.error(f"Error creating agent workflow: {wf_error}", exc_info=True)
            raise HTTPException(status_code=500, detail="Agent workflow could not be initialized.")

        # Prepare input message
        input_message = [HumanMessage(content=user_input.message)]

        query_data = {
            "messages": input_message,
            "id_number": user_input.id_number,
            "next": "",
            "query": user_input.message,
            "current_reasoning": [],
        }

        # Run the agent
        response = app_graph.invoke(query_data, config={"recursion_limit": 20})

        # Convert BaseMessage objects to strings for JSON serialization
        serialized_messages = [
            msg.content if isinstance(msg, BaseMessage) else str(msg)
            for msg in response.get("messages", [])
        ]

        # Log successful response
        logger.info(f"Successfully processed request for ID: {user_input.id_number}")
        logger.debug(f"Serialized Agent Response: {serialized_messages}")

        return {"messages": serialized_messages}

    except Exception as e:
        logger.error(f"Unhandled exception in execute_agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
def health_check():
    """Health check endpoint to verify server status."""
    return {"status": "healthy"}