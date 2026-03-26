import streamlit as st
from langgraph_database_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# *********************** utility functions ***********************

def generate_thread_id():
    thread_id = str(uuid.uuid4())
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    st.session_state['chat_threads'].append({
            "thread_id": thread_id,
            "name": None
        })

def load_conversation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )

    if state and 'messages' in state.values:
        return state.values['messages']
    
    return []

# *********************** session setup ***********************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

if not any(
    thread['thread_id'] == st.session_state['thread_id']
    for thread in st.session_state['chat_threads']
) : 
    add_thread(st.session_state['thread_id'])



# *********************** sidebar ui ***********************

st.sidebar.title('Langgraph Chatbot')
if st.sidebar.button('New chat'):
    reset_chat()

st.sidebar.header("my conversations")

for thread in st.session_state['chat_threads']:


    label = thread["name"] if thread["name"] else f"Chat {thread['thread_id'][:4]}"
    if st.sidebar.button(label, key=thread["thread_id"]):
        st.session_state['thread_id'] = thread["thread_id"]
        messages = load_conversation(thread["thread_id"])

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role= 'user'
            else: 
                role= 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        
        st.session_state['message_history'] = temp_messages


# *********************** find current thread ***********************

current_thread = None

for thread in st.session_state['chat_threads']:
    if thread["thread_id"] == st.session_state['thread_id']:
        current_thread = thread
        break


# *********************** main ui ***********************


# load the conversation history

for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.write(message['content'])

user_input = st.chat_input(" type here :) ")

if user_input: 
    rename_flag = False

    if current_thread and not current_thread["name"]:
        current_thread["name"] = user_input.strip().capitalize()[:30]
        st.session_state['chat_threads'] = [
    t if t["thread_id"] != current_thread["thread_id"]
    else {
        "thread_id": current_thread["thread_id"],
        "name": user_input.strip().capitalize()[:30]
    }
    for t in st.session_state['chat_threads']
]
        rename_flag = True

    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('assistant'):
        def stream_gen():
            for chunk, _ in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                if chunk.content:
                    yield chunk.content

        ai_message = st.write_stream(stream_gen())

    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })

