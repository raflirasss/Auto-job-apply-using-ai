# AI Job Hunter

Asisten pencari kerja pribadi: mencari lowongan, menilai kecocokan dengan CV kamu, membuat CV dan surat lamaran khusus, lalu melamar otomatis. Berjalan di komputer kamu sendiri (Windows).

**Apa yang dilakukan aplikasi ini?**

1. **Mencari lowongan** dari Google Alerts, channel Telegram, dan halaman karier perusahaan (Lever/Greenhouse).
2. **Menilai** setiap lowongan: cocok atau tidak dengan CV kamu (skor 0–100).
3. **Membuat CV dan surat lamaran khusus** untuk tiap lowongan (PDF dan Word).
4. **Melamar otomatis** lewat email (kalau lowongan minta "kirim CV ke …") atau lewat form lamaran perusahaan.
5. **Mencatat semua lamaran** supaya kamu bisa memantau statusnya.

> ⚠️ **Penting:** aplikasi hanya memakai data yang benar-benar ada di CV kamu. Aplikasi tidak mengarang pengalaman, skill, atau jawaban. Kalau ada pertanyaan yang tidak bisa dijawab dari profil kamu, proses berhenti dan menunggu kamu.

---

# 📘 Tutorial untuk pemula

Ikuti langkah berikut dari atas ke bawah. Tidak perlu paham pemrograman.

**Daftar isi**

1. [Yang kamu butuhkan](#1-yang-kamu-butuhkan)
2. [Install program pendukung (sekali saja)](#2-install-program-pendukung-sekali-saja)
3. [Download aplikasi](#3-download-aplikasi)
4. [Menjalankan aplikasi](#4-menjalankan-aplikasi)
5. [Login ke dashboard](#5-login-ke-dashboard)
6. [Upload CV dan lengkapi profil](#6-upload-cv-dan-lengkapi-profil)
7. [Atur preferensi pekerjaan](#7-atur-preferensi-pekerjaan)
8. [Atur sumber lowongan](#8-atur-sumber-lowongan)
9. [Atur email untuk melamar otomatis](#9-atur-email-untuk-melamar-otomatis)
10. [Cari lowongan pertama kali](#10-cari-lowongan-pertama-kali)
11. [Melihat hasil penilaian](#11-melihat-hasil-penilaian)
12. [Membuat CV dan surat lamaran](#12-membuat-cv-dan-surat-lamaran)
13. [Melamar](#13-melamar)
14. [Menyalakan mode otomatis harian](#14-menyalakan-mode-otomatis-harian)
15. [Memantau lamaran](#15-memantau-lamaran)
16. [Rutinitas sehari-hari](#16-rutinitas-sehari-hari)
17. [Masalah yang sering terjadi](#17-masalah-yang-sering-terjadi)
18. [Pertanyaan umum (FAQ)](#18-pertanyaan-umum-faq)

## 1. Yang kamu butuhkan

- Komputer **Windows 10 atau 11** dan koneksi internet.
- **CV** dalam format **PDF atau Word (.docx)**. PDF harus berisi teks (bisa diblok/di-copy), **bukan hasil foto/scan**.
- Sekitar **3 GB** ruang kosong di hard disk.
- Opsional: akun **Gmail** (untuk melamar lewat email) dan akun **Telegram**.

## 2. Install program pendukung (sekali saja)

Aplikasi ini butuh dua program gratis: **Python** dan **Node.js**.

**2.1 Install Python**

1. Buka https://www.python.org/downloads/ lalu klik tombol kuning **Download Python 3.x.x** (versi 3.12 atau lebih baru).
2. Buka file yang terdownload.
3. **PENTING:** di jendela pertama, **centang kotak "Add python.exe to PATH"** di bagian bawah.
4. Klik **Install Now**, tunggu sampai selesai, lalu klik **Close**.

**2.2 Install Node.js**

1. Buka https://nodejs.org/ lalu klik tombol versi **LTS**.
2. Buka file yang terdownload, lalu klik **Next** terus sampai **Install**, lalu **Finish**. Pengaturan bawaan sudah benar.

**2.3 Cek hasilnya**

1. Tekan tombol **Windows**, ketik `cmd`, lalu tekan **Enter**.
2. Ketik perintah berikut satu per satu, lalu tekan Enter:
   ```
   python --version
   node --version
   ```
3. Kalau muncul nomor versi (misalnya `Python 3.13.1` dan `v22.12.0`), berarti berhasil.
4. Kalau muncul *"is not recognized"* atau Microsoft Store terbuka, **restart komputer** lalu coba lagi. Kalau masih gagal, install ulang Python dan pastikan kotak *"Add python.exe to PATH"* dicentang.

## 3. Download aplikasi

1. Buka https://github.com/raflirasss/Auto-job-apply-using-ai
2. Klik tombol hijau **Code**, lalu **Download ZIP**.
3. Buka folder **Downloads**, klik kanan file ZIP, pilih **Extract All…**, lalu **Extract**.
4. Pindahkan folder hasil extract ke tempat yang mudah dicari, misalnya **Desktop**.

> Sudah biasa pakai Git? Cukup jalankan `git clone https://github.com/raflirasss/Auto-job-apply-using-ai.git`.

## 4. Menjalankan aplikasi

1. Buka folder aplikasi, lalu **klik dua kali file `start.bat`**.
2. Kalau muncul peringatan biru *"Windows protected your PC"*, klik **More info**, lalu **Run anyway**. Ini normal untuk file yang didownload dari internet.
3. Jendela hitam akan terbuka. **Pertama kali, prosesnya 5–15 menit** karena semua komponen didownload. Tunggu saja.
4. Di awal muncul kotak hijau seperti ini:
   ```
   File .env dibuat. Password dashboard kamu:  Ab3dEf7hJk9m
   ```
   **Catat password ini**, karena dipakai untuk login.
5. Kalau sudah siap, muncul tulisan `AI Job Hunter sudah jalan:  http://localhost:3000` dan browser terbuka otomatis.

> ⚠️ **Jangan tutup jendela hitam itu** selama memakai aplikasi. Untuk mematikan aplikasi, klik jendela hitam lalu tekan **Ctrl + C**.

Lain kali cukup klik dua kali `start.bat` lagi. Prosesnya sekitar 30 detik.

**Lupa password?** Buka file `.env` di folder aplikasi dengan Notepad (klik kanan, lalu **Open with**, lalu **Notepad**) dan lihat baris `DASHBOARD_PASSWORD=`. Kamu bisa mengganti password di situ (minimal 8 karakter), lalu jalankan ulang `start.bat`.

## 5. Login ke dashboard

1. Kalau browser belum terbuka, buka **http://localhost:3000** di Chrome atau Edge.
2. Masukkan password dari langkah 4, lalu klik **Sign in**.
3. Menu di sebelah kiri:

| Menu | Fungsinya |
|---|---|
| **Overview** | Ringkasan: jumlah lowongan, lamaran, interview |
| **Job Discovery** | Daftar lowongan yang ditemukan |
| **Applications** | Daftar lamaran dan statusnya |
| **AI Analysis** | Skor kecocokan tiap lowongan |
| **Documents** | CV asli serta CV dan surat lamaran yang dibuat |
| **Agent Control** | Menyalakan/mematikan mode otomatis |
| **Settings** | Semua pengaturan |

Ikon bulan/matahari di kiri bawah untuk mode gelap/terang. Ikon lonceng 🔔 untuk notifikasi.

## 6. Upload CV dan lengkapi profil

Ini langkah **paling penting**: semua penilaian dan dokumen dibuat dari profil ini.

1. Klik **Settings**, lalu tab **Candidate profile**.
2. Klik **Upload CV (PDF or DOCX)** dan pilih file CV kamu. Profil terisi otomatis: nama, kontak, pendidikan, pengalaman, dan skill.
3. **Periksa setiap bagian** dan perbaiki kalau ada yang salah baca.
4. Di atas muncul kotak kuning berisi data yang tidak ada di CV. Yang bertanda **Required** wajib diisi:
   - **Current domicile**: kota tempat tinggal (misalnya *Jakarta Timur*).
   - **Expected monthly salary (IDR)**: gaji yang diharapkan per bulan.
   - **Availability / start date**: kapan bisa mulai kerja (misalnya *immediately*).
   - **Legally allowed to work in Indonesia**: pilih *Yes* kalau kamu WNI.
5. Disarankan juga mengisi **Employment type** di setiap pengalaman kerja, serta **Certifications & projects** kalau ada.
6. Di **Target job categories**, centang jenis pekerjaan yang kamu incar. Hanya kategori yang didukung isi CV yang bisa dicentang.
7. Klik **Save & confirm** di bagian bawah layar. Kalau berhasil, muncul label hijau **Confirmed**.

> ⚠️ Aplikasi tidak akan menilai lowongan atau membuat dokumen sebelum profil di-**confirm**.

## 7. Atur preferensi pekerjaan

**Settings**, lalu tab **Job preferences**:

- **Accepted locations**: kota yang kamu mau (sudah terisi Jabodetabek).
- **Work arrangement**: onsite / hybrid (remote dimatikan secara bawaan).
- **Employment types**: full time / contract / dll.
- **Minimum monthly salary (IDR)**: lowongan dengan gaji di bawah ini otomatis ditolak.
- **Auto-apply threshold** (bawaan 85) dan **Review threshold** (bawaan 70).
- **Daily application limit**: maksimal lamaran otomatis per hari (bawaan 10).
- **Auto-apply**: nyalakan kalau mau aplikasi melamar sendiri.

Klik **Save preferences**.

## 8. Atur sumber lowongan

Buka **Settings**, lalu tab **Sources & email**. Ada 3 sumber; boleh pakai satu, dua, atau semuanya.

### 8.1 Google Alerts (paling disarankan)

1. Buka https://www.google.com/alerts (login dengan akun Google).
2. Ketik kata kunci, misalnya `"lowongan admin marketplace" jakarta`.
3. Klik **Show options** (Tampilkan opsi). Di **Deliver to** (Kirim ke), pilih **RSS feed**, lalu klik **Create Alert** (Buat Notifikasi).
4. Di daftar alert, klik **ikon RSS** (ikon oranye kecil) di sebelah alert tadi. Halaman baru terbuka. **Copy alamat dari address bar browser.**
5. Kembali ke dashboard: nyalakan **Use RSS feeds**, klik **Add feed**, isi **Name** (misalnya *Admin Marketplace*), lalu tempel alamat tadi di kolom sebelahnya.
6. Ulangi untuk posisi lain (**satu alert per posisi** paling bagus). Contoh kata kunci:
   ```
   "lowongan digital marketing" jakarta
   "lowongan social media specialist" jakarta
   "lowongan content creator" jakarta
   ```
7. Klik **Save sources** di bawah.

> Google Alerts hanya memberi judul, link, dan ringkasan singkat. Untuk detail lengkap, buka link lowongannya.

### 8.2 Channel Telegram

1. Cari channel loker yang **masih aktif** di Telegram (misalnya cari "loker jakarta"). Pastikan postingannya baru.
2. Lihat **username** channel (diawali `@`, ada di info channel).
3. Di dashboard, nyalakan **Read Telegram job channels**, ketik `@namachannel` di **Public channels**, lalu tekan **Enter**. Ulangi untuk channel lain.
4. **Read method**: pilih **Public web preview (t.me/s/…)**. Ini tidak perlu login.
5. Klik **Save sources**.

**(Opsional) Hubungkan akun Telegram** supaya hasil lebih lengkap:

1. Buka https://my.telegram.org, login dengan nomor HP Telegram, lalu klik **API development tools**. Isi form singkat (App title/Short name bebas, misalnya *jobhunter*), lalu klik **Create application**.
2. Catat **api_id** dan **api_hash**.
3. Di dashboard isi **api_id**, **api_hash**, dan **Phone** (format `+62812…`), lalu klik **Send login code**.
4. Masukkan kode yang dikirim ke aplikasi Telegram kamu (dan password verifikasi dua langkah kalau ada), lalu klik **Connect**.
5. Ubah **Read method** menjadi **Telegram API (your account)**, lalu **Save sources**.

> 🔒 Aplikasi hanya **membaca** channel yang kamu pilih. Aplikasi tidak pernah mengirim pesan, posting, atau bergabung ke grup.
>
> ⚠️ Waspada lowongan palsu. Aplikasi memberi tanda **WARNING** kalau postingan meminta biaya pendaftaran, deposit, atau "langsung kerja tanpa interview".

### 8.3 Halaman karier perusahaan (Lever / Greenhouse)

Kalau alamat halaman karier perusahaan incaran berbentuk:
- `jobs.lever.co/`**namaperusahaan**: masukkan **namaperusahaan** ke **Lever companies**;
- `job-boards.greenhouse.io/`**namaperusahaan**: masukkan ke **Greenhouse companies**.

Nyalakan **Read company career boards**, lalu **Save sources**. Hanya lowongan di Indonesia atau kota pilihan kamu yang diambil. Kalau tidak tahu perusahaan mana yang memakai Lever/Greenhouse, matikan saja bagian ini.

**Check sources every (hours)**: seberapa sering sumber dicek (bawaan setiap 6 jam, saat mode otomatis menyala).

## 9. Atur email untuk melamar otomatis

Supaya aplikasi bisa mengirim lamaran ke lowongan yang bilang "kirim CV ke hrd@…".

**9.1 Buat App Password Gmail** (Gmail tidak mengizinkan aplikasi memakai password biasa):

1. Aktifkan **Verifikasi 2 Langkah**: buka https://myaccount.google.com/security, lalu **2-Step Verification**.
2. Buka https://myaccount.google.com/apppasswords, isi nama (misalnya `Job Hunter`), lalu klik **Create**.
3. Muncul **16 huruf** (misalnya `abcd efgh ijkl mnop`). **Copy kode ini**, karena hanya muncul sekali.

**9.2 Masukkan ke dashboard:** **Settings**, lalu **Sources & email**, lalu bagian paling bawah **Email applications (your mailbox)**:

1. Isi **Your email address** (Gmail kamu), **Sender name** (nama lengkap), dan **App password** (16 huruf tadi).
2. **SMTP server** `smtp.gmail.com`, **Port** `465`, dan **SSL** menyala. Semuanya sudah terisi otomatis.
3. Klik **Save**, lalu **Test login**. Kalau muncul *"Login to the mail server succeeded"*, berarti berhasil. Tes ini tidak mengirim email apa pun.

## 10. Cari lowongan pertama kali

1. Buka menu **Job Discovery**, lalu klik **Check sources now**.
2. Tunggu sampai tulisan **Checking…** selesai (biasanya kurang dari 1 menit).
3. Muncul laporan per sumber (misalnya *"12 fetched, 10 new"*) dan daftar lowongan. Label **apply by email** artinya lowongan itu bisa dilamar lewat email.

Kalau hasilnya 0, baca pesan di bawah nama sumber. Misalnya *"no recent posts"* berarti channel Telegram itu sudah tidak aktif. Mau menambah lowongan sendiri? Klik **Add manually**.

## 11. Melihat hasil penilaian

1. Buka menu **AI Analysis**, lalu klik **Analyse new**.
2. Lowongan dikelompokkan menjadi:

| Kelompok | Artinya |
|---|---|
| **Auto-apply eligible** | Skor ≥ 85 dan semua syarat jelas. Boleh dilamar otomatis. |
| **Review queue** | Skor 70–84, atau gaji/lokasi tidak jelas. Sebaiknya kamu cek dulu. |
| **Skipped** | Skor di bawah 70. Kurang cocok. |
| **Rejected** | Gagal syarat wajib: gaji terlalu kecil, lokasi tidak sesuai, full remote, skill wajib tidak punya, dll. |

3. Klik sebuah lowongan untuk melihat **Score breakdown** (skill 35%, pengalaman 25%, judul 15%, pendidikan 10%, lokasi 10%, gaji 5%), **Matching skills** (hijau), **Missing skills** (merah), dan **Concerns**.

## 12. Membuat CV dan surat lamaran

1. Di detail lowongan, buka tab **Documents**.
2. Pilih **Template** (Classic / Modern) dan **Language**, lalu klik **Generate documents**.
3. Download **CV** dan **Cover letter** (PDF dan Word), teks **Email**, serta **Form answers**.

Isi CV tetap sama dengan CV asli kamu. Yang berubah hanya urutannya: skill dan pengalaman yang relevan dengan lowongan tampil lebih dulu. Tidak ada yang ditambah-tambahkan. Semua versi tersimpan di menu **Documents**.

## 13. Melamar

Di detail lowongan, buka tab **Apply**. Tombol yang muncul tergantung jenis lowongannya:

| Tombol | Kapan muncul | Apa yang terjadi |
|---|---|---|
| **Apply by email** | Lowongan punya alamat email lamaran | CV dan surat lamaran dikirim dari Gmail kamu. Ada konfirmasi dulu. |
| **Auto apply** | Lowongan punya form online | Browser mengisi dan mengirim form sendiri. Berhenti kalau ada CAPTCHA, login, atau pertanyaan yang tidak bisa dijawab. |
| **Assisted apply** | Lowongan punya form online | Browser terbuka dan data terisi otomatis, tapi **kamu sendiri yang cek dan klik kirim**. |

- Lamaran lewat **email** atau **auto apply** yang berhasil: status otomatis menjadi **Applied**.
- Lamaran lewat **assisted apply**: setelah kamu kirim, buka tab **Status**, pilih **Applied**, isi kolom konfirmasi (misalnya *"email konfirmasi 12 Nov"*), lalu klik **Update status**.

> ⚠️ Aplikasi **tidak pernah** membobol CAPTCHA, mengisi data sensitif (NIK, agama, tanggal lahir, rekening…), mencentang pernyataan atas nama kamu, menebak jawaban, atau menganggap lamaran terkirim tanpa bukti. Kalau menemui hal itu, prosesnya berhenti dan status menjadi **Pending action** beserta penjelasannya.

## 14. Menyalakan mode otomatis harian

1. Pastikan di **Settings → Job preferences**, **Auto-apply** menyala.
2. Buka **Agent Control**, lalu klik **Start agent**.

Mulai sekarang, **setiap hari jam 08:00 WIB** (dan cek sumber tiap 6 jam), aplikasi otomatis mencari lowongan baru, menilai, membuat dokumen, melamar sampai batas harian, lalu mengirim ringkasan ke ikon 🔔.

Tombol lain: **Pause** / **Resume** (berhenti sementara), dan **Run now** (jalankan sekarang tanpa menunggu jam 08:00).

> ⚠️ Mode otomatis **hanya berjalan selama jendela `start.bat` terbuka dan komputer menyala**. Kalau komputer mati jam 08:00, proses tetap jalan asalkan aplikasi dinyalakan paling lambat 1 jam setelahnya. Kalau lebih dari itu, proses hari itu dilewati.

## 15. Memantau lamaran

Buka menu **Applications**:
- tampilan **Table** atau **Kanban** (New, Qualified, Pending action, Applied, Interview, Closed);
- kotak pencarian dan filter status;
- klik sebuah lamaran, buka tab **Status**, lalu ubah statusnya saat ada kabar: **Interview**, **Assessment**, **Rejected**, **Accepted**.

Menu **Overview** menampilkan ringkasan angka dan tingkat keberhasilan.

## 16. Rutinitas sehari-hari

1. Klik dua kali `start.bat` (kalau belum jalan).
2. Cek ikon 🔔 untuk ringkasan hari ini.
3. **Applications**: selesaikan yang berstatus **Pending action**.
4. **AI Analysis**, lalu **Review queue**: lamar sendiri yang menurut kamu menarik.
5. Update status kalau ada panggilan interview atau penolakan.

## 17. Masalah yang sering terjadi

| Masalah | Solusi |
|---|---|
| `start.bat` langsung tertutup / *Python belum terpasang* | Install Python dari https://www.python.org/downloads/ dan **centang "Add python.exe to PATH"**. Restart komputer. |
| *Node.js belum terpasang* | Install Node.js versi LTS dari https://nodejs.org/, lalu restart komputer. |
| Instalasi paket gagal | Cek koneksi internet, lalu klik `start.bat` lagi. |
| *Port 3000/8000 dipakai program lain* | Tutup program yang disebut di pesan error, lalu klik `start.bat` lagi. |
| Dashboard 500 / *backend server is not running* | Pastikan jendela hitam terbuka. Tutup semua, lalu klik `start.bat` lagi. Script baru akan membersihkan proses lama otomatis. |
| Lupa password | Buka `.env` dengan Notepad, lihat/ganti `DASHBOARD_PASSWORD=` (minimal 8 karakter). Restart aplikasi. |
| Login salah 5 kali | Tunggu 5 menit. |
| CV tidak terbaca / profil kosong | CV mungkin hasil scan/foto. Gunakan PDF hasil Save as PDF dari Word/Canva, atau file `.docx`. |
| Tidak bisa **Save & confirm** | Masih ada pertanyaan **Required** yang kosong di kotak kuning. |
| **Test login** Gmail gagal | Pakai **App Password 16 huruf**, bukan password Gmail biasa. Verifikasi 2 Langkah harus aktif. |
| Telegram *no recent posts* | Channel tidak aktif atau privat. Ganti dengan channel yang masih aktif. |
| Google Alerts kosong | Alert baru bisa butuh waktu. Coba kata kunci yang lebih umum. |
| Lamaran berhenti dengan CAPTCHA/login/unresolved fields | Ini disengaja demi keamanan. Gunakan **Assisted apply** dan selesaikan sendiri. |

## 18. Pertanyaan umum (FAQ)

**Apakah aplikasi memakai AI berbayar?**

Tidak wajib. Penilaian, CV, dan surat lamaran dibuat dengan aturan tetap tanpa biaya. AI hanya opsional untuk **Generate AI explanation** dan harus diatur di **Settings → AI & scheduler**.

**Apakah data saya aman?**

CV, profil, dan lamaran tersimpan di folder `data/` di komputer kamu. Password email, session Telegram, dan API key disimpan terenkripsi. Jangan commit `.env` atau `data/`.

**Apakah aplikasi melamar ke semua lowongan otomatis?**

Tidak. Hanya lowongan dengan skor tinggi (`auto_apply_eligible`), lolos hard filter, dokumen tersedia, dan metode lamaran yang diizinkan. Email otomatis perlu SMTP. Form otomatis berhenti pada CAPTCHA, login, OTP, data sensitif, atau pertanyaan yang tidak dikenal.

**Apakah CV asli diubah?**

Tidak. CV asli tidak pernah ditimpa. Dokumen khusus lowongan disimpan sebagai versi baru.

**Bagaimana update aplikasi?**

Download ZIP terbaru dari GitHub, lalu salin `data/` dan `.env` dari folder lama ke folder baru. Jalankan `start.bat`.

**Bagaimana menghapus data?**

Tutup aplikasi, lalu hapus folder `data/` dan file `.env`. Saat `start.bat` dijalankan lagi, semuanya mulai dari awal.

## Dokumentasi teknis

<!--TUTORIAL-END-->

Di bawah ini detail arsitektur, API, keamanan, testing, dan deployment untuk developer.

## Layout

```
backend/            FastAPI app (Python)
  app/api/          HTTP routes (auth, candidate, jobs, documents, apply, agent, settings, dashboard)
  app/core/         settings, auth/session, encryption, PII-redacting logging
  app/models/       SQLAlchemy models
  app/schemas/      Pydantic schemas
  app/services/     cv_* (import), matching/ (Phase 3), documents/ (4), apply/ (5), agent/ (6), notifications
  app/sources/      JobSourceAdapter interface + registry (portal adapters plug in here)
  migrations/       Alembic migrations
  scripts/          import_cv.py, smoke_test.py + smoke_phases.py (live end-to-end checks, self-cleaning)
  tests/            pytest suite (synthetic fictional CVs only)
frontend/           Next.js 16 + TypeScript + Tailwind v4, shadcn-style components
config/             preferences.json, sources.json, scheduler.json (mirrors of DB settings)
                    candidate.json is generated from your CV and git-ignored
data/               SQLite DB (local dev), original CVs — git-ignored, contains personal data
```

## Local development (Windows)

Prerequisites: Python 3.12+, Node 20+. PostgreSQL optional for local dev (SQLite fallback).

```powershell
# 1. Configure secrets (once)
Copy-Item .env.example .env   # then set APP_SECRET_KEY (>=32 chars) and DASHBOARD_PASSWORD (>=8)

# 2. Backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The browser only talks to Next.js; `/api/*` is rewritten to the backend (`BACKEND_URL`, default `http://127.0.0.1:8000`) so the session cookie stays first-party.

### Importing a CV

Dashboard: **Settings → Candidate profile → Upload CV**, or CLI:

```powershell
cd backend
.venv\Scripts\python -m scripts.import_cv "C:\path\to\cv.pdf"
```

The original file is stored once under `data/cv/originals/<sha256>.pdf` and never overwritten. Each import creates a new **unconfirmed** profile version; earlier versions stay in `candidate_profile_versions`. The profile can only be confirmed when no critical question is open.

### Tests

```powershell
cd backend
.venv\Scripts\python -m pytest            # unit + API tests
.venv\Scripts\python -m scripts.smoke_test    # requires both servers running
.venv\Scripts\python -m scripts.smoke_phases  # phases 3-6 end to end; removes its test data afterwards

cd frontend
npx next typegen; npx tsc --noEmit; npx eslint .; npm run build
```

## Docker

```powershell
# .env must also contain POSTGRES_PASSWORD
docker compose up --build    # dashboard on http://localhost:3000 (bound to 127.0.0.1)
```

The backend runs `alembic upgrade head` on start and uses PostgreSQL. `./data` and `./config` are mounted volumes.

## Security notes

- Single-owner dashboard: password login → HMAC-signed, httpOnly, SameSite=strict session cookie (12 h default). Five failed logins lock a client for 5 minutes.
- All API routes except `/api/health` and `/api/auth/login` require auth; the Next.js proxy only handles redirects.
- AI API keys entered in the dashboard are Fernet-encrypted (key derived from `APP_SECRET_KEY`) and only shown masked. Environment keys are never written to the DB.
- Logs pass through a redaction filter (emails, phone numbers, tokens, keys).
- `.env`, `data/`, `config/candidate.json` are git-ignored. Changing `APP_SECRET_KEY` invalidates sessions and stored encrypted keys.

## Ingestion rules (all sources)

`backend/app/services/job_ingestion.py`, `job_normalize.py`:

- URLs are normalised (https, lowercase host, no trailing slash, tracking params such as `utm_*`, `ref`, `gh_src` removed). `jobstreet.com` URLs are rejected: JobStreet was removed as a source because its robots.txt and Cloudflare block automated access (checked 2026-11-11) and SEEK's API is for employers only.
- A listing is a duplicate when the canonical URL **or** `(source, external_id)` matches (e.g. `telegram:<channel>/<post>`, `lever:<company>:<id>`); the existing row is updated instead of adding one. Refreshes never replace a longer description or a disclosed salary with poorer data; manual edits always overwrite.
- Salary: structured API values are used as-is; text labels are parsed only when clearly IDR (`Rp`, `IDR`, or `jt/juta`) with a period, or a `jt` amount (read as monthly). Annual/weekly/daily are converted to monthly. Anything else stays **undisclosed**.
- Each new listing gets a tracking record with status `discovered`.

## Matching engine (Phase 3)

Code: `backend/app/services/matching/`. Everything that decides is deterministic Python; an LLM is used only to write optional prose.

| Component | Weight | How it is scored |
|---|---|---|
| Technical skills | 35% | Skills detected in the listing (EN + ID vocabulary) vs. profile skills. Mandatory skills count 2×, "nice to have" 0.5×. |
| Work experience | 25% | Half: years in profile vs. stated minimum (fresh-graduate listings = full marks). Half: share of past roles that mention the listing's skills. |
| Job title | 15% | Title category vs. your selected target categories (100) / categories supported by your CV (85) / unsupported (10). |
| Education | 10% | Lowest level mentioned (e.g. "D3/S1" → D3) vs. your highest degree; not-yet-completed degree = 75. |
| Location & arrangement | 10% | Greater-Jakarta aliases (Jaksel, South Jakarta, BSD, Cikarang, SCBD…). Unknown = 60. |
| Salary | 5% | Range ≥ minimum = 100; straddles minimum = 70; undisclosed = 0. |

**Hard filters (reject regardless of score):** disclosed salary whose maximum is below the minimum; location outside the list; fully remote (also detected from the description) while remote is disabled; work arrangement or employment type not in preferences; mandatory skills missing from the profile; mandatory education not met; experience below half the stated years; job title in a category the CV does not support; already applied.

**Recommendation:** any hard-filter failure → `reject`. Score ≥ auto-apply threshold (85) **and** salary, location and arrangement all verified → `auto_apply_eligible`. Score ≥ review threshold (70), or ≥ 85 but with something unverified → `review` (undisclosed-salary jobs go to `skip` if that review queue is disabled). Otherwise → `skip`.

The engine sets application status only while it is `discovered/analyzed/qualified/rejected`; it never overrides a status you set. Re-importing a listing clears its old analysis. Analysis requires a **confirmed** profile.

**AI explanation (optional):** `POST /api/jobs/{id}/analyze {"with_ai": true}` calls `{AI_BASE_URL}/chat/completions` (OpenAI-compatible) with the engine result, the job text, and an anonymised profile (no name, email, phone, website or domicile). The reply is stored as text only and never parsed back into the decision.

**Manual status updates:** marking a job `applied` requires your own confirmation text (e.g. the confirmation email date); interview/assessment/accepted require `applied` first.

## Sources and automatic discovery

JobStreet and its capture/browser scraper have been removed. The app never scrapes a portal that blocks automation.

**Google Alerts RSS:** go to `google.com/alerts`, create alerts such as `"lowongan admin marketplace" jakarta`, Show options → **Deliver to: RSS feed**, then add each feed URL in Settings → Sources & email. The app reads the feed and keeps the linked page as a summary-only listing; it does not scrape the linked site.

**Telegram:** add public `@channel` usernames in Settings. Public preview mode uses `https://t.me/s/<channel>` (read-only). Recommended API mode: create an app at `my.telegram.org` → API development tools, connect your own Telegram account in Settings with the code Telegram sends. The API session is encrypted. The app only reads chosen channels; it never joins, posts, messages or broadcasts. Telegram's official FAQ says bots receive channel messages only where they are members; using your own account is required for arbitrary public channels. Scam markers (fees, deposits, "no interview") are flagged.

**Company APIs:** add company board tokens in Settings → Sources & email. Lever public endpoint: `https://api.lever.co/v0/postings/<company>?mode=json`. Greenhouse public endpoint: `https://boards-api.greenhouse.io/v1/boards/<company>/jobs?content=true`. These APIs are designed to publish jobs; the public GET endpoints need no key. Applications can only be submitted where the employer's application policy permits it. Lever's POST application endpoint needs an API key generated by that employer's Super Admin, so this personal app does not pretend it can submit to arbitrary Lever boards.

The agent fetches enabled sources every configured interval (default 6 hours) and at the daily run. It respects robots.txt, identifies itself, rate-limits requests, stops on 403/429, and never rotates IPs or bypasses protections. New rows show source, source notes and apply method.

## Documents (Phase 4)

`backend/app/services/documents/`. Content comes only from the confirmed profile: job keywords reorder skills, skill groups and bullets and fill the "Relevant skills" line with skills **you already have**; nothing is added or rephrased. Profile sentences are quoted verbatim, so documents default to the profile's language (choose EN/ID per generation; the letter frame is translated, your bullets are not). Two single-column ATS templates (`classic`, `modern`), real selectable text, no tables/images in DOCX. Each generation is a new version in `data/documents/app_<id>/v<n>/` (CV PDF/DOCX, cover letter PDF/DOCX, `application_email.txt`, `form_answers.json`); answers without a verified fact are marked `REQUIRES YOUR INPUT`.

## Application engine (Phase 5)

`backend/app/services/apply/`. Flow: open page → closed/already-applied check → CAPTCHA / login / OTP detection → open the form (one clear "Apply" button) → detect fields → map to verified facts → fill/upload → (auto mode only) validate → submit → require on-page confirmation text.

Always enforced:

- CAPTCHA, anti-bot walls, login and OTP are **detected and stop the run**; they are never bypassed. The persistent browser profile (`data/browser_profile/`) lets *you* log in once yourself; the app never sees your password.
- Sensitive fields (NIK/KTP, NPWP, bank, religion, date of birth, gender, photo, passwords…), legal declarations/consent checkboxes, salary history and unknown free-text questions are never filled; if required, the run stops (auto) or lists them for you (assisted).
- Yes/No answers are only chosen when exactly one option matches your recorded fact.
- `applied` is set only with confirmation evidence (page text in auto mode, your own confirmation text otherwise). No confirmation → `pending_action`, never "success".
- Failures save a viewport-only screenshot (`data/screenshots/`); stored attempt logs contain field *labels* only, never values.
- One browser automation at a time; duplicates and already-applied jobs are refused.

**Apply methods** (`policy.py`), tried in this order by the agent for `auto_apply_eligible` jobs when `auto_apply` is on, within `daily_application_limit`:

- **email** – the listing names an address ("kirim CV ke hrd@…", typical on Telegram). Sent from your own mailbox via SMTP with the latest CV and cover letter PDFs. Recorded as applied only after the mail server accepts the message; a job is never emailed twice.
- **auto** – unattended browser submission on the employer's own form. Not offered for hosts that block automation (JobStreet, LinkedIn, Indeed, Glints).
- **assisted** – browser pre-fills verified fields, you review and submit. Always available as a fallback for any form.

Telegram posts and Google redirect links are not forms; such jobs can only be applied to by email (if an address is given) or by you.

## Scheduler & notifications (Phase 6)

`backend/app/services/agent/`. APScheduler runs inside the backend (`ENABLE_SCHEDULER=true`) with a cron trigger at the configured time in Asia/Jakarta. Guarantees: one run at a time (APScheduler `max_instances=1` plus a DB check covering manual runs and multiple processes); per-day idempotency keys; runs left `running` by a crash are marked failed on startup (heartbeat timeout 30 min); failed scheduled runs retry with exponential backoff (60 s, 120 s, 240 s… up to `max_retries`); pause/resume/start from Agent Control. Discovery steps that have no permitted adapter are reported as skipped, not faked.

Notifications are always stored for the dashboard (bell icon). Set `NOTIFY_WEBHOOK_URL` to also POST `{"title","body","level","content"}` to a webhook (Discord-compatible `content` field).

## Limitations

- Google Alerts gives a title/snippet/link, not a guaranteed full job description. Open the linked page yourself if you need more context; the app does not scrape it automatically.
- Telegram posts are unstructured. Unknown salary, company, location or questions stay empty; scam indicators are warnings, not proof.
- Lever and Greenhouse APIs publish jobs, but arbitrary candidate submission is not available: Lever requires the employer's API key; Greenhouse requires the employer's Job Board API key for POST. The app uses public GET discovery and auto-applies only on employer forms where the site permits it.
- Source feeds/APIs may return old, closed or duplicate listings; lookback and stable IDs reduce this, but status must be checked before applying.
- Email applications use the generated email text; listings that ask for a specific subject line or extra documents (KTP, ijazah…) need your attention. Check the source note before enabling auto-apply for a channel.
- Form detection is heuristic. Unusual multi-step forms or custom widgets may stop with "no form detected" / "unresolved fields"; that is the safe failure mode.
- CV parsing has no OCR; certifications/projects are entered manually. Skill vocabulary is ~60 skills (profile skills always count).
- AI explanations were tested against a mocked provider only; configure `AI_*` to use a real one.
- Assisted apply needs a desktop session (visible browser). In Docker the browser is headless, so use assisted apply from the local Windows install.
- Login throttling is in-memory. Docker files were written but not executed here (Docker not installed).
