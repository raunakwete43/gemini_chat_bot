import json
import os
import time

import google.generativeai as genai
import joblib
import streamlit as st

from chat_history import chat_history

st.set_page_config(
    page_title="Gemini ChatBOT",
    page_icon="./images/chat.png",
    layout="wide",
    initial_sidebar_state="auto",
)


def get_api_key() -> str:
    # Load API key from the config file
    with open("./key.json", "r") as config_file:
        config_data = json.load(config_file)

    api_key = config_data.get("api_key")

    if api_key is None:
        return None

    return api_key


security_settings = {
    "HARM_CATEGORY_HARASSMENT": "block_none",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "block_none",
    "HARM_CATEGORY_HATE_SPEECH": "block_none",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "block_none",
}


GOOGLE_API_KEY = get_api_key()
genai.configure(api_key=GOOGLE_API_KEY)


def get_chat_id():
    current_time = time.time()
    local_time = time.localtime(current_time)
    formatted_time = time.strftime("%a %b %d %y %I:%M %p", local_time)
    return formatted_time


new_chat_id = f"{get_chat_id()}"
MODEL_ROLE = "ai"
AI_AVATAR_ICON = "✨"

# Create a data/ folder if it doesn't already exist
try:
    os.mkdir("./data/")
except:
    # data/ folder already exists
    pass

# Load past chats (if available)
try:
    past_chats: dict = joblib.load("./data/past_chats_list")
except:
    past_chats = {}

with st.sidebar:
    uploaded_file = st.file_uploader("Upload Custom Chat History (JSON)", type=["json"])

    # Check if a file is uploaded
    if uploaded_file is not None:
        custom_chat_history = json.load(uploaded_file)
        st.success("Custom chat history uploaded successfully!")
    else:
        custom_chat_history = None


# Past Chats sidebar
with st.sidebar:
    st.write("# Past Chats")
    if st.session_state.get("chat_id") is None:
        st.session_state.chat_id = st.selectbox(
            label="Pick a past chat",
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, "New Chat"),
            placeholder="_",
        )
    else:
        # This will happen the first time AI response comes in
        st.session_state.chat_id = st.selectbox(
            label="Pick a past chat",
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(
                x,
                "New Chat"
                if x != st.session_state.chat_id
                else st.session_state.chat_title,
            ),
            placeholder="_",
        )
    # Save new chats after a message has been sent to AI
    # TODO: Give user a chance to name chat
    st.session_state.chat_title = f"Chat {st.session_state.chat_id}"

    # Add a button to delete the current chat
    if st.button("Delete Current Chat"):
        # Delete the chat history files
        os.remove(f"data/{st.session_state.chat_id}-st_messages")
        os.remove(f"data/{st.session_state.chat_id}-gemini_messages")

        # Remove the chat from the list of past chats
        del past_chats[st.session_state.chat_id]

        # Save the updated list of past chats
        joblib.dump(past_chats, "data/past_chats_list")

        # Reset the current chat ID
        st.session_state.chat_id = None

        # Reload the page to refresh the sidebar
        st.experimental_rerun()

st.write("## Chat with Gemini with the least safety options")


def display_chat_history_on_sidebar(chat_history):
    st.sidebar.markdown("## Chat History")

    for idx, message in enumerate(chat_history):
        role = message["role"]
        text = message["parts"][0]["text"]

        # Style the messages based on the role (user or model)
        if role == "user":
            st.sidebar.markdown(f"**User:** {text}")
        elif role == "model":
            st.sidebar.markdown(f"**AI Model:** {text}")

        # Add a separator between messages
        if idx < len(chat_history) - 1:
            st.sidebar.markdown("---")


# Chat history (allows to ask multiple questions)
# try:
#     st.session_state.messages = joblib.load(
#         f"data/{st.session_state.chat_id}-st_messages"
#     )
#     st.session_state.gemini_history = joblib.load(
#         f"data/{st.session_state.chat_id}-gemini_messages"
#     )
#     print("old cache")
# except:
#     st.session_state.messages = []
#     st.session_state.gemini_history = chat_history
#     print("new_cache made")

# st.write(custom_chat_history)

# Chat history (allows to ask multiple questions)
try:
    if custom_chat_history is not None:
        st.session_state.gemini_history = custom_chat_history
    else:
        st.session_state.messages = joblib.load(
            f"data/{st.session_state.chat_id}-st_messages"
        )
    st.session_state.gemini_history = joblib.load(
        f"data/{st.session_state.chat_id}-gemini_messages"
    )
    print("old cache")
except:
    st.session_state.messages = []
    st.session_state.gemini_history = custom_chat_history
    print("new_cache made")

st.session_state.model = genai.GenerativeModel(
    "gemini-pro", safety_settings=security_settings
)
st.session_state.chat = st.session_state.model.start_chat(
    history=st.session_state.gemini_history,
)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(
        name=message["role"],
        avatar=message.get("avatar"),
    ):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Your message here..."):
    # Save this as a chat for later
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, "data/past_chats_list")
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append(
        dict(
            role="user",
            content=prompt,
        )
    )
    ## Send message to AI
    response = st.session_state.chat.send_message(
        prompt,
        stream=True,
    )
    # Display assistant response in chat message container
    with st.chat_message(
        name=MODEL_ROLE,
        avatar=AI_AVATAR_ICON,
    ):
        message_placeholder = st.empty()
        full_response = ""
        assistant_response = response
        # Streams in a chunk at a time
        for chunk in response:
            # Simulate stream of chunk
            # TODO: Chunk missing `text` if API stops mid-stream ("safety"?)
            for ch in chunk.text.split(" "):
                full_response += ch + " "
                time.sleep(0.05)
                # Rewrites with a cursor at end
                message_placeholder.write(full_response + "▌")
        # Write full message with placeholder
        message_placeholder.write(full_response)

    # Add assistant response to chat history
    st.session_state.messages.append(
        dict(
            role=MODEL_ROLE,
            content=st.session_state.chat.history[-1].parts[0].text,
            avatar=AI_AVATAR_ICON,
        )
    )
    st.session_state.gemini_history = st.session_state.chat.history
    # Save to file
    joblib.dump(
        st.session_state.messages,
        f"data/{st.session_state.chat_id}-st_messages",
    )
    joblib.dump(
        st.session_state.gemini_history,
        f"data/{st.session_state.chat_id}-gemini_messages",
    )

with st.sidebar:
    st.write(st.session_state.gemini_history)
