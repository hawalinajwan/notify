import requests
import json
import hashlib
import os
import re
from datetime import datetime, date, timedelta

# ===================== KONFIGURASI =====================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1495382294234660934/PX_Lxy8-YPXFBaKQwG611rCnkHmA1PmBVQdQReXpHT5HamYdtd00_QdOKenG1Txgnm6m"

COOKIE = os.environ.get("ETHOL_COOKIE", "")
TOKEN  = os.environ.get("ETHOL_TOKEN", "")

# Gist untuk kalender .ics
GIST_ID       = "da7af98c4e4ecd5f5963ef70b3d284cb"
GIST_TOKEN    = os.environ.get("GIST_TOKEN", "")
GIST_FILENAME = "deadline.ics"

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

NOTIF_CONFIG = {
    "PENGINGAT-TUGAS": {"emoji": "📚", "label": "Pengingat Tugas", "color": 0xF1C40F},
    "TUGAS-BARU":      {"emoji": "📝", "label": "Tugas Baru",      "color": 0x3498DB},
    "NILAI-KELUAR":    {"emoji": "🎯", "label": "Nilai Keluar",    "color": 0x2ECC71},
    "PENGUMUMAN":      {"emoji": "📢", "label": "Pengumuman",      "color": 0x9B59B6},
    "ABSENSI":         {"emoji": "🗓️", "label": "Absensi",         "color": 0xE67E22},
    "JADWAL":          {"emoji": "📅", "label": "Jadwal",          "color": 0x1ABC9C},
}
DEFAULT_CONFIG = {"emoji": "🔔", "label": "Notifikasi", "color": 0x5865F2}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_sent_ids() -> set:
    if os.path.exists(SENT_IDS_FILE):
        with open(SENT_IDS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_sent_ids(ids: set):
    with open(SENT_IDS_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)


def make_id(notif: dict) -> str:
    if notif.get("idNotifikasi"):
        return notif["idNotifikasi"]
    return hashlib.md5(json.dumps(notif, sort_keys=True).encode()).hexdigest()


def get_notifikasi():
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Gagal ambil notifikasi: {e}")
        return None


# ─── Discord ──────────────────────────────────────────────────────────────────

def send_to_discord(notif: dict):
    kode       = notif.get("kodeNotifikasi", "")
    config     = NOTIF_CONFIG.get(kode, DEFAULT_CONFIG)
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
        "footer":    {"text": "PENS • ethol.pens.ac.id"},
        "timestamp": datetime.utcnow().isoformat(),
    }

    payload = {"username": "PENS Notifikasi", "embeds": [embed]}

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code in (200, 204):
            print(f"  ✅ Discord: [{kode}] {keterangan[:70]}")
        else:
            print(f"  ⚠️  Discord {r.status_code}: {r.text}")
    except Exception as e:
        print(f"  ❌ Gagal kirim Discord: {e}")


# ─── Kalender via GitHub Gist ─────────────────────────────────────────────────

def fetch_gist_ics() -> str:
    """Ambil isi file .ics dari Gist."""
    try:
        r = requests.get(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={"Authorization": f"token {GIST_TOKEN}"},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()["files"][GIST_FILENAME]["content"]
    except Exception as e:
        print(f"  ⚠️  Gagal fetch Gist: {e}")
        return None


def push_gist_ics(content: str):
    """Upload isi .ics yang sudah diupdate ke Gist."""
    try:
        r = requests.patch(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={"Authorization": f"token {GIST_TOKEN}"},
            json={"files": {GIST_FILENAME: {"content": content}}},
            timeout=10,
        )
        r.raise_for_status()
        print("  📅 Gist berhasil diupdate.")
    except Exception as e:
        print(f"  ❌ Gagal update Gist: {e}")


def extract_deadline_date(keterangan: str) -> date:
    """Ekstrak tanggal deadline dari teks keterangan."""
    # Pola: "X hari lagi"
    m = re.search(r"(\d+)\s+hari\s+lagi", keterangan, re.IGNORECASE)
    if m:
        return date.today() + timedelta(days=int(m.group(1)))

    # Pola YYYY-MM-DD
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", keterangan)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # Pola DD-MM-YYYY
    m = re.search(r"(\d{2})-(\d{2})-(\d{4})", keterangan)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    # Fallback: besok
    return date.today() + timedelta(days=1)


def parse_events_from_ics(ics_content: str) -> dict:
    """Baca events dari string .ics → {uid: block}"""
    events = {}
    blocks = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", ics_content, re.DOTALL)
    for block in blocks:
        uid_match = re.search(r"UID:(.+)", block)
        if uid_match:
            events[uid_match.group(1).strip()] = block.strip()
    return events


def build_ics(events: dict) -> str:
    """Bangun string .ics dari dict events."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PENS Notifikasi//ID",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:📚 Deadline Tugas PENS",
        "X-WR-TIMEZONE:Asia/Jakarta",
        "REFRESH-INTERVAL;VALUE=DURATION:PT5M",
        "X-PUBLISHED-TTL:PT5M",
    ]
    for block in events.values():
        lines.append(block)
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def add_to_calendar(notif: dict) -> bool:
    """Tambah event deadline ke Gist. Return True jika ada perubahan."""
    keterangan = notif.get("keterangan", "")
    notif_id   = make_id(notif)
    url_web    = notif.get("urlWeb", "")
    full_url   = f"{BASE_URL}{url_web}" if url_web else BASE_URL
    uid        = f"{notif_id}@ethol.pens.ac.id"

    deadline     = extract_deadline_date(keterangan)
    date_str     = deadline.strftime("%Y%m%d")
    date_end_str = (deadline + timedelta(days=1)).strftime("%Y%m%d")
    now_str      = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    summary      = keterangan.replace(",", "\\,").replace(";", "\\;")

    # Fetch isi Gist sekarang
    current_ics = fetch_gist_ics()
    if current_ics:
        existing = parse_events_from_ics(current_ics)
    else:
        existing = {}

    if uid in existing:
        print(f"  ℹ️  Event sudah ada di kalender, skip.")
        return False

    event_block = "\r\n".join([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_str}",
        f"DTSTART;VALUE=DATE:{date_str}",
        f"DTEND;VALUE=DATE:{date_end_str}",
        f"SUMMARY:📝 {summary}",
        f"DESCRIPTION:{summary}",
        f"URL:{full_url}",
        "CATEGORIES:Deadline,Tugas",
        "STATUS:CONFIRMED",
        "TRANSP:TRANSPARENT",
        "END:VEVENT",
    ])

    existing[uid] = event_block
    push_gist_ics(build_ics(existing))
    print(f"  📅 Kalender: deadline {deadline} — {keterangan[:60]}")
    return True


# ─── Main ─────────────────────────────────────────────────────────────────────

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

    new_notifs        = [n for n in notifs if make_id(n) not in sent_ids]
    new_notifs_sorted = list(reversed(new_notifs))

    new_count = 0
    for notif in new_notifs_sorted:
        send_to_discord(notif)

        # Kalender hanya untuk TUGAS-BARU
        if notif.get("kodeNotifikasi") == "TUGAS-BARU":
            add_to_calendar(notif)

        sent_ids.add(make_id(notif))
        new_count += 1

    save_sent_ids(sent_ids)
    print(f"\nSelesai — {new_count} notifikasi baru dikirim.")


if __name__ == "__main__":
    main()
