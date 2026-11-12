"""Cover letter and application email built only from profile facts (nothing guessed)."""

from __future__ import annotations

from app.schemas.candidate import CandidateProfileData
from app.services.documents.content import TailoredResume


def _join(items: list[str], lang: str) -> str:
    items = [i for i in items if i]
    if len(items) <= 1:
        return items[0] if items else ""
    return f"{', '.join(items[:-1])} {'dan' if lang == 'id' else 'and'} {items[-1]}"


def _degree_phrase(profile: CandidateProfileData, lang: str) -> str | None:
    if not profile.education:
        return None
    e = profile.education[0]
    degree = e.degree or e.field_of_study
    if not degree:
        return None
    if lang == "id":
        return f"mahasiswa {degree} di {e.institution}" if e.is_expected else f"lulusan {degree} dari {e.institution}"
    return f"a {degree} student at {e.institution}" if e.is_expected else f"a {degree} graduate from {e.institution}"


def _role_line(exp, lang: str) -> str:
    title = exp.title or ("staf" if lang == "id" else "a team member")
    if lang == "id":
        return f"sebagai {title} di {exp.company}" + (f" ({exp.dates})" if exp.dates else "")
    return f"as {title} at {exp.company}" + (f" ({exp.dates})" if exp.dates else "")


def _top_bullets(resume: TailoredResume, n: int = 3) -> list[str]:
    """Most job-relevant bullets (already relevance-sorted), quoted verbatim from the profile."""
    return [b.rstrip(".") + "." for exp in resume.experience for b in exp.bullets[:2]][:n]


def cover_letter(profile: CandidateProfileData, resume: TailoredResume, job, lang: str) -> list[str]:
    """Paragraphs: salutation first, sign-off last.

    Profile sentences are quoted verbatim (never translated or rephrased), so they stay
    factually identical to the CV. Callers should pass the profile's own language.
    """
    company = job.company or ("perusahaan Anda" if lang == "id" else "your company")
    skills = resume.relevant_skills[:5]
    bullets = _top_bullets(resume)
    degree = _degree_phrase(profile, lang)
    roles = [_role_line(e, lang) for e in resume.experience[:2]]
    name = profile.personal.full_name or ""

    if lang == "id":
        paras = ["Dengan hormat,"]
        intro = f"Saya ingin melamar posisi {job.title} di {company}."
        if degree:
            intro += f" Saya adalah {degree}."
        paras.append(intro)
        if roles:
            paras.append(f"Saya memiliki pengalaman kerja {_join(roles, lang)}. Beberapa tanggung jawab yang relevan dengan posisi ini:")
            paras += [f"• {b}" for b in bullets]
        if skills:
            paras.append(f"Keahlian saya yang sesuai dengan posisi ini meliputi {_join(skills, lang)}.")
        paras.append("Terlampir CV saya untuk pertimbangan Bapak/Ibu. Saya berharap dapat berdiskusi lebih lanjut mengenai kontribusi yang dapat saya berikan. Terima kasih atas waktu dan perhatiannya.")
        paras.append(f"Hormat saya,\n{name}")
    else:
        paras = ["Dear Hiring Manager,"]
        intro = f"I am writing to apply for the {job.title} position at {company}."
        if degree:
            intro += f" I am {degree}."
        paras.append(intro)
        if roles:
            paras.append(f"I have worked {_join(roles, lang)}. Responsibilities relevant to this role include:")
            paras += [f"• {b}" for b in bullets]
        if skills:
            paras.append(f"Skills I would bring to this role include {_join(skills, lang)}.")
        paras.append("My CV is attached for your consideration. I would welcome the opportunity to discuss how I can contribute to your team. Thank you for your time.")
        paras.append(f"Sincerely,\n{name}")
    return paras


def application_email(profile: CandidateProfileData, job, lang: str) -> tuple[str, str]:
    name = profile.personal.full_name or ""
    company = job.company or ""
    contact = " | ".join(x for x in (profile.personal.phone, profile.personal.email) if x)
    if lang == "id":
        subject = f"Lamaran Posisi {job.title} - {name}".strip(" -")
        body = (f"Yth. Tim Rekrutmen{' ' + company if company else ''},\n\n"
                f"Saya bermaksud melamar posisi {job.title}. Bersama email ini saya lampirkan CV dan surat lamaran saya.\n\n"
                f"Terima kasih atas perhatiannya.\n\nHormat saya,\n{name}\n{contact}")
    else:
        subject = f"Application for {job.title} - {name}".strip(" -")
        body = (f"Dear {company + ' ' if company else ''}Recruitment Team,\n\n"
                f"I would like to apply for the {job.title} position. Please find my CV and cover letter attached.\n\n"
                f"Thank you for your consideration.\n\nBest regards,\n{name}\n{contact}")
    return subject, body
