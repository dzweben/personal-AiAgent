"""entry point.

this is still the same little script it always was: ask a question, let the agent go do
research with its tools, print a structured answer. the heavy lifting just moved into the
`agent` package so the file stays short and readable.

run it the classic way:
    python3 main.py

or, once you pip install the project, use the nicer cli:
    aiagent research "the health benefits of green tea" --export markdown
"""

from dotenv import load_dotenv

from agent import console
from agent.agent import build_agent
from agent.config import load_settings

# keep importing the old schema name from here too, some of my notebooks reference it
from agent.models import ResearchResponse  # noqa: F401

load_dotenv()


def main():
    settings = load_settings()
    console.banner()
    console.info(
        f"provider={settings.provider} model={settings.model} "
        f"temperature={settings.temperature}"
    )

    agent = build_agent(settings=settings)

    query = input("What can I help you research? ")
    result = agent.research(query)

    # print the pretty version, and fall back to the raw output if parsing flopped
    console.print_response(result)
    if result.structured is None:
        print("Raw Response -", result.raw)


if __name__ == "__main__":
    main()
