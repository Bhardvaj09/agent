import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus

# --- Initialize session state to store the API key ---
if 'openai_api_key' not in st.session_state:
    st.session_state.openai_api_key = None

# --- Set up OpenAI with the API key ---
def get_openai_response(messages, model="gpt-3.5-turbo", max_tokens=500, temperature=0.7):
    import openai
    client = openai.OpenAI(api_key=st.session_state.openai_api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"OpenAI API error: {str(e)}")
        return None

# --- Query Analyzer ---
def analyze_query(user_query):
    if not st.session_state.openai_api_key:
        return user_query
        
    prompt = f"""Improve the following research query for accurate web results:\n\nOriginal: "{user_query}"\n\nImproved:"""
    
    messages = [{"role": "user", "content": prompt}]
    improved = get_openai_response(messages, max_tokens=30)
    
    return improved if improved else user_query

# --- Web Search Function ---
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
    if not st.session_state.openai_api_key:
        return "API key not configured. Please add your OpenAI API key above."
    
    prompt = f"""Summarize this information into a clear, concise research answer for the query: "{query}"\n\n""" + "\n\n".join(contents)
    
    messages = [{"role": "user", "content": prompt}]
    summary = get_openai_response(messages, max_tokens=500)
    
    return summary if summary else "Failed to generate summary. Please check your API key and try again."

# --- Main Agent Function ---
def research_agent(query):
    if not st.session_state.openai_api_key:
        st.error("OpenAI API key not configured. Please add it above.")
        return "Please enter a valid OpenAI API key to continue.", []
    
    st.write("📝 Analyzing query...")
    improved = analyze_query(query)
    
    st.write(f"🔍 Searching for: {improved}")
    urls = perform_web_search(improved)
    
    if not urls:
        return "I couldn't find any relevant sources. Please try a different query.", []
    
    st.write(f"🌐 Found {len(urls)} sources")
    
    texts = []
    for i, url in enumerate(urls):
        st.write(f"📄 Extracting content from source {i+1}...")
        text = extract_content(url)
        if text and len(text) > 100:  # Only include substantial content
            texts.append(text)
    
    if not texts:
        return "I found sources but couldn't extract meaningful content. Please try another query.", urls
    
    st.write("🧠 Synthesizing information...")
    summary = synthesize_information(texts, query)
    return summary, urls

# --- Streamlit UI ---
st.set_page_config(page_title="Web Research Agent", layout="centered")
st.title("🔍 Web Research Agent")
st.markdown("Enter a topic or question. The agent will search the web, extract relevant data, and summarize it for you.")

# API key input
api_key = st.text_input("Enter your OpenAI API Key:", type="password", key="api_key_input")
if api_key:
    st.session_state.openai_api_key = api_key
    st.success("API Key set successfully!")

query = st.text_input("Enter your research query")
search_btn = st.button("Start Research")

if search_btn and query:
    if not st.session_state.openai_api_key:
        st.error("Please enter your OpenAI API key")
    else:
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
