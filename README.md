WEB RESEARCH AGENT

A powerful Streamlit-based web app that helps you research any topic by:
- Enhancing your search query using OpenAI
- Searching the web (via DuckDuckGo and Google)
- Extracting and analyzing website content
- Summarizing key information using GPT

##  Features

- **Smart Query Refinement**: Uses OpenAI to improve your original question.
- **Dual Search Engines**: Searches DuckDuckGo first, then falls back to Google if needed.
- **Web Scraping**: Extracts text from top websites for the given topic.
- **Summarization**: Uses GPT to generate a clear and concise summary.
- **Streamlit Interface**: Clean, interactive UI with debug options.

---

##  Requirements

Install dependencies via pip:

```
pip install -r requirements.txt
```

**`requirements.txt`:**
```
streamlit
requests
beautifulsoup4
openai
```

---

## 🔧 Setup Instructions



2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the App**
   ```bash
   streamlit run app.py
   ```

4. **Enter your OpenAI API key** in the input box at the top.

---

## 🛠 Usage

- Type a research question into the input box (e.g., *"What are the health benefits of green tea?"*).
- Click **Start Research**.
- The app will:
  - Refine your query
  - Search the web
  - Extract and summarize content
- View the final summary and source links.

---

## Debugging Features

- **HTML View**: Optionally show raw HTML returned from search pages.
- **Clear Session State**: Reset the app without refreshing the browser.

## Powered By

- [Streamlit](https://streamlit.io/)
- [OpenAI GPT](https://openai.com/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [DuckDuckGo HTML Search](https://duckduckgo.com/html/)
- Google Search (via HTML scraping)
