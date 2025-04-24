import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from serpapi import GoogleSearch


# ✅ Set your keys here
openai.api_key="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"
SERP_API_KEY = "b29a8a610c6d564e92178262992e734a803221e4d0e33b898bdaea2a13b378da"

# --- Query Analyzer ---
def analyze_query(user_query):
    prompt = f"""Improve the following research query for accurate web results:\n\nOriginal: "{user_query}"\n\nImproved:"""
    response = openai.chat_completions.create(
        model="gpt-3.5-turbo",  # Ensure you use the correct model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=30
    )
    return response['choices'][0]['message']['content'].strip()

# --- Perform Web Search ---
         
def perform_web_search(query):
    search = GoogleSearch({
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google",  # This can be changed to other engines like Google News, Bing, etc.
    })
    
    results = search.get_dict()  # Get results as a dictionary
    urls = []
    if 'organic_results' in results:
        for item in results['organic_results']:
            urls.append(item['link'])
    return urls

# --- Extract content ---
def extract_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return " ".join(p.get_text() for p in paragraphs)[:2000]  # Limit to avoid overflow
    except:
        return ""

# --- Summarize with OpenAI ---
def synthesize_information(contents):
    prompt = "Summarize this information into a clear research answer:\n\n" + "\n\n".join(contents)
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  # Use the correct model name from OpenAI
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response['choices'][0]['message']['content'].strip()

# --- Full Agent ---
def research_agent(query):
    improved = analyze_query(query)
    urls = perform_web_search(improved)
    texts = [extract_content(url) for url in urls]
    summary = synthesize_information(texts)
    return summary, urls

# --- Streamlit UI ---
st.set_page_config(page_title="Web Research Agent", layout="centered")
st.title("🔍 Web Research Agent")
st.markdown("Enter a topic or question. The agent will search the web, extract relevant data, and summarize it for you.")

query = st.text_input("Enter your research query")
search_btn = st.button("Start Research")

if search_btn and query:
    with st.spinner("Working on your request..."):
        try:
            summary, urls = research_agent(query)
            st.success("Done!")

            st.subheader("📄 Summary")
            st.write(summary)

            st.subheader("🔗 Sources")
            for url in urls:
                st.markdown(f"- [{url}]({url})")

        except Exception as e:
            st.error(f"Error: {e}")
