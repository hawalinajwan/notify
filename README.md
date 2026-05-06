# 🔔 Web Notifikasi → Discord & Kalender

Otomatis monitoring notifikasi dari **ETHOL PENS** dan kirim ke Discord + GitHub Gist (Kalender).

## 📋 Fitur

- ✅ **Monitoring Notifikasi Real-time** - Cek notifikasi setiap 60 detik
- 🎯 **Smart Filtering** - Hanya kirim notifikasi baru yang belum dikirim
- 💬 **Discord Integration** - Embed messages dengan kategori & warna berbeda
- 📅 **Auto Calendar** - Simpan deadline tugas ke GitHub Gist (format `.ics`)
- 🚨 **Absensi Alert** - Mention `@everyone` untuk notifikasi absensi
- 📊 **Data Efficient** - Optimasi transfer data untuk VPS dengan quota terbatas
- 🔒 **Secure** - Semua kredensial di `.env` file

## 🚀 Setup

### 1. Clone & Install Dependencies

```bash
cd /Users/xxx/notify
pip install -r requirements.txt
```

### 2. Buat `.env` File

```bash
cp .env.example .env
```

Edit `.env` dengan nilai sesuai:

```env
# ETHOL PENS
ETHOL_COOKIE=your_cookie_here
ETHOL_TOKEN=your_token_here

# Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy

# GitHub Gist (untuk kalender)
GIST_ID=gist_id_anda
GIST_TOKEN=github_personal_token
```

### 3. Jalankan Script

```bash
python notif_to_discord.py
```

Atau dengan `nohup` untuk background:

```bash
nohup python notif_to_discord.py > notif.log 2>&1 &
```

## 🔑 Cara Mendapat Credentials

### ETHOL Cookie & Token

1. Buka https://ethol.pens.ac.id
2. Login ke akun Anda
3. Buka **DevTools** (F12 → Network tab)
4. Refresh halaman
5. Cari request ke `/api/notifikasi/mahasiswa`
6. Copy header `cookie` dan `token`
7. Paste ke `.env`

### Discord Webhook URL

1. Buka Discord server Anda
2. Settings → Webhooks → Create Webhook
3. Copy webhook URL
4. Paste ke `.env` sebagai `DISCORD_WEBHOOK_URL`

### GitHub Gist & Token

1. Login ke https://github.com/settings/tokens
2. Generate new token (Fine-grained → Gist scope)
3. Buat gist baru di https://gist.github.com (nama file: `deadline.ics`)
4. Copy Gist ID dari URL: `https://gist.github.com/username/GIST_ID`
5. Paste ke `.env`

## 📁 Struktur File

```
notify/
├── notif_to_discord.py      # Main script
├── .env                      # Credentials (JANGAN commit!)
├── .env.example              # Template .env
├── sent_ids.json             # Cache ID notifikasi yang sudah dikirim
├── requirements.txt          # Dependencies
└── README.md                 # File ini
```

## 🎨 Discord Embed Preview

Setiap notifikasi muncul dengan format:

```
📚 Pengingat Tugas
> Tugas Algoritma deadline besok!

🕐 Waktu:    10:30 AM
⏰ Deadline:  15 Mei 2026

[🔗 Lihat Detail di ETHOL]
```

Warna & emoji berubah sesuai tipe notifikasi:
- 📝 Tugas Baru (Biru)
- 📚 Pengingat Tugas (Kuning)
- 🎯 Nilai Keluar (Hijau)
- 📢 Pengumuman (Ungu)
- 🗓️ Absensi/Presensi (Orange)
- 📅 Jadwal (Cyan)

## 💾 Data Transfer Optimization

Script sudah dioptimasi untuk VPS dengan quota terbatas:

| Fitur               | Detail                                                                                             |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| Minimal headers     | Hanya field essential (accept, cookie, token, user-agent)                                          |
| Selective fields    | Ambil hanya: idNotifikasi, kodeNotifikasi, keterangan, waktuNotifikasi, createdAtIndonesia, urlWeb |
| Compression         | Support gzip, deflate (br & zstd optional)                                                         |
| Smart caching       | Hindari fetch deadline jika sudah di-cache                                                         |
| Efficient filtering | Gunakan sent_ids.json untuk skip notifikasi duplikat                                               |

**Estimate penghematan:** ~500 MB - 1 GB/bulan (tergantung volume notifikasi)

## ⚙️ Konfigurasi

Edit `notif_to_discord.py` untuk customize:

```python
# Polling interval (dalam detik)
INTERVAL = 60

# API endpoint
API_URL = "https://ethol.pens.ac.id/api/notifikasi/mahasiswa?filterNotif=SEMUA"

# Konfigurasi tipe notifikasi (emoji, label, warna)
NOTIF_CONFIG = {
    "PENGINGAT-TUGAS": {"emoji": "📚", "label": "Pengingat Tugas", "color": 0xF1C40F},
    "TUGAS-BARU":      {"emoji": "📝", "label": "Tugas Baru",      "color": 0x3498DB},
    "NILAI-KELUAR":    {"emoji": "🎯", "label": "Nilai Keluar",    "color": 0x2ECC71},
    "PENGUMUMAN":      {"emoji": "📢", "label": "Pengumuman",      "color": 0x9B59B6},
    "ABSENSI":         {"emoji": "🗓️", "label": "Absensi",         "color": 0xE67E22},
    "PRESENSI":        {"emoji": "🗓️", "label": "Absensi",         "color": 0xE67E22},
    "JADWAL":          {"emoji": "📅", "label": "Jadwal",          "color": 0x1ABC9C},
}
```

### Headers yang Digunakan

Script menggunakan headers lengkap (seperti browser) untuk menghindari rejection dari server:
- User-Agent: iPhone Safari
- Authorization via token + cookie
- Compression: gzip, deflate, br, zstd
- CORS headers yang lengkap

## 📊 Monitoring

### Log File

```bash
# Lihat log realtime
tail -f notif.log

# Search error
grep ERROR notif.log

# Search by tipe notifikasi
grep "✅ Discord" notif.log
```

### Check Status Running

```bash
# Status
ps aux | grep "python notif_to_discord.py"

# Kill process
pkill -f "python notif_to_discord.py"

# Restart dengan nohup
nohup python notif_to_discord.py > notif.log 2>&1 &
```

### Cache Files

```bash
# Lihat notifikasi yang sudah dikirim
cat sent_ids.json

# Reset (clear cache - HATI-HATI!)
rm sent_ids.json
```

## 🐛 Troubleshooting

### HTTP 401/403 Error
**Penyebab:** Token atau cookie sudah expired

**Solusi:**
1. Login ulang ke https://ethol.pens.ac.id
2. Buka DevTools (F12) → Network tab
3. Cari request ke `/api/notifikasi/mahasiswa`
4. Copy header `cookie` dan `token` terbaru
5. Update di `.env`
6. Restart script

```bash
pkill -f "python notif_to_discord.py"
nohup python notif_to_discord.py > notif.log 2>&1 &
```

### Webhook URL Invalid
**Penyebab:** Discord webhook sudah di-delete atau URL salah

**Solusi:**
1. Buka Discord server → Settings → Webhooks
2. Buat webhook baru
3. Copy URL ke `.env` sebagai `DISCORD_WEBHOOK_URL`
4. Restart script

### Gist Not Found (404)
**Penyebab:** Gist ID tidak ada atau file `deadline.ics` tidak ditemukan

**Solusi:**
1. Buat gist baru di https://gist.github.com
2. **Penting:** Nama file harus `deadline.ics` (jangan format lain)
3. Copy Gist ID dari URL: `https://gist.github.com/username/GIST_ID_INI`
4. Update `.env` dengan GIST_ID dan GIST_TOKEN
5. Restart script

### "No module named requests"
**Penyebab:** Dependencies belum terinstall

**Solusi:**
```bash
pip install -r requirements.txt
# atau
pip install requests
```

### Response Structure Unknown
**Penyebab:** Format API response berbeda dari expected

**Solusi:**
Script sudah handle multiple format (data, notifikasi, result, results). Jika tetap error, check:
```bash
# Lihat response struktur
curl -H "cookie: YOUR_COOKIE" \
     -H "token: YOUR_TOKEN" \
     "https://ethol.pens.ac.id/api/notifikasi/mahasiswa?filterNotif=SEMUA"
```

### Notifikasi Tidak Terkirim ke Discord
**Penyebab:** Request gagal atau timeout

**Debug:**
```bash
tail -f notif.log | grep "❌"  # Lihat error messages
tail -f notif.log | grep "⚠️"  # Lihat warning
```

Kemungkinan penyebab:
- Discord webhook rate-limited (tunggu beberapa detik)
- Network timeout (check internet connection)
- Discord webhook URL tidak valid

## 📝 Files Generated

- **sent_ids.json** - Cache ID notifikasi yang sudah dikirim (auto-generated)
  ```json
  ["123456", "789012", "hash_md5_notifikasi"]
  ```
  - Digunakan untuk skip notifikasi duplikat
  - Auto-updated setiap ada notifikasi baru
  - Aman di-delete jika ingin reset (tapi akan mengirim ulang notifikasi lama)

- **notif.log** - Log file jika dijalankan dengan nohup
  - Format: `[YYYY-MM-DD HH:MM:SS] Log message`
  - Useful untuk monitoring & debugging

## 🔄 Workflow

```
┌─────────────────────────────────────┐
│ Script Mulai (setiap 60 detik)      │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ Call API     │ (ETHOL)
        └──────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ Filter notif baru│ (cek sent_ids.json)
        └──────┬───────────┘
               │
         ┌─────┴──────┐
         │            │
         ▼            ▼
      ✅ Ada       ❌ Tidak ada
      Baru         Baru
         │            │
         ▼            ▼
   ┌─────────┐   (sleep 60s)
   │Discord  │   Cek lagi
   └────┬────┘
        │
        ▼
   ┌──────────────┐
   │ Ambil Deadline│ (jika TUGAS-BARU)
   │ dari API     │
   └────┬─────────┘
        │
        ▼
   ┌─────────────┐
   │Push ke Gist │ (update calendar)
   └─────────────┘
        │
        ▼
   ┌──────────────┐
   │Save sent_ids │ (prevent duplicate)
   └──────────────┘
```

## 🔐 Security Tips

⚠️ **PENTING:**
- ✅ Jangan commit `.env` ke git! (Add ke `.gitignore`)
- ✅ Jangan share credentials dengan orang lain
- ✅ Rotate GitHub token setiap 3 bulan
- ✅ Gunakan environment variable untuk production (jangan hardcode)
- ✅ Keep cookie & token updated (expire setiap login baru)

### .gitignore
```
.env
sent_ids.json
notif.log
__pycache__/
*.pyc
```

## 📱 Kompatibilitas

- Python 3.8+
- macOS / Linux / Windows
- Butuh internet connection

## 📄 License

Private Project - PENS Mahasiswa

## 👨‍💻 Development

### Setup Virtual Environment

```bash
# Setup venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Testing Manual

```bash
# Test API connection
python3 << 'EOF'
import requests
headers = {
    "cookie": "YOUR_COOKIE",
    "token": "YOUR_TOKEN"
}
r = requests.get("https://ethol.pens.ac.id/api/notifikasi/mahasiswa?filterNotif=SEMUA", 
                 headers=headers)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")
EOF

# Test Discord webhook
python3 << 'EOF'
import requests
payload = {
    "content": "Test notification ✅",
    "embeds": [{
        "title": "Test",
        "description": "Testing webhook",
        "color": 3498591
    }]
}
r = requests.post("YOUR_WEBHOOK_URL", json=payload)
print(f"Status: {r.status_code}")
EOF
```

### Run Locally (Development)

```bash
# Terminal 1: Run script
python notif_to_discord.py

# Terminal 2: Monitor logs
tail -f notif.log
```

## 📚 Function Overview

| Fungsi                      | Kegunaan                                 |
| --------------------------- | ---------------------------------------- |
| `load_env()`                | Load credentials dari `.env` file        |
| `load_sent_ids()`           | Baca cache notifikasi yang sudah dikirim |
| `save_sent_ids()`           | Simpan cache notifikasi                  |
| `make_id()`                 | Generate unique ID untuk notifikasi      |
| `get_notifikasi()`          | Fetch notifikasi dari ETHOL API          |
| `send_to_discord()`         | Kirim notifikasi ke Discord webhook      |
| `fetch_gist_ics()`          | Ambil calendar dari GitHub Gist          |
| `push_gist_ics()`           | Update calendar di GitHub Gist           |
| `fetch_deadline_from_api()` | Ambil deadline tugas dari API            |
| `add_to_calendar()`         | Tambah event ke ICS calendar             |
| `check_once()`              | Cek notifikasi 1x (main logic)           |
| `main()`                    | Loop utama (cek setiap interval)         |

---

