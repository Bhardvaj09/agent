import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
import time

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

# --- Alternative Web Search Function using Google ---
def perform_google_search(query):
    encoded_query = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Save HTML
        st.session_state.last_html = response.text[:10000]  # Store first 10K chars for debugging
        
        # Find all search result links
        links = []
        for result in soup.find_all('a'):
            href = result.get('href', '')
            # Google search results have hrefs that start with '/url?q='
            if href.startswith('/url?q='):
                # Extract actual URL
                actual_url = href.split('/url?q=')[1].split('&')[0]
                if actual_url.startswith('http') and 'google' not in actual_url:
                    links.append(actual_url)
        
        # Return unique links
        unique_links = list(dict.fromkeys(links))
        return unique_links[:5]
    
    except Exception as e:
        st.error(f"Google search error: {str(e)}")
        return []

# --- DuckDuckGo Search (updated parser) ---
def perform_duckduckgo_search(query):
    encoded_query = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: Save HTML
        st.session_state.last_html = response.text[:10000]  # Store first 10K chars for debugging
        
        # Try different selectors for DuckDuckGo results
        results = soup.select('.result__a') or soup.select('.result-link') or soup.select('a.result')
        
        urls = []
        for result in results[:10]:
            link = result.get('href')
            if link:
                # Try to extract the real URL from DuckDuckGo redirect
                if 'duckduckgo.com/l/' in link or '/l/?uddg=' in link:
                    match = re.search(r'uddg=([^&]+)', link)
                    if match:
                        try:
                            from urllib.parse import unquote
                            extracted_url = unquote(match.group(1))
                            urls.append(extracted_url)
                        except:
                            pass
                elif link.startswith('http'):
                    urls.append(link)
        
        if not urls:  # If no results found, look for any links in the page
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('http') and 'duckduckgo.com' not in href:
                    urls.append(href)
        
        return urls[:5]
        
    except Exception as e:
        st.error(f"DuckDuckGo search error: {str(e)}")
        return []

# --- Combined search function ---
def perform_web_search(query):
    # Try DuckDuckGo first
    urls = perform_duckduckgo_search(query)
    
    # If DuckDuckGo fails, try Google
    if not urls:
        st.info("DuckDuckGo search returned no results. Trying Google...")
        urls = perform_google_search(query)
    
    # If both fail, use OpenAI to suggest URLs
    if not urls and st.session_state.openai_api_key:
        st.info("Web searches failed. Using AI to suggest relevant websites...")
        prompt = f"""For the query "{query}", suggest 5 specific websites (with full URLs) that would have relevant and authoritative information. Format each as a full URL on a new line."""
        
        messages = [{"role": "user", "content": prompt}]
        ai_urls = get_openai_response(messages)
        
        if ai_urls:
            # Extract URLs from the AI response
            url_pattern = r'https?://[^\s)"]+'
            extracted_urls = re.findall(url_pattern, ai_urls)
            urls = extracted_urls[:5]
    
    return urls

# --- Extract content from URL ---
def extract_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Get text from paragraphs
        paragraphs = soup.find_all("p")
        content = " ".join(p.get_text() for p in paragraphs)
        
        # If no paragraphs found, get all text
        if not content:
            content = soup.get_text()
        
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
    st.write(f"📊 Improved query: '{improved}'")
    
    st.write(f"🔍 Searching the web...")
    urls = perform_web_search(improved)
    
    if not urls:
        # Show debugging info if search failed
        st.error("No search results found. Here's some HTML from the last search attempt:")
        if 'last_html' in st.session_state:
            with st.expander("HTML Sample"):
                st.code(st.session_state.last_html[:1000])
        return "I couldn't find any relevant sources. The search might be blocked or returning no results.", []
    
    st.write(f"🌐 Found {len(urls)} sources")
    for url in urls:
        st.write(f"- {url}")
    
    texts = []
    for i, url in enumerate(urls):
        st.write(f"📄 Extracting content from source {i+1}...")
        text = extract_content(url)
        if text and len(text) > 150:  # Only include substantial content
            # Show a sample of the extracted text
            st.write(f"Sample: {text[:150]}...")
            texts.append(text)
        else:
            st.write("Couldn't extract useful content from this source.")
    
    if not texts:
        return "I found sources but couldn't extract meaningful content. The sites might be blocking automated access.", urls
    
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

# Option to adjust the search engine
search_engine = st.radio(
    "Select search engine:",
    ["DuckDuckGo", "Google", "Both (try DuckDuckGo first)"],
    index=2
)

# Add a debug section
with st.expander("Debug Options"):
    if st.button("Clear Session State"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Session state cleared!")
    
    show_html = st.checkbox("Show HTML response from search engine")

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
                    
                # Show HTML in debug mode
                if show_html and 'last_html' in st.session_state:
                    st.subheader("Debug: HTML Response")
                    st.code(st.session_state.last_html[:5000], language="html")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
