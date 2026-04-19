import requests
import json
import hashlib
import os
from datetime import datetime

# ===================== KONFIGURASI =====================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1495382294234660934/PX_Lxy8-YPXFBaKQwG611rCnkHmA1PmBVQdQReXpHT5HamYdtd00_QdOKenG1Txgnm6m"

COOKIE = os.environ.get("ETHOL_COOKIE", "")
TOKEN  = os.environ.get("ETHOL_TOKEN", "")

API_URL       = "https://ethol.pens.ac.id/api/notifikasi/mahasiswa?filterNotif=SEMUA"
SENT_IDS_FILE = "sent_ids.json"
BASE_URL      = "https://ethol.pens.ac.id"
# =======================================================

HEADERS = {
    "authority":          "ethol.pens.ac.id",
    "accept":             "application/json, text/plain, */*",
    "accept-encoding":    "gzip, deflate, br, zstd",
    "accept-language":    "en-GB,en;q=0.9",
    "cookie":             COOKIE,
    "referer":            "https://ethol.pens.ac.id/mahasiswa/beranda",
    "sec-ch-ua":          '"Chromium";v="146", "Not.A.Brand";v="24", "Brave";v="146"',
    "sec-ch-ua-mobile":   "?1",
    "sec-ch-ua-platform": '"iOS"',
    "sec-fetch-dest":     "empty",
    "sec-fetch-mode":     "cors",
    "sec-fetch-site":     "same-origin",
    "sec-gpc":            "1",
    "token":              TOKEN,
    "user-agent":         "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
}

# Mapping kode notifikasi → emoji & warna
NOTIF_CONFIG = {
    "PENGINGAT-TUGAS": {"emoji": "📚", "label": "Pengingat Tugas", "color": 0xF1C40F},
    "TUGAS-BARU":      {"emoji": "📝", "label": "Tugas Baru",      "color": 0x3498DB},
    "NILAI-KELUAR":    {"emoji": "🎯", "label": "Nilai Keluar",    "color": 0x2ECC71},
    "PENGUMUMAN":      {"emoji": "📢", "label": "Pengumuman",      "color": 0x9B59B6},
    "ABSENSI":         {"emoji": "🗓️", "label": "Absensi",         "color": 0xE67E22},
    "JADWAL":          {"emoji": "📅", "label": "Jadwal",          "color": 0x1ABC9C},
}
DEFAULT_CONFIG = {"emoji": "🔔", "label": "Notifikasi", "color": 0x5865F2}


def load_sent_ids() -> set:
    if os.path.exists(SENT_IDS_FILE):
        with open(SENT_IDS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_sent_ids(ids: set):
    with open(SENT_IDS_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)


def get_notifikasi():
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Gagal ambil notifikasi: {e}")
        return None


def make_id(notif: dict) -> str:
    if notif.get("idNotifikasi"):
        return notif["idNotifikasi"]
    return hashlib.md5(json.dumps(notif, sort_keys=True).encode()).hexdigest()


def send_to_discord(notif: dict):
    kode     = notif.get("kodeNotifikasi", "")
    config   = NOTIF_CONFIG.get(kode, DEFAULT_CONFIG)

    keterangan = notif.get("keterangan", "Tidak ada keterangan.")
    waktu      = notif.get("waktuNotifikasi", "-")
    tgl_indo   = notif.get("createdAtIndonesia", "-")
    url_web    = notif.get("urlWeb", "")
    full_url   = f"{BASE_URL}{url_web}" if url_web else None

    description = f"> {keterangan}"
    if full_url:
        description += f"\n\n[🔗 Lihat Detail di ETHOL]({full_url})"

    embed = {
        "title":       f"{config['emoji']}  {config['label']}",
        "description": description,
        "color":       config["color"],
        "fields": [
            {"name": "🕐 Waktu",   "value": waktu,    "inline": True},
            {"name": "📅 Tanggal", "value": tgl_indo, "inline": True},
        ],
        "footer": {
            "text": "PENS • ethol.pens.ac.id",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    payload = {
        "username": "PENS Notifikasi",
        "embeds":   [embed],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code in (200, 204):
            print(f"  ✅ Terkirim: [{kode}] {keterangan[:70]}")
        else:
            print(f"  ⚠️  Discord {r.status_code}: {r.text}")
    except Exception as e:
        print(f"  ❌ Gagal kirim Discord: {e}")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cek notifikasi...")

    sent_ids = load_sent_ids()
    data     = get_notifikasi()

    if not data:
        print("Tidak ada data dari API.")
        return

    notifs = (
        data
        if isinstance(data, list)
        else data.get("data") or data.get("notifikasi") or data.get("result") or []
    )

    print(f"Total notifikasi : {len(notifs)}")
    print(f"Sudah dikirim    : {len(sent_ids)}")

    # Filter hanya yang belum dikirim
    new_notifs = [n for n in notifs if make_id(n) not in sent_ids]

    # Balik urutan: kirim yang terlama dulu agar di Discord urutan terbaru di bawah (paling atas = paling baru)
    new_notifs_sorted = list(reversed(new_notifs))

    new_count = 0
    for notif in new_notifs_sorted:
        nid = make_id(notif)
        send_to_discord(notif)
        sent_ids.add(nid)
        new_count += 1

    save_sent_ids(sent_ids)
    print(f"\nSelesai — {new_count} notifikasi baru dikirim ke Discord.")


if __name__ == "__main__":
    main()
