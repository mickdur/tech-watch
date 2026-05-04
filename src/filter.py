import logging
from src.fetcher import Item

logger = logging.getLogger(__name__)

PRIORITY_KEYWORDS = [
    # Personal productivity with AI
    "productivity", "personal ai", "ai assistant", "copilot", "note-taking", "second brain",
    "obsidian", "notion ai",
    # Code generation / dev tooling
    "code generation", "code gen", "codegen", "programming assistant", "dev tool",
    "cursor", "github copilot", "devin", "codeium", "tabnine", "aider", "continue.dev",
    "ide", "vscode", "code completion", "software engineer", "coding assistant",
    # Workflow automation / orchestration
    "workflow", "automation", "orchestration", "pipeline", "n8n", "zapier", "make.com",
    "langgraph", "prefect", "airflow", "dify",
    # Agents / multi-agent
    "agent", "multi-agent", "agentic", "autonomous", "tool use", "function calling",
    "react agent", "crew ai", "autogen", "openai swarm", "mcp", "model context protocol",
]

BROAD_KEYWORDS = [
    # Model releases / benchmarks
    "model release", "benchmark", "gpt-", "claude", "gemini", "llama", "mistral",
    "qwen", "phi-", "falcon", "yi-", "deepseek", "o1", "o3", "grok",
    "new model", "open source model", "foundation model", "frontier model",
    # Research with practical implications
    "paper", "research", "arxiv", "preprint", "fine-tun", "rag", "retrieval augmented",
    "context window", "long context", "inference", "latency", "quantization", "gguf",
    "lora", "qlora", "instruction tuning",
    # Infrastructure
    "inference server", "vllm", "ollama", "llm serving", "triton", "trt-llm",
    "embedding", "vector database", "chroma", "pinecone", "weaviate",
    # General LLM/GenAI
    "large language model", "llm", "generative ai", "gen ai", "genai",
    "transformer", "attention", "prompt", "token", "hallucination", "alignment",
    "rlhf", "dpo", "ppo", "constitutional ai",
]

DISCARD_KEYWORDS = [
    "crypto", "bitcoin", "blockchain", "web3", "nft", "defi",
    "stock market", "investment tip", "price prediction", "trading bot",
    "celebrity", "entertainment", "sports",
]


def _text(item: Item) -> str:
    return f"{item.title} {item.excerpt}".lower()


def _is_relevant(item: Item) -> bool:
    text = _text(item)

    for kw in DISCARD_KEYWORDS:
        if kw in text:
            return False

    for kw in PRIORITY_KEYWORDS:
        if kw in text:
            return True

    for kw in BROAD_KEYWORDS:
        if kw in text:
            return True

    return False


def filter_items(items: list[Item]) -> list[Item]:
    relevant = [i for i in items if _is_relevant(i)]
    logger.info(
        "Filter: %d / %d items passed relevance check",
        len(relevant),
        len(items),
    )
    return relevant
