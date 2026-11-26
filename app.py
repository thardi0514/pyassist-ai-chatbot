
import streamlit as st
import os
import sqlite3
from contextlib import closing
from dotenv import load_dotenv
from google import genai

# --------------------------------
# 1. ENVIRONMENT CONFIGURATION
# --------------------------------

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API_KEY = os.getenv("GEMINI_API_KEY")

DB_PATH = os.path.join(os.path.dirname(__file__), "pyassist.db")

MODEL_NAME = "gemini-3.1-flash-lite"

# --------------------------------
# 2. DATABASE CONNECTION
# --------------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --------------------------------
# 3. CREATE DATABASE TABLES
# --------------------------------

def init_db():

    with closing(get_connection()) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
            )
        """)

        conn.commit()


# --------------------------------
# 4. CREATE NEW CONVERSATION
# --------------------------------

def create_conversation():

    with closing(get_connection()) as conn:

        cursor = conn.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            ("New Chat",)
        )

        conn.commit()

        return cursor.lastrowid


# --------------------------------
# 5. SAVE MESSAGE
# --------------------------------

def save_message(conversation_id, role, content):

    with closing(get_connection()) as conn:

        conn.execute("""
            INSERT INTO messages
            (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, content))

        # Set conversation title from first user message
        if role == "user":

            conn.execute("""
                UPDATE conversations
                SET title = CASE
                    WHEN title = 'New Chat' THEN ?
                    ELSE title
                END,
                updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (content[:45], conversation_id))

        conn.execute("""
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (conversation_id,))

        conn.commit()


# --------------------------------
# 6. FETCH CONVERSATIONS
# --------------------------------

def get_conversations():

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT id, title
            FROM conversations
            ORDER BY updated_at DESC
        """).fetchall()


# --------------------------------
# 7. FETCH MESSAGES
# --------------------------------

def get_messages(conversation_id):

    with closing(get_connection()) as conn:

        return conn.execute("""
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """, (conversation_id,)).fetchall()


# --------------------------------
# 8. DELETE CONVERSATION
# --------------------------------

def delete_conversation(conversation_id):

    with closing(get_connection()) as conn:

        conn.execute("""
            DELETE FROM conversations
            WHERE id = ?
        """, (conversation_id,))

        conn.commit()


# --------------------------------
# 9. INITIALIZE APPLICATION
# --------------------------------

st.set_page_config(
    page_title="PyAssist AI",
    page_icon="🤖",
    layout="centered"
)

init_db()

if "current_chat_id" not in st.session_state:

    chats = get_conversations()

    if chats:
        st.session_state.current_chat_id = chats[0][0]
    else:
        st.session_state.current_chat_id = create_conversation()


# --------------------------------
# 10. CUSTOM STYLING
# --------------------------------

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


# --------------------------------
# 11. HEADER
# --------------------------------

st.markdown(
    '<div class="main-title">🤖 PyAssist</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Your personal AI assistant powered by Gemini</div>',
    unsafe_allow_html=True
)


# --------------------------------
# 12. API VALIDATION
# --------------------------------

if not API_KEY:
    st.error("API key not found. Please check your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)


# --------------------------------
# 13. SIDEBAR
# --------------------------------

with st.sidebar:

    st.title("⚙️ Settings")

    st.write("Welcome to PyAssist!")

    # Create new conversation
    if st.button("➕ New Chat", use_container_width=True):

        st.session_state.current_chat_id = create_conversation()
        st.rerun()

    st.divider()

    st.subheader("💬 Chat History")

    chats = get_conversations()

    for chat_id, chat_title in chats:

        button_label = (
            f"📌 {chat_title}"
            if chat_id == st.session_state.current_chat_id
            else chat_title
        )

        if st.button(
            button_label,
            key=f"chat_{chat_id}",
            use_container_width=True
        ):

            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.divider()

    # Delete selected conversation
    if st.button("🗑️ Delete Current Chat", use_container_width=True):

        delete_conversation(st.session_state.current_chat_id)

        remaining_chats = get_conversations()

        if remaining_chats:
            st.session_state.current_chat_id = remaining_chats[0][0]
        else:
            st.session_state.current_chat_id = create_conversation()

        st.rerun()

    st.divider()

    st.subheader("About PyAssist")

    st.write(
        "PyAssist is an AI chatbot built using Python, "
        "Streamlit and Google's Gemini API."
    )

    st.caption("Built as a Python portfolio project.")


# --------------------------------
# 14. SUGGESTED PROMPTS
# --------------------------------

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


# --------------------------------
# 15. LOAD AND DISPLAY CHAT HISTORY
# --------------------------------

current_chat_id = st.session_state.current_chat_id

messages = get_messages(current_chat_id)

for role, content in messages:

    with st.chat_message(role):
        st.markdown(content)


# --------------------------------
# 16. CHAT INPUT
# --------------------------------

user_input = st.chat_input("Ask PyAssist anything...")

if user_input:
    prompt = user_input


# --------------------------------
# 17. GENERATE GEMINI RESPONSE
# --------------------------------

if prompt:

    # Save user message permanently
    save_message(current_chat_id, "user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    # Get complete conversation from SQLite
    stored_messages = get_messages(current_chat_id)

    conversation = [
        {
            "role": "user" if role == "user" else "model",
            "parts": [{"text": content}]
        }
        for role, content in stored_messages
    ]

    with st.chat_message("assistant"):

        with st.spinner("PyAssist is thinking..."):

            try:

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=conversation
                )

                answer = (
                    response.text
                    or "Sorry, I couldn't generate a response."
                )

                st.markdown(answer)

                # Save AI response permanently
                save_message(
                    current_chat_id,
                    "assistant",
                    answer
                )

            except Exception:
                st.error(
                    "Something went wrong while connecting to Gemini."
                )

                st.info("Please try again in a moment.")
