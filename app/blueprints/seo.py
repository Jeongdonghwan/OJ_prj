"""SEO: sitemap.xml + robots.txt."""
import sqlalchemy as sa
from flask import Blueprint, Response, current_app

from app.db import schema
from app.db.engine import get_conn

bp = Blueprint("seo", __name__)

STATIC_PATHS = ["/", "/community", "/news", "/columns", "/quiz/archive",
                "/policy", "/terms"]
MAX_URLS = 5000


@bp.get("/sitemap.xml")
def sitemap():
    site = current_app.config["SITE_URL"]
    conn = get_conn()
    entries = [(f"{site}{p}", None) for p in STATIC_PATHS]

    p = schema.posts
    posts = conn.execute(
        sa.select(p.c.id, p.c.created_at, p.c.updated_at)
        .where(p.c.deleted_at.is_(None))
        .order_by(p.c.id.desc()).limit(MAX_URLS)
    ).mappings().all()
    for r in posts:
        lastmod = (r["updated_at"] or r["created_at"])
        entries.append((f"{site}/post/{r['id']}", lastmod.date().isoformat()))

    n = schema.news_articles
    news = conn.execute(
        sa.select(n.c.id, n.c.published_at)
        .order_by(n.c.id.desc()).limit(MAX_URLS)
    ).mappings().all()
    for r in news:
        entries.append((f"{site}/news/{r['id']}", r["published_at"].date().isoformat()))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in entries:
        lines.append("<url>")
        lines.append(f"  <loc>{loc}</loc>")
        if lastmod:
            lines.append(f"  <lastmod>{lastmod}</lastmod>")
        lines.append("</url>")
    lines.append("</urlset>")
    return Response("\n".join(lines), mimetype="application/xml")


@bp.get("/robots.txt")
def robots():
    site = current_app.config["SITE_URL"]
    body = "\n".join([
        "User-agent: *",
        "Disallow: /admin",
        "Disallow: /my",
        "Disallow: /api/",
        "Disallow: /write",
        "Disallow: /notifications",
        "Disallow: /auth/",
        "Disallow: /logout",
        "",
        f"Sitemap: {site}/sitemap.xml",
    ])
    return Response(body, mimetype="text/plain")
