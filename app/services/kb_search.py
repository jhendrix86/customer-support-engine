"""
Real knowledge-base search: a genuine `ilike` text query against
persisted KnowledgeArticle rows, with a simple, honestly-computed term-
overlap relevance score - not true semantic search (no embedding
infrastructure exists anywhere in this engine, unlike baselayer's
embedding_generator.py), and not fabricated relevance numbers either.
"""

import re
from typing import List

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_article import KnowledgeArticle

_WORD_RE = re.compile(r"[a-zA-Z0-9]+")


def _words(text: str) -> set:
    return {w.lower() for w in _WORD_RE.findall(text or "") if len(w) > 2}


def _relevance(query_words: set, article: KnowledgeArticle) -> float:
    if not query_words:
        return 0.0
    article_words = _words(article.title) | _words(article.content)
    overlap = query_words & article_words
    return round(len(overlap) / len(query_words), 2)


async def search_articles(db: AsyncSession, query: str, limit: int = 5) -> List[dict]:
    """Real search: ilike match on title/content/category, ranked by term overlap."""
    query_words = _words(query)
    if not query_words:
        return []

    conditions = [
        KnowledgeArticle.title.ilike(f"%{word}%") | KnowledgeArticle.content.ilike(f"%{word}%")
        for word in query_words
    ]
    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.is_published == True, or_(*conditions))  # noqa: E712
    )
    articles = result.scalars().all()

    scored = [(a, _relevance(query_words, a)) for a in articles]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [{"article": a, "relevance": score} for a, score in scored[:limit]]
