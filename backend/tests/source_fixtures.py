"""Synthetic source payloads (fictional companies) shaped like the real public formats."""

GOOGLE_ALERTS_ATOM = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:idx="urn:atom-extension:indexing">
  <id>tag:google.com,2005:reader/user/000/state/com.google/alerts/111</id>
  <title>Google Alert - Lowongan Admin Marketplace</title>
  <entry>
    <id>tag:google.com,2013:googlealerts/feed:1</id>
    <title type="html">&lt;b&gt;Lowongan&lt;/b&gt; Admin Marketplace PT Contoh Niaga Jakarta Utara</title>
    <link href="https://www.google.com/url?rct=j&amp;sa=t&amp;url=https://karir.contoh.co.id/lowongan/admin-marketplace&amp;ct=ga&amp;cd=1"/>
    <published>{recent}</published>
    <content type="html">Dibutuhkan Admin Marketplace, wajib menguasai Shopee dan Tokopedia. Gaji Rp 5.000.000 - Rp 6.500.000 per bulan.</content>
  </entry>
  <entry>
    <id>tag:google.com,2013:googlealerts/feed:2</id>
    <title type="html">Old post</title>
    <link href="https://www.google.com/url?url=https://example.org/old"/>
    <published>2020-01-01T00:00:00Z</published>
    <content type="html">Lowongan lama</content>
  </entry>
</feed>"""

RSS2 = """<?xml version="1.0"?><rss version="2.0"><channel><title>Loker Feed</title>
<item><title>Social Media Specialist - PT Fiktif Media</title><link>https://jobs.example.com/123?utm_source=rss</link>
<description>&lt;p&gt;Membuat konten Instagram dan TikTok.&lt;/p&gt;</description><pubDate>{recent_rfc}</pubDate></item>
</channel></rss>"""

TELEGRAM_PREVIEW = """<html><body><section class="tgme_channel_history">
<div class="tgme_widget_message_wrap"><div class="tgme_widget_message text_not_supported_wrap js-widget_message" data-post="lokerjkt_test/101">
 <div class="tgme_widget_message_text js-message_text" dir="auto">🔥 LOWONGAN KERJA<br/><br/>Posisi: Admin Marketplace<br/>Perusahaan: PT Contoh Niaga<br/>
 Lokasi: Jakarta Utara<br/>Gaji: 4,5 - 5,5 jt<br/>Status: Kontrak<br/>Kualifikasi:<br/>- Menguasai Shopee & Tokopedia<br/>- Bisa Canva<br/><br/>
 Kirim CV ke hrd@contohniaga.co.id dengan subjek Admin Marketplace</div>
 <div class="tgme_widget_message_footer"><a class="tgme_widget_message_date" href="https://t.me/lokerjkt_test/101"><time datetime="{recent}" class="time">10:00</time></a></div>
</div></div>
<div class="tgme_widget_message_wrap"><div class="tgme_widget_message js-widget_message" data-post="lokerjkt_test/102">
 <div class="tgme_widget_message_text js-message_text">Promo kursus digital marketing diskon 50%! Daftar sekarang.</div>
 <div class="tgme_widget_message_footer"><time datetime="{recent}">11:00</time></div></div></div>
<div class="tgme_widget_message_wrap"><div class="tgme_widget_message js-widget_message" data-post="lokerjkt_test/103">
 <div class="tgme_widget_message_text js-message_text">Dibutuhkan Customer Service Online, kerja dari HP gaji 10 jt, biaya pendaftaran 100rb. Lokasi: Bekasi. Daftar: https://bit.ly/xyz</div>
 <div class="tgme_widget_message_footer"><time datetime="{recent}">12:00</time></div></div></div>
</section></body></html>"""

LEVER_JSON = [
    {"id": "aaa-111", "text": "Marketplace Specialist", "hostedUrl": "https://jobs.lever.co/contoh/aaa-111",
     "applyUrl": "https://jobs.lever.co/contoh/aaa-111/apply", "createdAt": None,
     "categories": {"commitment": "Full-time", "location": "Jakarta, Indonesia", "team": "Commerce"},
     "workplaceType": "hybrid", "descriptionPlain": "Manage Shopee and Tokopedia stores.",
     "lists": [{"text": "Requirements", "content": "<li>Shopee</li><li>Canva</li>"}],
     "salaryRange": {"currency": "IDR", "interval": "per-month-salary", "min": 6000000, "max": 8000000}},
    {"id": "bbb-222", "text": "Engineer", "hostedUrl": "https://jobs.lever.co/contoh/bbb-222",
     "categories": {"commitment": "Full-time", "location": "Singapore"}, "descriptionPlain": "x"},
]

GREENHOUSE_JSON = {"jobs": [
    {"id": 555, "title": "Digital Marketing Associate", "absolute_url": "https://job-boards.greenhouse.io/contoh/jobs/555",
     "location": {"name": "Jakarta, Indonesia"}, "updated_at": "{recent}", "company_name": "Contoh",
     "content": "&lt;p&gt;Run &lt;strong&gt;Facebook Ads&lt;/strong&gt; and Google Ads.&lt;/p&gt;"},
    {"id": 556, "title": "Account Manager", "absolute_url": "https://job-boards.greenhouse.io/contoh/jobs/556",
     "location": {"name": "Manila, Philippines"}, "updated_at": "{recent}", "content": "x"},
]}
