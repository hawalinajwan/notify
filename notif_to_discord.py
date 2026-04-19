import requests
import json
import hashlib
import os
from datetime import datetime

# ===================== KONFIGURASI =====================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1495382294234660934/PX_Lxy8-YPXFBaKQwG611rCnkHmA1PmBVQdQReXpHT5HamYdtd00_QdOKenG1Txgnm6m"

# Diambil dari GitHub Secrets
COOKIE = os.environ.get("ETHOL_COOKIE", "")
TOKEN  = os.environ.get("ETHOL_TOKEN", "")

API_URL        = "https://ethol.pens.ac.id/api/notifikasi/mahasiswa?filterNotif=SEMUA"
SENT_IDS_FILE  = "sent_ids.json"
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
    raw = json.dumps(notif, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def send_to_discord(notif: dict):
    judul  = notif.get("judul")   or notif.get("title")     or "Notifikasi Baru"
    pesan  = notif.get("pesan")   or notif.get("message")   or notif.get("isi") or str(notif)
    tanggal= notif.get("tanggal") or notif.get("createdAt") or notif.get("waktu") or ""
    tipe   = notif.get("tipe")    or notif.get("type")      or ""

    color_map = {
        "info":    0x3498DB,
        "warning": 0xF1C40F,
        "danger":  0xE74C3C,
        "success": 0x2ECC71,
    }
    color = color_map.get(str(tipe).lower(), 0x5865F2)

    embed = {
        "title":       f"🔔 {judul}",
        "description": pesan,
        "color":       color,
        "footer":      {"text": f"ethol.pens.ac.id • {tanggal}"},
        "timestamp":   datetime.utcnow().isoformat(),
    }
    if tipe:
        embed["fields"] = [{"name": "Tipe", "value": str(tipe).upper(), "inline": True}]

    payload = {"username": "PENS Notifikasi", "embeds": [embed]}

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code in (200, 204):
            print(f"  ✅ Terkirim: {judul}")
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

    # Sesuaikan key response — coba beberapa kemungkinan
    notifs = (
        data
        if isinstance(data, list)
        else data.get("data") or data.get("notifikasi") or data.get("result") or []
    )

    print(f"Total notifikasi dari API : {len(notifs)}")
    print(f"ID yang sudah dikirim     : {len(sent_ids)}")

    new_count = 0
    for notif in notifs:
        nid = make_id(notif)
        if nid not in sent_ids:
            send_to_discord(notif)
            sent_ids.add(nid)
            new_count += 1

    save_sent_ids(sent_ids)
    print(f"\nSelesai — {new_count} notifikasi baru dikirim ke Discord.")


if __name__ == "__main__":
    main()
