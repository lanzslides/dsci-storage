# DE LEON, Ivan Yuri
# FERMIN, Lanz Railey
# TAGULAO, Rafael Ma. Vicente

import streamlit as st
import os
import multiprocessing
import time
from llama_cpp import Llama

st.set_page_config(layout = 'wide')

# Token variables
max_input = 4096
max_output = 256

# Silence errors
os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"
os.environ["LLAMA_SET_ROWS"] = "1"

NUM_THREADS = multiprocessing.cpu_count() 

# Load Deepseek
# Need st.cache_resource (https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_resource)
@st.cache_resource
def load_llm():
    return Llama(
        model_path="deepseek-llm-7b-chat.Q4_K_M.gguf",
        n_ctx=max_input,
        n_threads=NUM_THREADS,
        use_mlock=True,
        n_batch=max_output,
        verbose=False
    )

llm = load_llm()

# Token counter
def count_tokens(text: str) -> int:
    return len(llm.tokenize(text.encode("utf-8")))

# Format full memory conversation
def build_prompt(history):
    prompt = "<|system|>\nYou are R-LLM, or Rafa-Lanz-Lion Model, helpful assistant.\n"
    for user_msg, assistant_msg in history:
        prompt += f"<|user|>\n{user_msg.strip()}\n<|assistant|>\n{assistant_msg.strip()}\n"
    return prompt

# Wrapper
st.title("Welcome to R-LLM.")
st.subheader("I am R-LLM, a Really Little Language Model. I *hope* I can help you today..." )

# Initialize
if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "token_stats" not in st.session_state:
    st.session_state.token_stats = {
        "prompt_tokens": 0,
        "response_tokens": 0,
        "context_tokens": 0,
        "total_tokens": 0,
        "speed": 0.0,
        "time": 0.0,
    }

# Define token_history for viz
if "token_history" not in st.session_state:
    st.session_state.token_history = [] 

col_chat, col_stats = st.columns([3,1])

with col_chat:

    chat_history = st.container(height=500, border=True)
    with chat_history:
        for user_msg, assistant_msg in st.session_state.conversation:
            # This answers 4.2
            with st.chat_message("user"):
                st.markdown(user_msg)
            with st.chat_message("assistant"):
                st.markdown(assistant_msg)

    user_input = st.chat_input("Type your message here.")
    if user_input:
        with chat_history:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("...")

        st.session_state.conversation.append((user_input, ""))
        
        # Adding build_prompt() here addresses 4.1
        # Build context prompt (history only)
        context_prompt = build_prompt(st.session_state.conversation[:-1])
        context_tokens = count_tokens(context_prompt)

        # Prompt is full input to model
        prompt = context_prompt + f"<|user|>\n{user_input}\n<|assistant|>\n"

        # Individual token counts
        prompt_tokens = count_tokens(f"<|user|>\n{user_input}\n<|assistant|>\n")

        start = time.time()
        output = llm(prompt, max_tokens=256, stop=["<|user|>", "</s>"])
        response = output["choices"][0]["text"].strip()
        response_tokens = count_tokens(response)
        end = time.time()

        message_placeholder.markdown(response)
        st.session_state.conversation[-1] = (user_input, response)
        
        st.session_state.token_stats["prompt_tokens"] = prompt_tokens
        st.session_state.token_stats["response_tokens"] = response_tokens
        st.session_state.token_stats["context_tokens"] = context_tokens
        st.session_state.token_stats["total_tokens"] = prompt_tokens + response_tokens + context_tokens
        st.session_state.token_stats["time"] = end - start
        st.session_state.token_stats["speed"] = response_tokens / (end - start + 1e-6)
    
with col_stats:
    st.subheader("Model Details")

    col1, col2 = st.columns(2)

    with col1:
        st.caption("Token Count")
        st.metric("Input Tokens", st.session_state.token_stats["prompt_tokens"])
        st.metric("Response Tokens", st.session_state.token_stats["response_tokens"])
        st.metric("Context Tokens", st.session_state.token_stats["context_tokens"])

    with col2:
        st.caption("Model Performance")
        st.text(f"Time: {st.session_state.token_stats['time']:.2f} sec")
        st.text(f"Speed: {st.session_state.token_stats['speed']:.2f} tokens/sec")

    # This is for 4.4
    st.divider()
    st.subheader("Model Token Quota")

    progress_num = min(st.session_state.token_stats["total_tokens"] / max_input, 1.0)
    progress_pct = int(progress_num * 100)

    st.progress(progress_num,
    text=f"{st.session_state.token_stats['total_tokens']} / {max_input} tokens — {progress_pct}%"
)
    if st.session_state.token_stats["total_tokens"] >= max_input:
        st.error("⚠️ WARNING: You’ve reached the token quota! The next prompt may cause a ValueError.")
        if st.button("🔁 Start Over"):
            # Clear all session state variables
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    if user_input:
        st.session_state.token_history.append(prompt_tokens + response_tokens)
    
    st.divider()
    st.subheader("Current Token Usage")
    st.line_chart(st.session_state.token_history, use_container_width=True)
