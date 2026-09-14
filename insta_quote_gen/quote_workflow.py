from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import END, START, StateGraph


class Quote(BaseModel):
    text: str = Field(description="A short inspiring quote of 10-15 words")
    keywords: list[str] = Field(
        description="One to three keywords describing the quote's theme"
    )


class QuoteBatch(BaseModel):
    quotes: list[Quote]


class QuoteGenerationState(TypedDict):
    num_quotes: int
    quotes: list[dict]


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Generate original, inspiring quotes for social media. "
            "Return only the requested structured data.",
        ),
        (
            "human",
            "Generate {num_quotes} unique quotes. Each quote must be 10-15 "
            "words and include one to three relevant keywords.",
        ),
    ]
)


def create_quote_generation_graph(model):
    structured_model = PROMPT | model.with_structured_output(QuoteBatch)

    def generate_quotes(state: QuoteGenerationState):
        result = structured_model.invoke({"num_quotes": state["num_quotes"]})
        return {"quotes": [quote.dict() for quote in result.quotes]}

    graph = StateGraph(QuoteGenerationState)
    graph.add_node("generate_quotes", generate_quotes)
    graph.add_edge(START, "generate_quotes")
    graph.add_edge("generate_quotes", END)
    return graph.compile()


def generate_new_quotes(model, num_quotes=30):
    """Generate quote records through the LangGraph workflow."""
    try:
        result = create_quote_generation_graph(model).invoke(
            {"num_quotes": num_quotes, "quotes": []}
        )
        return result["quotes"]
    except Exception as error:
        print(f"Error generating new quotes: {error}")
        return []