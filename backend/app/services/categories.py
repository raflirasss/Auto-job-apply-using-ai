"""Job-category evidence: which potential categories are actually supported by the profile.

A category is only *suggested* when profile text contains supporting evidence. The owner
decides; nothing is auto-selected. Keyword lists are intentionally conservative.
"""

from __future__ import annotations

import re

from app.schemas.candidate import CandidateProfileData

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Digital Marketing": ("digital marketing", "facebook ads", "google ads", "social media marketing", "digital promotion", "copywriting", "seo", "sem"),
    "Marketplace Administration": ("marketplace", "shopee", "tokopedia", "lazada", "product listing", "catalog management"),
    "E-commerce Operations": ("e-commerce", "ecommerce", "marketplace", "order", "voucher", "free shipping", "sales performance"),
    "Social Media Management": ("social media", "instagram", "tiktok", "reels", "feed", "fyp"),
    "Content Creation": ("content creation", "short-form video", "reels", "capcut", "promotional content", "video content"),
    "Graphic Design": ("graphic design", "canva", "photoshop", "illustrator", "figma", "banner", "photo editing", "product visuals"),
    "Customer Service": ("customer service", "customer communication", "customer orders", "inquiries", "whatsapp"),
    "Data Analysis": ("data analysis", "sales analysis", "excel", "google sheets", "sql", "power bi", "tableau", "python"),
    "Administration": ("administration", "data management", "microsoft excel", "google sheets", "data entry"),
    "Web Development": ("web development", "html", "css", "javascript", "typescript", "react", "next.js", "laravel", "php", "node"),
    "Software Engineering": ("software engineer", "backend", "frontend", "python", "java", "golang", "api", "git", "docker"),
    "IT Support": ("it support", "helpdesk", "troubleshooting", "networking", "hardware", "technical support"),
}


def profile_text(profile: CandidateProfileData) -> str:
    parts: list[str] = [profile.summary or ""]
    for exp in profile.experience:
        parts += [exp.title or "", *exp.responsibilities]
    for edu in profile.education:
        parts += [edu.degree or "", edu.field_of_study or ""]
    for group in profile.skills:
        parts += [group.category, *group.skills]
    for proj in profile.projects:
        parts += [proj.name, proj.description or "", *proj.technologies]
    parts += [c.name for c in profile.certifications]
    return "\n".join(parts).lower()


def category_evidence(profile: CandidateProfileData) -> list[dict]:
    text = profile_text(profile)
    out = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = [k for k in keywords if re.search(rf"(?<![\w]){re.escape(k)}(?![\w])", text)]
        out.append({
            "category": category,
            "evidence": hits,
            "supported": len(hits) >= 2,
            "selected": category in profile.target_job_categories,
        })
    out.sort(key=lambda c: (-len(c["evidence"]), c["category"]))
    return out
