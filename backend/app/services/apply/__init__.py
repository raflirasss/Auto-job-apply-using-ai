"""Browser application engine (Phase 5).

Safety contract (enforced in code, covered by tests):
- never bypass CAPTCHA / login / OTP / identity checks: detect and stop;
- only fill fields mapped to verified profile facts; unknown required fields stop the run;
- never tick legal declarations or consent boxes, never fill sensitive personal data;
- never submit an incomplete form; "submitted" requires on-page confirmation evidence.
"""
