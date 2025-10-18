import streamlit as st
import requests
from logger.logging import logger  # Ensure this is configured properly


# Configure logging if not already done


API_URL = "http://127.0.0.1:8000/execute"

st.set_page_config(page_title="🩺 Doctor Appointment System", layout="centered")

st.title("🩺 Doctor Appointment System")
st.markdown("Use this interface to interact with the doctor appointment assistant.")

user_id = st.text_input("Enter your ID number:", "")
query = st.text_area("Enter your query:", "Can you check if a dentist is available tomorrow at 10 AM?")

if st.button("Submit Query"):
    if user_id and query:
        try:
            logger.info(f"Sending request to API: {API_URL}")
            logger.debug(f"User ID: {user_id}, Query: {query}")

            payload = {
                "id_number": user_id.strip(),  # Send as string per FastAPI model
                "message": query.strip()
            }

            response = requests.post(
                API_URL,
                json=payload,
                verify=False  # Only for dev; use proper certs in prod
            )

            if response.status_code == 200:
                logger.info("Successfully received response from API.")
                data = response.json()
                logger.debug(f"API Response: {data}")

                st.success("Assistant Response:")
                st.write(data.get("messages", "No message in response"))
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                st.error(error_msg)

        except Exception as e:
            logger.exception("Exception occurred during API call.")
            st.error(f"An exception occurred: {str(e)}")
    else:
        logger.warning("Missing input fields.")
        st.warning("Please enter both an ID number and your query.")