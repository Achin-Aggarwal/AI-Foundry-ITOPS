# llm_connector.py
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Ensure Groq API Key is available
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("⚠️ Missing GROQ_API_KEY. Please set it in your environment or .env file.")

# Initialize Groq LLM
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",  # You can switch to another model if needed
    temperature=0.7
)

# Create prompt templates
general_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant."),
    ("user", "{input}")
])

cs_it_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a specialized CS/IT expert assistant. You have deep knowledge in:
    - Programming languages (Python, Java, JavaScript, C++, etc.)
    - Algorithms and data structures
    - Database design and management
    - System design and architecture
    - Software engineering principles
    - Web development (frontend/backend)
    - DevOps and cloud technologies
    - Cybersecurity
    - Machine learning and AI
    - Operating systems and networking
    
    Provide detailed, accurate, and practical answers. Include code examples when relevant.
    Use clear explanations that are educational and helpful for learning."""),
    ("user", "{input}")
])

# Create chains
general_chain = general_prompt | llm
cs_it_chain = cs_it_prompt | llm


def get_llm_response(user_input: str) -> str:
    """
    Send user input to Groq LLM and return the generated response for general queries.
    """
    try:
        result = general_chain.invoke({"input": user_input})
        return result.content
    except Exception as e:
        return f"⚠️ Error while generating response: {e}"


def get_cs_it_response(user_input: str) -> str:
    """
    Send user input to Groq LLM with specialized CS/IT context and return the response.
    """
    try:
        result = cs_it_chain.invoke({"input": user_input})
        return result.content
    except Exception as e:
        return f"⚠️ Error while generating CS/IT response: {e}"