import requests
import json
import hashlib
import os
import re
import time
from datetime import datetime, date, timedelta
from pathlib import Path

# ===================== LOAD .env =====================
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

# ===================== KONFIGURASI =====================
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
COOKIE              = os.environ.get("ETHOL_COOKIE", "")
TOKEN               = os.environ.get("ETHOL_TOKEN", "")
GIST_ID             = os.environ.get("GIST_ID", "")
GIST_TOKEN          = os.environ.get("GIST_TOKEN", "")

GIST_FILENAME = "deadline.ics"
API_URL       = "https://ethol.pens.ac.id/api/notifikasi/mahasiswa?filterNotif=SEMUA"
SENT_IDS_FILE = Path(__file__).parent / "sent_ids.json"
BASE_URL      = "https://ethol.pens.ac.id"
INTERVAL      = 60  # detik
# =======================================================

# Pakai headers lengkap persis seperti browser agar tidak di-reject server
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
    "PRESENSI":        {"emoji": "🗓️", "label": "Absensi",         "color": 0xE67E22},
    "JADWAL":          {"emoji": "📅", "label": "Jadwal",          "color": 0x1ABC9C},
}
DEFAULT_CONFIG = {"emoji": "🔔", "label": "Notifikasi", "color": 0x5865F2}
ABSENSI_CODES  = {"ABSENSI", "PRESENSI"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_sent_ids() -> set:
    if SENT_IDS_FILE.exists():
        with open(SENT_IDS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_sent_ids(ids: set):
    with open(SENT_IDS_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)


def make_id(notif: dict) -> str:
    if notif.get("idNotifikasi"):
        return str(notif["idNotifikasi"])
    return hashlib.md5(json.dumps(notif, sort_keys=True).encode()).hexdigest()


def get_notifikasi():
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        for key in ("data", "notifikasi", "result", "results"):
            if key in data and isinstance(data[key], list):
                return data[key]
        print(f"  [WARN] Struktur response tidak dikenal: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        return []
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        print(f"  [ERROR] HTTP {code} saat fetch notifikasi.")
        if code in (401, 403):
            print("  [WARN] Token/cookie expired! Update ETHOL_COOKIE dan ETHOL_TOKEN di .env")
        return None
    except Exception as e:
        print(f"  [ERROR] Gagal ambil notifikasi: {e}")
        return None


# ─── Discord ──────────────────────────────────────────────────────────────────

def send_to_discord(notif: dict):
    kode       = notif.get("kodeNotifikasi", "")
    config     = NOTIF_CONFIG.get(kode, DEFAULT_CONFIG)
    keterangan = notif.get("keterangan", "Tidak ada keterangan.")
    waktu      = notif.get("waktuNotifikasi", "-")
    tgl_indo   = notif.get("createdAtIndonesia", "-")
    url_web    = notif.get("urlWeb", "")
    full_url   = f"{BASE_URL}/mahasiswa{url_web}" if url_web else None

    description = f"> {keterangan}"
    if full_url:
        description += f"\n\n[🔗 Lihat Detail di ETHOL]({full_url})"

    # Untuk TUGAS-BARU dan PENGINGAT-TUGAS, tampilkan deadline
    if kode in ("TUGAS-BARU", "PENGINGAT-TUGAS"):
        data_terkait = notif.get("dataTerkait", "")
        _, deadline_indo = fetch_deadline_from_api(data_terkait)
        tanggal_label = "⏰ Deadline"
        tanggal_value = deadline_indo if deadline_indo else tgl_indo
    else:
        tanggal_label = "📅 Tanggal"
        tanggal_value = tgl_indo

    embed = {
        "title":       f"{config['emoji']}  {config['label']}",
        "description": description,
        "color":       config["color"],
        "fields": [
            {"name": "🕐 Waktu",       "value": waktu or "-",        "inline": True},
            {"name": tanggal_label,    "value": tanggal_value or "-", "inline": True},
        ],
        "footer":    {"text": "PENS • ethol.pens.ac.id"},
        "timestamp": datetime.utcnow().isoformat(),
    }

    payload = {"username": "PENS Notifikasi", "embeds": [embed]}
    if kode in ABSENSI_CODES:
        payload["content"] = "@everyone 🚨 Segera buka absen!"

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code in (200, 204):
            print(f"  ✅ Discord: [{kode}] {keterangan[:70]}")
        else:
            print(f"  ⚠️  Discord {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  ❌ Gagal kirim Discord: {e}")


# ─── Kalender via GitHub Gist ─────────────────────────────────────────────────

def fetch_gist_ics() -> str:
    try:
        r = requests.get(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={
                "Authorization": f"token {GIST_TOKEN}",
                "Accept":        "application/vnd.github+json",
            },
            timeout=10,
        )
        r.raise_for_status()
        files = r.json().get("files", {})
        if GIST_FILENAME not in files:
            return None
        return files[GIST_FILENAME]["content"]
    except Exception as e:
        print(f"  ⚠️  Gagal fetch Gist: {e}")
        return None


def push_gist_ics(content: str):
    try:
        r = requests.patch(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={
                "Authorization": f"token {GIST_TOKEN}",
                "Accept":        "application/vnd.github+json",
            },
            json={"files": {GIST_FILENAME: {"content": content}}},
            timeout=10,
        )
        r.raise_for_status()
        print("  📅 Gist berhasil diupdate.")
    except Exception as e:
        print(f"  ❌ Gagal update Gist: {e}")


def fetch_deadline_from_api(nomor_tugas: str) -> tuple:
    """
    Fetch deadline dari: /api/tugas/by-nomor?nomorTugas=<nomor>
    nomor_tugas diambil dari field dataTerkait di notifikasi.
    """
    if not nomor_tugas:
        return None, ""
    try:
        api_url = f"{BASE_URL}/api/tugas/by-nomor?nomorTugas={nomor_tugas}"
        r = requests.get(api_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        item = data[0] if isinstance(data, list) and data else data
        if not isinstance(item, dict):
            return None, ""
        deadline_str  = item.get("deadline", "")
        deadline_indo = item.get("deadline_indonesia", "")
        if deadline_str:
            d = datetime.strptime(deadline_str[:19], "%Y-%m-%d %H:%M:%S").date()
            return d, deadline_indo
    except Exception as e:
        print(f"  ⚠️  Gagal fetch deadline dari API: {e}")
    return None, ""


def extract_deadline_date(keterangan: str) -> date:
    """Fallback: tebak deadline dari teks keterangan."""
    m = re.search(r"(\d+)\s+hari\s+lagi", keterangan, re.IGNORECASE)
    if m:
        return date.today() + timedelta(days=int(m.group(1)))
    return date.today() + timedelta(days=1)


def parse_events_from_ics(ics_content: str) -> dict:
    events = {}
    blocks = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", ics_content, re.DOTALL)
    for block in blocks:
        uid_match = re.search(r"UID:(.+)", block)
        if uid_match:
            events[uid_match.group(1).strip()] = block.strip()
    return events


def build_ics(events: dict) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PENS Notifikasi//ID",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Deadline Tugas PENS",
    ]
    for block in events.values():
        block_lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        lines.extend(block_lines)
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def add_to_calendar(notif: dict):
    keterangan = notif.get("keterangan", "")
    notif_id   = make_id(notif)
    url_web    = notif.get("urlWeb", "")
    full_url   = f"{BASE_URL}/mahasiswa{url_web}" if url_web else BASE_URL
    uid        = f"{notif_id}@ethol.pens.ac.id"

    # Ambil nomor tugas dari dataTerkait
    nomor_tugas = notif.get("dataTerkait", "")
    deadline, deadline_indo = fetch_deadline_from_api(nomor_tugas)

    # Jika fetch gagal / response kosong, jangan add ke kalender
    if not deadline:
        print("  ℹ️  Deadline tidak ditemukan dari API, skip kalender.")
        return

    print(f"  📅 Deadline terdeteksi: {deadline} ({deadline_indo})")

    date_str     = deadline.strftime("%Y%m%d")
    date_end_str = (deadline + timedelta(days=1)).strftime("%Y%m%d")
    now_str      = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    summary      = re.sub(r"[\r\n]+", " ", keterangan).strip()

    current_ics = fetch_gist_ics()
    existing    = parse_events_from_ics(current_ics) if current_ics else {}

    if uid in existing:
        print("  ℹ️  Event sudah ada di kalender, skip.")
        return

    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_str}",
        f"DTSTART;VALUE=DATE:{date_str}",
        f"DTEND;VALUE=DATE:{date_end_str}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:DL: {deadline_indo}\\n{summary}",
        f"URL:{full_url}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ]
    existing[uid] = "\n".join(event_lines)
    push_gist_ics(build_ics(existing))
    print(f"  📅 Kalender: deadline {deadline} — {keterangan[:60]}")


# ─── Main Loop ────────────────────────────────────────────────────────────────

def check_once(sent_ids: set) -> set:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cek notifikasi...")
    notifs = get_notifikasi()

    if notifs is None:
        return sent_ids

    if not notifs:
        print("  Tidak ada data dari API.")
        return sent_ids

    new_notifs        = [n for n in notifs if make_id(n) not in sent_ids]
    new_notifs_sorted = list(reversed(new_notifs))

    if not new_notifs_sorted:
        print("  Tidak ada notifikasi baru.")
        return sent_ids

    print(f"  🔔 {len(new_notifs_sorted)} notifikasi baru ditemukan!")
    for notif in new_notifs_sorted:
        send_to_discord(notif)
        if notif.get("kodeNotifikasi") == "TUGAS-BARU":
            add_to_calendar(notif)
        sent_ids.add(make_id(notif))

    save_sent_ids(sent_ids)
    return sent_ids


def main():
    print("=" * 50)
    print("  PENS Notifikasi -> Discord & Kalender")
    print(f"  Interval polling: setiap {INTERVAL} detik")
    print("=" * 50)

    sent_ids = load_sent_ids()
    print(f"  {len(sent_ids)} ID notifikasi sebelumnya di-load.\n")

    while True:
        try:
            sent_ids = check_once(sent_ids)
        except KeyboardInterrupt:
            print("\n[INFO] Script dihentikan.")
            break
        except Exception as e:
            print(f"  [ERROR] Unexpected: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()