import requests
from bs4 import BeautifulSoup
import openai

# Set up OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your actual OpenAI API key
BING_API_KEY = "YOUR_BING_API_KEY"  # Replace with your Bing API key

# Function to analyze the query and improve it
def analyze_query(user_query):
    prompt = f"""
    You are a smart query analyst for a research agent. Improve the following research query for web search purposes. Focus it to get the most relevant and insightful web content.

    Original query: "{user_query}"

    Improved search query:
    """
    response = openai.Completion.create(
        engine="text-davinci-003",  # Change the engine as needed
        prompt=prompt.strip(),
        max_tokens=30
    )
    return response.choices[0].text.strip().replace('"', '')

# Function to perform a web search using the Bing API
def perform_web_search(query):
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": query, "count": 5}
    response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
    results = response.json()
    urls = []
    if 'webPages' in results:
        for item in results['webPages']['value']:
            urls.append(item['url'])
    return urls

# Function to extract content from a URL
def extract_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = " ".join(p.get_text() for p in paragraphs if p.get_text())
        return text[:2000]  # Limit content to avoid token overflow
    except Exception as e:
        return ""

# Function to synthesize content into a summary
def synthesize_information(contents):
    prompt = "Summarize the following information into a concise research report:\n\n" + "\n\n".join(contents)
    response = openai.Completion.create(
        engine="text-davinci-003",  # Change the engine as needed
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text.strip()

# Function to integrate all steps and perform web research
def research_agent(query):
    search_terms = analyze_query(query)
    urls = perform_web_search(search_terms)
    all_content = [extract_content(url) for url in urls if url]
    summary = synthesize_information(all_content)
    return summary, urls
