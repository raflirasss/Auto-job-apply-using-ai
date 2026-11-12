"""Local HTML fixtures served via Playwright routing (no network, no real job sites)."""

GOOD_FORM = """
<html><body>
<h1>Admin Marketplace</h1>
<form id="f" onsubmit="event.preventDefault(); document.body.innerHTML='<h2>Thank you for applying</h2><p>Your application has been submitted.</p>';">
  <label for="n">Full name *</label><input id="n" name="name" required>
  <label for="e">Email</label><input id="e" type="email" name="email" required>
  <label for="p">Mobile phone</label><input id="p" type="tel" name="phone" required>
  <label for="cv">Upload CV</label><input id="cv" type="file" name="cv" required>
  <label for="s">Expected salary</label><input id="s" name="salary">
  <label for="w">Are you legally allowed to work in Indonesia?</label>
  <select id="w" name="wa" required><option value="">--</option><option>Yes</option><option>No</option></select>
  <button type="submit">Submit application</button>
</form></body></html>
"""

UNKNOWN_QUESTION = GOOD_FORM.replace(
    '<button type="submit">',
    '<label for="q">Why do you want to join our company?</label><textarea id="q" required></textarea><button type="submit">')

LEGAL_CHECKBOX = GOOD_FORM.replace(
    '<button type="submit">',
    '<label><input type="checkbox" name="decl" required> I hereby declare that the information is accurate and complete</label><button type="submit">')

SENSITIVE = GOOD_FORM.replace(
    '<button type="submit">', '<label for="k">NIK (KTP)</label><input id="k" name="nik" required><button type="submit">')

CAPTCHA = "<html><body><div class='g-recaptcha' data-sitekey='x' style='width:300px;height:80px'>captcha</div><form><label for='n'>Name</label><input id='n'></form></body></html>"
LOGIN = "<html><body><h2>Sign in to apply</h2><label for='u'>Email</label><input id='u'><label for='pw'>Password</label><input id='pw' type='password'></body></html>"
CLOSED = "<html><body><h1>Sorry, this job is no longer available.</h1></body></html>"

NO_CONFIRMATION = GOOD_FORM.replace(
    "document.body.innerHTML='<h2>Thank you for applying</h2><p>Your application has been submitted.</p>';", "")

APPLY_BUTTON_FIRST = """
<html><body><h1>Listing</h1><button onclick="document.getElementById('wrap').style.display='block'; this.remove();">Apply now</button>
<div id="wrap" style="display:none">""" + GOOD_FORM.split("<body>")[1].split("</body>")[0] + "</div></body></html>"
