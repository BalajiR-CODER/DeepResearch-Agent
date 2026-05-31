from typing import TypedDict, List, Optional
import json
import re

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GOOGLE_API_KEY, MODEL_NAME
from backend.tools import search_web, scrape_page

# ---------- State ----------
class ResearchState(TypedDict):
    query: str
    sub_queries: List[str]
    current_idx: int
    search_results: List[List[dict]]   # search_results[i] = results for sub_query i
    scraped_content: List[List[str]]   # scraped_content[i] = scraped texts for sub_query i
    final_report: Optional[str]

# ---------- LLM ----------
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2,
    thinking_budget=0  # disable thinking mode — keeps latency and cost predictable
)

# ---------- Nodes ----------
def planner_node(state: ResearchState) -> dict:
    """Break down the main query into 3-4 specific sub-queries."""
    prompt = f"""
You are a research assistant. Given the user's research question, break it down into 3-4 specific sub-queries that can be answered by web searches.
Return ONLY a JSON list of strings, nothing else.

User question: {state['query']}

Example output: ["subquery 1", "subquery 2", "subquery 3"]
"""
    response = llm.invoke(prompt)
    content = response.content.strip()

    try:
        # Strip markdown code fences if the model wraps output in ```json ... ```
        if "```" in content:
            content = re.sub(r"```(?:json)?\s*", "", content).replace("```", "").strip()
        sub_queries = json.loads(content)
        if not isinstance(sub_queries, list) or len(sub_queries) == 0:
            raise ValueError("Invalid format")
    except Exception:
        # Fallback: treat the original query as a single sub-query
        sub_queries = [state["query"]]

    return {
        "sub_queries": sub_queries,
        "current_idx": 0,
        "search_results": [],
        "scraped_content": []
    }


def search_node(state: ResearchState) -> dict:
    """Search the web for the current sub-query and store results."""
    idx = state["current_idx"]
    sub_q = state["sub_queries"][idx]
    results = search_web(sub_q, max_results=3)

    new_search = state["search_results"].copy()
    new_search.append(results)

    new_scrape = state["scraped_content"].copy()
    if len(new_scrape) <= idx:
        new_scrape.append([])  # placeholder; filled by scrape_node

    return {"search_results": new_search, "scraped_content": new_scrape}


def scrape_node(state: ResearchState) -> dict:
    """Scrape top 2 URLs for the current sub-query.
    Falls back to DuckDuckGo snippets if scraping fails (paywall, JS-rendered, timeout).
    """
    idx = state["current_idx"]
    results = state["search_results"][idx] if idx < len(state["search_results"]) else []
    scraped_texts = []

    for r in results[:2]:
        url = r.get("url", "")
        if url:
            text = scrape_page(url)
            if text:
                scraped_texts.append(f"Source: {url}\nTitle: {r['title']}\n\n{text}")

    # Fallback: use search snippets when scraping returns nothing
    if not scraped_texts:
        for r in results[:2]:
            if r.get("snippet"):
                scraped_texts.append(
                    f"Source: {r['url']}\nTitle: {r['title']}\n\n{r['snippet']}"
                )

    new_scrape = state["scraped_content"].copy()
    if idx < len(new_scrape):
        new_scrape[idx] = scraped_texts
    else:
        new_scrape.append(scraped_texts)

    return {"scraped_content": new_scrape}


def writer_node(state: ResearchState) -> dict:
    """Synthesize all scraped content into a markdown report with citations."""
    context_parts = []
    for i, sub_q in enumerate(state["sub_queries"]):
        context_parts.append(f"## Sub-query: {sub_q}")
        sources = state["scraped_content"][i] if i < len(state["scraped_content"]) else []
        for j, content in enumerate(sources):
            context_parts.append(f"### Source {j + 1}:\n{content}")

    full_context = "\n\n".join(context_parts)

    prompt = f"""
You are an expert research analyst. Using the web search results provided below, write a comprehensive, well-structured markdown report answering the user's original question.
The report should:
- Start with an executive summary.
- Organize information under clear headings.
- Include inline citations like [1], [2] referring to the numbered sources at the end.
- List all sources with URLs at the end under "Sources".

User question: {state['query']}

Research findings:
{full_context}

Now write the final report in markdown:
"""
    response = llm.invoke(prompt)
    return {"final_report": response.content}


# ---------- Graph ----------
def create_research_agent():
    workflow = StateGraph(ResearchState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("search", search_node)
    workflow.add_node("scrape", scrape_node)
    workflow.add_node("writer", writer_node)

    def next_subquery(state: ResearchState) -> dict:
        return {"current_idx": state["current_idx"] + 1}

    workflow.add_node("next", next_subquery)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "search")
    workflow.add_edge("search", "scrape")
    workflow.add_edge("scrape", "next")

    def route_after_next(state: ResearchState) -> str:
        if state["current_idx"] < len(state["sub_queries"]):
            return "search"
        return "writer"

    workflow.add_conditional_edges(
        "next",
        route_after_next,
        {"search": "search", "writer": "writer"}
    )
    workflow.add_edge("writer", END)

    return workflow.compile()


# Global agent instance
agent = create_research_agent()


def run_research(query: str) -> str:
    """Run the full research pipeline and return the markdown report."""
    initial_state: ResearchState = {
        "query": query,
        "sub_queries": [],
        "current_idx": 0,
        "search_results": [],
        "scraped_content": [],
        "final_report": None
    }
    final_state = agent.invoke(initial_state)
    return final_state["final_report"]