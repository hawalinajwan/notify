# 🔔 PENS Notifikasi → Discord

Script otomatis yang mengambil notifikasi dari `ethol.pens.ac.id` dan mengirimkannya ke Discord via webhook, dijalankan otomatis setiap 30 menit menggunakan **GitHub Actions** (gratis).

---

## 📁 Struktur File

```
├── notif_to_discord.py          # Script utama
├── .github/
│   └── workflows/
│       └── notifikasi.yml       # Jadwal GitHub Actions
└── sent_ids.json                # Dibuat otomatis (tracking notif terkirim)
```

---

## 🚀 Cara Setup

### 1. Buat Repository GitHub
- Buat repo baru di GitHub (boleh private)
- Upload semua file ini

### 2. Ambil Cookie & Token dari Browser
1. Buka `ethol.pens.ac.id` → login
2. Buka **DevTools** (F12) → tab **Network**
3. Refresh halaman, klik request ke `/api/notifikasi/...`
4. Tab **Headers** → salin nilai:
   - **Cookie** (panjang, mulai dari `hakAktif=mahasiswa; ...`)
   - **Token** (JWT panjang, mulai dari `eyJ...`)

### 3. Tambahkan GitHub Secrets
Di repo GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name   | Nilai                        |
|---------------|------------------------------|
| `ETHOL_COOKIE`| Nilai Cookie dari browser    |
| `ETHOL_TOKEN` | Nilai Token dari browser     |

### 4. Aktifkan GitHub Actions
- Pergi ke tab **Actions** di repo
- Klik **"I understand my workflows, go ahead and enable them"**
- Selesai! Script akan jalan otomatis setiap 30 menit ✅

### 5. Test Manual
- Tab **Actions** → pilih workflow **"Cek Notifikasi PENS → Discord"**
- Klik **"Run workflow"** → **"Run workflow"**
- Lihat log apakah berhasil

---

## ⚠️ Catatan Penting

- **Token JWT expired** → Kalau dapat error 401/403, login ulang di browser dan update secret `ETHOL_TOKEN` dan `ETHOL_COOKIE`
- **GitHub Actions gratis** untuk repo public, dan untuk repo private ada batas 2000 menit/bulan (cukup untuk jalan tiap 30 menit)
- Notifikasi yang sudah dikirim **tidak akan dikirim ulang** berkat sistem cache `sent_ids.json`

---

## 🎨 Tampilan di Discord

Notifikasi akan muncul sebagai embed berwarna:
- 🔵 **Biru** → Info
- 🟡 **Kuning** → Warning  
- 🔴 **Merah** → Danger/Error
- 🟢 **Hijau** → Success
- 🟣 **Ungu** → Lainnya
