
import streamlit as st
import os
from dotenv import load_dotenv
from google import genai

# Load API key from the same folder as app.py
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API_KEY = os.getenv("GEMINI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="PyAssist AI",
    page_icon="🤖",
    layout="centered"
)

# Custom styling
st.markdown("""
<style>
.stApp {
    background-color: #f7f8fc;
}
.main-title {
    text-align: center;
    font-size: 38px;
    font-weight: bold;
    color: #4338ca;
}
.subtitle {
    text-align: center;
    color: #64748b;
    margin-bottom: 25px;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">🤖 PyAssist</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Your personal AI assistant powered by Gemini</div>',
    unsafe_allow_html=True
)

if not API_KEY:
    st.error("API key not found. Please check your .env file.")
    st.stop()

# Gemini connection
client = genai.Client(api_key=API_KEY)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.write("Welcome to PyAssist!")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("About PyAssist")
    st.write(
        "PyAssist is an AI chatbot built using Python, "
        "Streamlit and Google's Gemini API."
    )

    st.caption("Built as a Python portfolio project.")

# Suggested prompts
st.subheader("What can I help you with?")

col1, col2 = st.columns(2)

prompt = None

with col1:
    if st.button("🐍 Explain Python", use_container_width=True):
        prompt = "Explain Python in simple words with an example."

    if st.button("💻 Coding Help", use_container_width=True):
        prompt = "Give me beginner-friendly Python coding tips."

with col2:
    if st.button("🤖 What is AI?", use_container_width=True):
        prompt = "Explain Artificial Intelligence with real-life examples."

    if st.button("📚 Interview Preparation", use_container_width=True):
        prompt = "Give me 5 important Python interview questions with answers."

st.divider()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Ask PyAssist anything...")

if user_input:
    prompt = user_input

# Generate response
if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("PyAssist is thinking..."):
            try:
                conversation = [
                    {
                        "role": "user" if m["role"] == "user" else "model",
                        "parts": [{"text": m["content"]}]
                    }
                    for m in st.session_state.messages
                ]

                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=conversation
                )

                answer = response.text or "Sorry, I couldn't generate a response."

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.info("Please try again in a moment.")
