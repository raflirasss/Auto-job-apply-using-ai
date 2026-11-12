"""Skill and job-title vocabularies (English + Indonesian aliases), matched on word boundaries."""

from __future__ import annotations

import re
from functools import lru_cache

SKILLS: dict[str, tuple[str, ...]] = {
    # Marketing / e-commerce / creative
    "Digital Marketing": ("digital marketing", "pemasaran digital", "online marketing", "marketing digital"),
    "Social Media": ("social media", "media sosial", "sosial media", "sosmed"),
    "Content Creation": ("content creation", "content creator", "pembuatan konten", "membuat konten", "create content", "konten"),
    "Copywriting": ("copywriting", "copywriter", "copy writing"),
    "Facebook Ads": ("facebook ads", "meta ads", "fb ads", "instagram ads"),
    "Google Ads": ("google ads", "google adwords", "adwords"),
    "SEO": ("seo", "search engine optimization"),
    "TikTok": ("tiktok", "tik tok"),
    "Instagram": ("instagram",),
    "Marketplace Management": ("marketplace", "e-marketplace"),
    "Shopee": ("shopee",),
    "Tokopedia": ("tokopedia",),
    "Lazada": ("lazada",),
    "TikTok Shop": ("tiktok shop",),
    "E-commerce": ("e-commerce", "ecommerce", "e commerce", "online shop", "toko online"),
    "Product Listing": ("product listing", "listing produk", "upload produk", "product upload", "product listings"),
    "Catalog Management": ("catalog management", "katalog", "catalogue", "catalog"),
    "Customer Service": ("customer service", "pelayanan pelanggan", "layanan pelanggan", "customer support", "customer care"),
    "Order Handling": ("customer orders", "handling orders", "pesanan", "order processing", "process orders"),
    "WhatsApp": ("whatsapp", "wa business"),
    "Graphic Design": ("graphic design", "desain grafis", "design grafis"),
    "Canva": ("canva",),
    "CapCut": ("capcut",),
    "Adobe Photoshop": ("photoshop",),
    "Adobe Illustrator": ("illustrator",),
    "Adobe Premiere": ("premiere",),
    "CorelDRAW": ("coreldraw", "corel draw"),
    "Figma": ("figma",),
    "Video Editing": ("video editing", "edit video", "editing video", "short-form video", "video content", "reels"),
    "Photo Editing": ("photo editing", "edit foto", "editing foto", "product photo editing"),
    # Office / data
    "Microsoft Excel": ("microsoft excel", "ms excel", "excel"),
    "Google Sheets": ("google sheets", "google sheet", "spreadsheet"),
    "Microsoft Office": ("microsoft office", "ms office"),
    "Data Analysis": ("data analysis", "analisis data", "analisa data", "sales analysis", "data analyst"),
    "Data Entry": ("data entry", "input data", "entry data"),
    "Data Management": ("data management",),
    "Power BI": ("power bi", "powerbi"),
    "Tableau": ("tableau",),
    "English": ("english", "bahasa inggris"),
    # Technology
    "Python": ("python",),
    "JavaScript": ("javascript",),
    "TypeScript": ("typescript",),
    "React": ("react", "reactjs", "react.js"),
    "Next.js": ("next.js", "nextjs"),
    "Node.js": ("node.js", "nodejs"),
    "PHP": ("php",),
    "Laravel": ("laravel",),
    "Java": ("java",),
    "Golang": ("golang",),
    "SQL": ("sql", "mysql", "postgresql", "postgres"),
    "HTML": ("html",),
    "CSS": ("css",),
    "Git": ("git", "github", "gitlab"),
    "Docker": ("docker",),
    "REST API": ("rest api", "restful api", "restful"),
    "Networking": ("networking", "jaringan komputer"),
    "Troubleshooting": ("troubleshooting", "troubleshoot"),
    "Hardware": ("hardware", "perangkat keras"),
}

# Job-title keywords per category. Category names match services.categories.CATEGORY_KEYWORDS.
TITLE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Digital Marketing": ("digital marketing", "digital marketer", "marketing digital", "performance marketing", "ads specialist", "advertiser", "marketing"),
    "Marketplace Administration": ("admin marketplace", "marketplace admin", "marketplace specialist", "marketplace", "admin online shop", "admin e-commerce", "admin ecommerce"),
    "E-commerce Operations": ("e-commerce", "ecommerce", "online shop", "toko online"),
    "Social Media Management": ("social media", "sosial media", "media sosial", "sosmed"),
    "Content Creation": ("content creator", "content writer", "content specialist", "konten", "content", "video editor", "creator"),
    "Graphic Design": ("graphic designer", "desain grafis", "designer", "desainer"),
    "Customer Service": ("customer service", "customer support", "customer care", "customer experience"),
    "Data Analysis": ("data analyst", "analis data", "business analyst", "data analysis"),
    "Administration": ("admin", "administrasi", "administration", "administrative"),
    "Web Development": ("web developer", "frontend", "front end", "front-end", "full stack", "fullstack", "web programmer"),
    "Software Engineering": ("software engineer", "backend", "back end", "back-end", "developer", "programmer", "mobile engineer"),
    "IT Support": ("it support", "helpdesk", "help desk", "technical support", "it staff", "network engineer"),
}


@lru_cache(maxsize=512)
def _pattern(alias: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w]){re.escape(alias)}(?![\w])")


def contains(text: str, alias: str) -> bool:
    return bool(_pattern(alias).search(text))


def extract_skills(text: str) -> set[str]:
    lower = text.lower()
    return {skill for skill, aliases in SKILLS.items() if any(contains(lower, a) for a in aliases)}


def title_categories(title: str) -> set[str]:
    lower = title.lower()
    return {cat for cat, kws in TITLE_CATEGORIES.items() if any(contains(lower, k) for k in kws)}
