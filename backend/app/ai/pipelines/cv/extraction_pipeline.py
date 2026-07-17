"""CV extraction pipeline based on LiteParse."""

from app.ai.providers.parsing.liteparse_client import create_liteparse_client


def extract_cv_to_markdown(file_path: str) -> str:
    """Parse a CV file and return markdown content.

    The client is configured with output_format="markdown", so
    result.text already contains the fully rendered document markdown
    (headings, lists, tables). ParsedPage objects have no per-page
    `markdown` attribute, so there is nothing to reconstruct per page.
    """
    parser = create_liteparse_client()
    result = parser.parse(file_path)
    text = getattr(result, "text", "")
    return str(text).strip()
