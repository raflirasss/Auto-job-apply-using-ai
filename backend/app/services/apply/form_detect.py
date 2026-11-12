"""Detect visible form fields on a page and turn them into FormField objects."""

from __future__ import annotations

from app.services.apply.classify import FormField

# Runs in the page. Returns plain data; values are never read.
_JS = r"""
() => {
  const out = [];
  const els = Array.from(document.querySelectorAll('input, textarea, select'));
  let i = 0;
  for (const el of els) {
    const type = (el.tagName === 'SELECT') ? 'select' : (el.tagName === 'TEXTAREA' ? 'textarea' : (el.type || 'text').toLowerCase());
    if (['hidden', 'submit', 'button', 'reset', 'image', 'search'].includes(type)) continue;
    const style = window.getComputedStyle(el);
    // File inputs are often visually hidden behind a styled button: check their container instead.
    const box = type === 'file' ? (el.closest('label') || el.parentElement || el) : el;
    const visible = type === 'file'
      ? box.getClientRects().length > 0 && window.getComputedStyle(box).visibility !== 'hidden'
      : (el.offsetParent !== null && style.visibility !== 'hidden' && style.display !== 'none');
    if (!visible || el.disabled) continue;
    const id = el.id;
    let label = '';
    if (id) { const l = document.querySelector(`label[for="${CSS.escape(id)}"]`); if (l) label = l.innerText; }
    if (!label) { const l = el.closest('label'); if (l) label = l.innerText; }
    if (!label) label = el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
    if (!label) {
      const fs = el.closest('fieldset'); const lg = fs && fs.querySelector('legend'); if (lg) label = lg.innerText;
    }
    const marker = `ajh-${i++}`;
    el.setAttribute('data-ajh', marker);
    let options = [];
    if (el.tagName === 'SELECT') options = Array.from(el.options).filter(o => o.value !== '').map(o => o.text.trim());
    if (type === 'radio' && el.name) {
      const group = Array.from(document.querySelectorAll(`input[type=radio][name="${CSS.escape(el.name)}"]`));
      if (group[0] !== el) continue;  // one entry per radio group
      options = group.map(r => { const l = r.id && document.querySelector(`label[for="${CSS.escape(r.id)}"]`); return (l ? l.innerText : r.value).trim(); });
      const fs = el.closest('fieldset'); const lg = fs && fs.querySelector('legend'); if (lg) label = lg.innerText;
    }
    const required = el.required || el.getAttribute('aria-required') === 'true' || /\*\s*$/.test(label.trim());
    out.push({ selector: `[data-ajh="${marker}"]`, label: label.replace(/\s+/g, ' ').replace(/\*\s*$/, '').trim(),
               tag: el.tagName.toLowerCase(), type, name: el.name || '', required, options });
  }
  return out;
}
"""


def detect_fields(page) -> list[FormField]:
    return [FormField(**raw) for raw in page.evaluate(_JS)]


def fill(page, decision) -> None:
    """Apply one decision. Raises on failure; caller treats any exception as a stop."""
    f = decision.field
    loc = page.locator(f.selector)
    if decision.action == "upload":
        loc.set_input_files(decision.value)
    elif decision.action == "select":
        if f.type == "radio":
            name = f.name.replace('"', '\\"')
            radios = page.locator(f'input[type=radio][name="{name}"]')
            idx = f.options.index(decision.value)
            radios.nth(idx).check()
        else:
            loc.select_option(label=decision.value)
    elif decision.action == "fill":
        loc.fill(decision.value)


def validation_errors(page) -> list[str]:
    """Native constraint-validation failures plus visible aria-invalid fields (labels only)."""
    return page.evaluate(r"""
    () => Array.from(document.querySelectorAll('input, textarea, select'))
      .filter(el => el.offsetParent !== null || el.type === 'file')
      .filter(el => (el.willValidate && !el.checkValidity()) || el.getAttribute('aria-invalid') === 'true')
      .map(el => (el.labels && el.labels[0] ? el.labels[0].innerText : (el.name || el.id || el.type)).trim())
    """)
