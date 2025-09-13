from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()
class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]


llm = ChatOpenAI(model ="gpt-4o")
parser = PydanticOutputParser(pydantic_object=ResearchResponse)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", 
         """
        "You are an APA scientific research assistant. "
        "You will be given a topic to research. You will return a summary of your Research-Backed "
        "findings, a list of sources you used, and a list of tools you used"
        "Please only use validated scientific sources"
        "Wrap the output in this format and provide no other text\n{format_instructions}
        """
    ),
    ("placeholder", "{chat_history}"),
    ("human", "{query}"),
    ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())



