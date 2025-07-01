# model.py
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Prioritaskan secrets di Streamlit Cloud
API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("🚨 API key not found. Set GROQ_API_KEY in .env or Streamlit secrets.")

client = Groq(api_key=API_KEY)

def ask_model(prompt, model="llama3-70b-8192", temperature=0.1):
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
