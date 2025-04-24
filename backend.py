import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import re
import json
from urllib.parse import quote_plus

# ✅ Set your keys here
openai.api_key = "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"

# --- Query Analyzer ---
def analyze_query(user_query):
    prompt = f"""Improve the following research query for accurate web results:\n\nOriginal: "{user_query}"\n\nImproved:"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=30
    )
    return response.choices[0].message.content.strip()

# --- Alternative Web Search Function ---
def perform_web_search(query):
    # Create a safe search query
    encoded_query = quote_plus(query)
    
    # Use DuckDuckGo's HTML search (no API key needed)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract links from search results
        results = soup.find_all('a', class_='result__a')
        urls = []
        
        for result in results[:5]:  # Get top 5 results
            link = result.get('href')
            if link and link.startswith('http'):
                urls.append(link)
            elif link and '//' in link:
                # Extract URL from redirects
                match = re.search(r'uddg=([^&]+)', link)
                if match:
                    extracted_url = match.group(1)
                    urls.append(extracted_url)
        
        return urls[:5]  # Return top 5 results
        
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

# --- Extract content from URL ---
def extract_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text
        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text() for p in paragraphs)
        
        # Clean up text
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content[:2000]  # Limit to 2000 chars
    except Exception as e:
        return f"Error extracting content from {url}: {str(e)}"

# --- Summarize using OpenAI ---
def synthesize_information(contents, query):
    prompt = f"""Summarize this information into a clear, concise research answer for the query: "{query}"\n\n""" + "\n\n".join(contents)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error in summarization: {str(e)}"

# --- Main Agent Function ---
def research_agent(query):
    st.write("📝 Analyzing query...")
    improved = analyze_query(query)
    
    st.write(f"🔍 Searching for: {improved}")
    urls = perform_web_search(improved)
    
    st.write(f"🌐 Found {len(urls)} sources")
    
    texts = []
    for i, url in enumerate(urls):
        st.write(f"📄 Extracting content from source {i+1}...")
        text = extract_content(url)
        if text and len(text) > 100:  # Only include substantial content
            texts.append(text)
    
    if not texts:
        return "I couldn't find enough information to answer your query. Please try rephrasing or ask something else.", urls
    
    st.write("🧠 Synthesizing information...")
    summary = synthesize_information(texts, query)
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
            st.error(f"Error: {str(e)}")
