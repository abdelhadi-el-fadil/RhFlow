"""CV extraction pipeline based on LiteParse."""

from app.ai.providers.parsing.liteparse_client import create_liteparse_client


def extract_cv_to_markdown(file_path: str) -> str:
    """Parse a CV file and return markdown content."""
    parser = create_liteparse_client()
    result = parser.parse(file_path)

    pages = getattr(result, "pages", None)
    if pages:
        markdown_parts = [str(getattr(page, "markdown", "")).strip() for page in pages]
        markdown = "\n\n".join(part for part in markdown_parts if part)
        if markdown.strip():
            return markdown.strip()

    text = getattr(result, "text", "")
    return str(text).strip()
