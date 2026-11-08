"""Knowledge-base articles: written, reviewed, published, retired."""
from .models import DeskError


class Article:
    def __init__(self, slug, title, author):
        self.slug = slug
        self.title = title
        self.author = author
        self.body = ""
        self.status = "draft"
        self.reviewer = None


def submit(article):
    if article.status != "draft":
        raise DeskError(f"only drafts are submitted, not {article.status}")
    if not article.body.strip():
        raise DeskError("an empty article cannot be reviewed")
    article.status = "in_review"


def approve(article, reviewer):
    if article.status != "in_review":
        raise DeskError(f"nothing to approve: {article.status}")
    if reviewer == article.author:
        raise DeskError("authors cannot approve their own article")
    article.reviewer = reviewer
    article.status = "published"


def send_back(article):
    if article.status != "in_review":
        raise DeskError(f"nothing to send back: {article.status}")
    article.status = "draft"


def retire(article):
    if article.status != "published":
        raise DeskError(f"only published articles retire, not {article.status}")
    article.status = "retired"


def visible(articles):
    return [a for a in articles if a.status == "published"]
