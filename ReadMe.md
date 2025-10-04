# AiAgent - a project for fun!

This is a **personal project** I built for fun to explore how to create a simple AI-powered research assistant in Python. I got bored and did this for literally no reason.
The project integrates **LangChain**, **OpenAI**, **Anthropic**, and community tools (DuckDuckGo & Wikipedia) to run queries, parse structured outputs, and even save results to a text file.

##  Features that I used to build a lil' LLM, cause why not!?
- Uses **LangChain** with:
  - `langchain-openai` → access to OpenAI’s GPT models.
  - `langchain-anthropic` → access to Anthropic’s models.
  - `langchain-community` → DuckDuckGo + Wikipedia integrations.
- A **Pydantic schema** enforces structured outputs (topic, summary, sources, tools used).
- **Custom tools**:
  - 🔍 Search the web with DuckDuckGo.
  - 📚 Query Wikipedia for quick lookups.
  - 💾 Save structured results automatically to `research_output.txt`.
- Wraps everything in a **tool-calling agent** powered by LangChain.
- Interactive command-line input (`What can I help you research?`).

## 📂 Project Structure
AiAgent/
├── main.py             # Entry point – sets up the model, parser, and agent
├── tools.py            # Custom tools: save to file, DuckDuckGo, Wikipedia
├── requirements.txt    # Dependencies
├── .env                # Stores API keys (not in repo, ignored by Git)
├── .gitignore          # Ignore venv, cache, env files, etc.
└── venv/               # Virtual environment (ignored)

## ⚙️ Installation
1. **Clone the repo**
   git clone https://github.com/dzweben/AiAgent.git
   cd AiAgent

2. **Set up virtual environment**

   - I mean...you don't have to do this all from a virtual enviornment but I decided to for funsies.
     
   python3 -m venv venv
   source venv/bin/activate   # Mac/Linux
   venv\Scripts\activate      # Windows

4. **Install dependencies**
   pip install -r requirements.txt

5. **Set environment variables**
   Create a `.env` file in the project root:
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key

## ▶Usage
Run the agent:
   python3 main.py

Example interaction:
   What can I help you research? "The health benefits of drinking green tea" (sorry for a more boring example I was burnt out of this project by the time I got here!)

Output (to console & saved in `research_output.txt`):
{
  "topic": "Green Tea Health Benefits",
  "summary": "Green tea is rich in antioxidants and may reduce the risk of heart disease, improve brain function, and support weight loss.",
  "sources": [
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6520897/",
    "https://www.healthline.com/nutrition/top-10-evidence-based-health-benefits-of-green-tea"
  ],
  "tools_used": ["search", "wikipedia", "save_text_to_file"]
}

## 📦 Requirements
See `requirements.txt`:
- langchain
- langchain-community
- langchain-openai
- langchain-anthropic
- wikipedia
- python-dotenv
- pydantic
- ddgs

## 📝 Notes
- This is just a **sandbox project** to play with AI agent design. I guess this is what I do when I get bored?
- Virtual environments are intentionally ignored (`venv/` in `.gitignore`).
- Output file appends new research queries with timestamps.

