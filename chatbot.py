import re
import random
from datetime import date, timedelta
from typing import Dict, List, Any, Optional

from database import (
    get_inventory,
    add_inventory_item,
    update_inventory_item,
    get_shopping,
    add_shopping_item,
)

# ==============================================================================
# KATALOG RESEP LOKAL (INDONESIAN RECIPE KNOWLEDGE BASE)
# ==============================================================================
RECIPE_CATALOG = [
    {
        "name": "Sup Wortel Kentang",
        "emoji": "🍲",
        "required": ["wortel", "kentang"],
        "optional": ["bawang putih"],
        "steps": [
            "Kupas dan potong dadu kentang serta iris wortel sesuai selera.",
            "Tumis bawang putih cincang hingga harum, lalu masukkan air kaldu/air matang secukupnya.",
            "Rebus kentang dan wortel hingga empuk.",
            "Bumbui dengan garam, merica, dan sedikit kaldu bubuk. Sajikan hangat!",
        ],
    },
    {
        "name": "Telur Dadar Wortel",
        "emoji": "🥕🍳",
        "required": ["telur", "wortel"],
        "optional": ["minyak goreng", "bawang putih"],
        "steps": [
            "Iris tipis atau parut wortel.",
            "Kocok telur bersama garam, lada, dan irisan wortel hingga merata.",
            "Panaskan sedikit minyak goreng di wajan anti-lengket.",
            "Dadar telur dengan api sedang hingga matang keemasan di kedua sisinya.",
        ],
    },
    {
        "name": "Nasi Goreng Telur",
        "emoji": "🍳🍚",
        "required": ["beras", "telur"],
        "optional": ["bawang putih", "minyak goreng"],
        "steps": [
            "Gunakan nasi putih yang sudah dingin.",
            "Tumis bawang putih cincang hingga harum, masukkan telur lalu orak-arik hingga matang.",
            "Masukkan nasi putih, beri sedikit kecap manis, garam, dan lada.",
            "Aduk cepat dengan api besar hingga aroma nasi goreng sedap keluar.",
        ],
    },
    {
        "name": "Kentang Goreng Krispi",
        "emoji": "🍟",
        "required": ["kentang"],
        "optional": ["minyak goreng"],
        "steps": [
            "Kupas kentang, potong memanjang seperti stik, lalu rendam di air garam 15 menit.",
            "Tiriskan dan keringkan potongan kentang dengan tisu dapur.",
            "Goreng dalam minyak panas dengan api sedang hingga kuning keemasan dan renyah.",
        ],
    },
    {
        "name": "Telur Orak-Arik Gurih",
        "emoji": "🍳",
        "required": ["telur"],
        "optional": ["minyak goreng", "susu", "bawang putih"],
        "steps": [
            "Kocok telur bersama sedikit susu (opsional) dan sejumput garam.",
            "Panaskan wajan dengan sedikit minyak atau mentega dengan api kecil.",
            "Tuang kocokan telur lalu aduk perlahan (scramble) hingga teksturnya lembut dan creamy.",
        ],
    },
    {
        "name": "Pancake Susu Lembut",
        "emoji": "🥞",
        "required": ["telur", "susu"],
        "optional": ["mentega", "minyak goreng"],
        "steps": [
            "Campur tepung terigu, telur, susu, dan sedikit gula dalam mangkuk.",
            "Aduk rata hingga adonan kental dan licin tanpa gumpalan.",
            "Tuang sesendok sayur adonan ke teflon panas, tunggu hingga bersarang/berbusa, lalu balik.",
        ],
    },
    {
        "name": "Tumis Sayur Bawang Putih",
        "emoji": "🥬",
        "required": ["wortel"],
        "optional": ["bawang putih", "minyak goreng"],
        "steps": [
            "Iris wortel tipis menyerong.",
            "Tumis bawang putih geprek dengan sedikit minyak sampai harum kekuningan.",
            "Masukkan irisan wortel, beri sedikit air, garam, dan lada, tumis sampai matang renyah.",
        ],
    },
]

# ==============================================================================
# KAMUS NORMALISASI KATA & SINONIM BAHASA INDONESIA
# ==============================================================================
SLANG_MAP = {
    "brp": "berapa",
    "yg": "yang",
    "kpn": "kapan",
    "baput": "bawang putih",
    "bamer": "bawang merah",
    "grg": "goreng",
    "kadaluarsa": "kedaluwarsa",
    "expired": "kedaluwarsa",
    "abisin": "habiskan",
    "habisin": "habiskan",
    "telor": "telur",
    "aja": "saja",
    "udah": "sudah",
    "udh": "sudah",
    "ad": "ada",
    "ga": "tidak",
    "gak": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "nda": "tidak",
    "sy": "saya",
    "aq": "saya",
    "aku": "saya",
    "gue": "saya",
    "gw": "saya",
    "makasih": "terima kasih",
    "thx": "terima kasih",
    "thanks": "terima kasih",
    "tengkyu": "terima kasih",
    "hallo": "halo",
    "helo": "halo",
    "hello": "halo",
    "bwt": "buat",
    "utk": "untuk",
    "dgn": "dengan",
    "dlm": "dalam",
    "blanja": "belanja",
    "minyakk": "minyak",
}

GREETING_RESPONSES = [
    "Halo! Senang bisa menyapa kamu. Ada yang bisa aku bantu kelola dari pantry hari ini? 😊",
    "Hai! Foodsy siap membantu. Mau cek stok makanan, tanggal kedaluwarsa, atau butuh ide masak hari ini? 🌿",
    "Halo! Pantry buddy kamu di sini. Ada yang ingin kamu cek atau catat sekarang? ✨",
]

CLARIFICATION_RESPONSES = [
    "Maaf, aku belum begitu menangkap maksud pertanyaanmu. Kamu bisa menanyakan hal seperti:\n\n- **\"Apa saja stok pantry?\"**\n- **\"Bahan apa yang mau kedaluwarsa?\"**\n- **\"Ada ide resep apa hari ini?\"**\n- Atau sebutkan bahan langsung, misalnya: **\"Telur ada berapa?\"**",
    "Hmm, aku belum paham maksudmu nih. Apakah kamu ingin mengecek stok, mencari ide resep, atau menanyakan bahan tertentu? Beri tahu aku lebih detail ya. 🌿",
    "Pertanyaanmu menarik, tapi aku butuh sedikit kejelasan. Coba tanyakan stok bahan tertentu (misal: *\"Susu masih ada?\"*) atau minta rekomendasi resep!",
]

THANK_RESPONSES = [
    "Sama-sama! Senang bisa membantu merawat dapurmu. Ada lagi yang mau kamu tanyakan? 🌿",
    "Kembali kasih! Semoga masakanmu lezat dan bahan makanan selalu terawat baik ya. 😊",
    "Sama-sama! Jangan ragu panggil aku lagi kalau butuh inspirasi masak atau cek stok! ✨",
]


class ChatbotEngine:
    """
    Mesin Chatbot Kontekstual untuk Foodsy.
    Mampu melacak topik pembicaraan sebelumnya, menangani rujukan kata ganti
    ('yang tadi', 'berapa jumlahnya', 'yang pertama'), serta mencocokkan resep
    secara dinamis dari database SQLite tanpa dependensi eksternal.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_context(session_state: Any) -> Dict[str, Any]:
        """Inisialisasi atau ambil context state dari session_state Streamlit."""
        if "chat_context" not in session_state or not isinstance(session_state.get("chat_context"), dict) or "last_intent" not in session_state.chat_context:
            session_state.chat_context = {
                "last_intent": None,
                "last_items": [],       # List item yang baru saja ditampilkan bot
                "active_item": None,     # Satu item spesifik yang sedang dibahas
                "last_recipes": [],     # List resep yang baru saja disarankan
                "active_recipe": None,   # Resep yang sedang aktif
                "last_query": "",
                "pending_expiry_item": None,
            }
        return session_state.chat_context

    @staticmethod
    def normalize_text(text: str) -> str:
        """Membersihkan dan menormalkan kalimat dari singkatan serta slang."""
        cleaned = text.strip().lower()
        cleaned = re.sub(r"[^\w\s-]", " ", cleaned)
        words = cleaned.split()
        normalized_words = [SLANG_MAP.get(w, w) for w in words]
        return " ".join(normalized_words)

    @staticmethod
    def days_left(item: Dict[str, Any]) -> int:
        """Hitung sisa hari kedaluwarsa."""
        exp = item["expiry"]
        if isinstance(exp, str):
            try:
                exp = date.fromisoformat(exp)
            except ValueError:
                return 0
        return (exp - date.today()).days

    def find_inventory_item(self, text: str, inventory: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Mencari apakah teks mengandung nama bahan yang ada di database."""
        low_text = text.lower()
        for item in inventory:
            name_low = item["name"].lower()
            if re.search(rf"\b{re.escape(name_low)}\b", low_text):
                return item

        for item in inventory:
            name_low = item["name"].lower()
            parts = name_low.split()
            for p in parts:
                if len(p) >= 4 and p in low_text:
                    return item
        return None

    def match_recipes(self, inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Mencocokkan resep dari katalog dengan bahan riil yang ada di database SQLite.
        Menghasilkan skor kecocokan dan daftar bahan yang kurang.
        """
        inv_names = {x["name"].lower() for x in inventory}
        results = []

        for recipe in RECIPE_CATALOG:
            req = [r.lower() for r in recipe["required"]]
            matched_req = []
            missing_req = []
            for r in req:
                if any(r in name or name in r for name in inv_names):
                    matched_req.append(r)
                else:
                    missing_req.append(r)

            match_score = len(matched_req) / len(req) if req else 0.0
            results.append({
                "recipe": recipe,
                "score": match_score,
                "matched": matched_req,
                "missing": missing_req,
                "ready": len(missing_req) == 0,
            })

        results.sort(key=lambda x: (x["ready"], x["score"]), reverse=True)
        return results

    @staticmethod
    def parse_expiry_date(text: str):
        """Menerima tanggal DD-MM-YYYY, DD/MM/YYYY, atau YYYY-MM-DD, serta tanggal relatif."""
        from datetime import datetime
        value = text.strip().lower()

        # 1. Format tanggal numerik standar
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        # 2. Tanggal relatif sederhana dalam bahasa Indonesia
        today = date.today()
        if value in ["besok", "tomorrow"]:
            return today + timedelta(days=1)
        if value in ["lusa"]:
            return today + timedelta(days=2)
        if value in ["seminggu lagi", "1 minggu lagi", "seminggu", "1 minggu"]:
            return today + timedelta(days=7)
        if value in ["2 minggu lagi", "dua minggu lagi"]:
            return today + timedelta(days=14)
        if value in ["sebulan lagi", "1 bulan lagi", "sebulan", "1 bulan"]:
            return today + timedelta(days=30)

        match_hari = re.match(r"^(\d+)\s*hari(?:\s*lagi)?$", value)
        if match_hari:
            return today + timedelta(days=int(match_hari.group(1)))

        match_minggu = re.match(r"^(\d+)\s*minggu(?:\s*lagi)?$", value)
        if match_minggu:
            return today + timedelta(weeks=int(match_minggu.group(1)))

        match_bulan = re.match(r"^(\d+)\s*bulan(?:\s*lagi)?$", value)
        if match_bulan:
            return today + timedelta(days=int(match_bulan.group(1)) * 30)

        return None

    def is_switch_intent(self, raw_message: str, norm: str, inventory: List[Dict[str, Any]]) -> bool:
        """
        Mendeteksi apakah pesan pengguna merupakan intent/perintah baru
        (bukan input tanggal untuk bahan yang sedang menunggu).
        """
        # Cek perintah cek stok / pantry
        if any(w in norm for w in ["stok", "inventaris", "inventory", "persediaan", "isi pantry", "my pantry", "bahan yang ada"]):
            return True

        # Cek perintah kedaluwarsa
        if any(w in norm for w in ["kedaluwarsa", "expired", "basi", "kapan habis", "segera habis", "lewat tanggal"]):
            return True

        # Cek ide resep / masak
        if any(w in norm for w in [
            "resep", "masak", "menu", "masakan", "ide makanan", "makan apa",
            "bisa buat apa", "bisa bikin apa", "mau masak", "ide resep"
        ]):
            return True

        # Cek daftar belanja
        if any(w in norm for w in ["daftar belanja", "shopping list", "belanja", "beli apa"]):
            return True

        # Cek sapaan / terima kasih / identitas
        greetings = ["halo", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum", "hallo"]
        if any(g in norm for g in greetings):
            return True
        if any(w in norm for w in ["terima kasih", "makasih", "thank you", "thanks", "siapa kamu", "nama kamu siapa"]):
            return True

        # Cek perintah penambahan / perubahan bahan baru
        stock_keywords = ["stok", "pantry", "tambahkan", "tambah", "catat", "masukkan", "masukan", "simpan", "belanja", "beli", "baru belanja"]
        if any(term in norm for term in stock_keywords) and self.extract_stock_pairs(raw_message):
            return True
        if re.search(r"(?:tambahkan|tambah|catat|masukkan|simpan)\s+", raw_message, re.IGNORECASE):
            return True

        # Cek bahan spesifik yang ada di pantry
        if self.find_inventory_item(norm, inventory) and any(w in norm for w in ["ada", "punya", "stok", "masih", "cek", "berapa", "kapan"]):
            return True

        # Cek pertanyaan lanjutan / rujukan kontekstual
        if any(w in norm for w in ["apa saja", "bahan apa saja", "ada apa saja", "berapa jumlahnya", "yang tadi", "pertama", "kedua", "ketiga", "terakhir"]):
            return True

        return False

    @staticmethod
    def extract_stock_pairs(message: str):
        """Extract multiple pantry items from natural Indonesian messages."""
        units = r"(?:butir|buah|kg|kilo(?:gram)?|gram|gr|liter|lt|l|ml|mili(?:liter)?|bungkus|pack|ikat|pcs|kaleng|botol|sachet|ons)"
        text = message.lower().replace("\n", ",")
        text = re.sub(r"\b(?:aku|saya|mau|ingin|nih|ini|ya|yah|dong|tolong|please|baru|abis|habis|belanja|beli|membeli|tambahkan|tambah|catat|dicatat|masukkan|masukan|simpan|ke|dalam|pantry|my|stok|bahan|foodsy)\b", " ", text)
        text = re.sub(r"\s+", " ", text).strip(" ,.!?:")
        # First try cleanly separated segments (commas, conjunctions, new lines).
        segments = re.split(r"\s+(?:dan|serta)\s+|[,;]+", text)
        pairs = []
        qty_pattern = rf"\d+(?:[.,]\d+)?\s*{units}"
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            m = re.fullmatch(rf"(?P<name>[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ ]*?)\s+(?P<qty>{qty_pattern})", segment, re.I)
            if m:
                name, qty = m.group("name"), m.group("qty")
            else:
                m = re.fullmatch(rf"(?P<qty>{qty_pattern})\s+(?P<name>[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ ]*)", segment, re.I)
                if not m:
                    continue
                name, qty = m.group("name"), m.group("qty")
            name = re.sub(r"\s+", " ", name).strip(" .,!-").title()
            qty = re.sub(r"\s+", " ", qty).strip()
            if name and not any(x[0].casefold() == name.casefold() for x in pairs):
                pairs.append((name, qty))
        # Fallback: handle adjacent items without punctuation, e.g. "beras 5kg tomat 3 buah ayam 1 kg".
        if len(pairs) < 2:
            matches = list(re.finditer(rf"(?P<qty>{qty_pattern})", text, re.I))
            scanned = []
            for idx, match in enumerate(matches):
                prev_end = matches[idx-1].end() if idx else 0
                chunk = text[prev_end:match.start()].strip(" ,;:.-")
                # Ignore introductory words and retain the final ingredient phrase.
                chunk = re.sub(r"\b(?:tolong|masukkan|masukan|tambahkan|tambah|catat|simpan|stok|bahan)\b", " ", chunk)
                chunk = re.sub(r"\s+", " ", chunk).strip()
                if chunk:
                    name = chunk.title()
                    qty = re.sub(r"\s+", " ", match.group("qty")).strip()
                    if not any(x[0].casefold() == name.casefold() for x in scanned):
                        scanned.append((name, qty))
            if len(scanned) > len(pairs):
                pairs = scanned
        # Also support quantity-first items in a multi-item sentence.
        if not pairs:
            matches = list(re.finditer(rf"(?P<qty>{qty_pattern})\s+(?P<name>[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ ]*?)(?=(?:[,;]|\s+dan\s+|\s+\d)|$)", text, re.I))
            for m in matches:
                name = re.sub(r"\s+", " ", m.group("name")).strip(" ,;.!-").title()
                qty = re.sub(r"\s+", " ", m.group("qty")).strip()
                if name and not any(x[0].casefold() == name.casefold() for x in pairs):
                    pairs.append((name, qty))
        return pairs

    def process_message(self, raw_message: str, session_state: Any) -> str:
        """
        Fungsi utama pemroses pesan pengguna.
        Memadukan intent detection, entity resolution, memory context, dan data SQLite.
        """
        msg = raw_message.strip()
        norm = self.normalize_text(msg)
        context = self.get_context(session_state)

        # Selalu ambil data terbaru langsung dari SQLite
        inventory = get_inventory()
        shopping = get_shopping()

        # ----------------------------------------------------------------------
        # 1. TAMBAH / UPDATE BAHAN + KONFIRMASI TANGGAL KEDALUWARSA
        # ----------------------------------------------------------------------
        pending_queue = context.get("pending_expiry_items", [])
        if not pending_queue and context.get("pending_expiry_item"):
            pending_queue = [context["pending_expiry_item"]]

        if pending_queue:
            pending = pending_queue[0]
            parsed_date = self.parse_expiry_date(msg)
            if parsed_date:
                add_inventory_item(pending["name"], pending["qty"], parsed_date)
                pending_queue.pop(0)
                context["pending_expiry_items"] = pending_queue
                context["pending_expiry_item"] = pending_queue[0] if pending_queue else None
                session_state.inventory = get_inventory()
                session_state.shopping = get_shopping()
                context["active_item"] = next(
                    (x for x in session_state.inventory if x["name"].lower() == pending["name"].lower()), None
                )
                context["last_intent"] = "ADD_ITEM"
                if pending_queue:
                    nxt = pending_queue[0]
                    return (
                        f"Berhasil menyimpan **{pending['name']} ({pending['qty']})** dengan tanggal kedaluwarsa "
                        f"**{parsed_date.strftime('%d-%m-%Y')}**. 🌿\n\n"
                        f"Sekarang masukkan tanggal kedaluwarsa untuk **{nxt['name']} ({nxt['qty']})** "
                        "dengan format **DD-MM-YYYY**."
                    )
                return (
                    f"Berhasil! **{pending['name']} ({pending['qty']})** sudah tersimpan di My Pantry. 🌿\n\n"
                    f"Tanggal kedaluwarsa: **{parsed_date.strftime('%d-%m-%Y')}**."
                )
            if any(w in norm for w in ["batal", "cancel", "tidak jadi"]):
                context["pending_expiry_items"] = []
                context["pending_expiry_item"] = None
                return "Oke, penambahan bahan yang masih menunggu tanggal kedaluwarsa dibatalkan. Data yang belum diberi tanggal belum disimpan."

            # Jika pengguna memasukkan perintah atau intent lain, batalkan pending dan tangani perintah baru
            if self.is_switch_intent(msg, norm, inventory):
                cancelled_names = ", ".join(f"**{x['name']}**" for x in pending_queue)
                context["pending_expiry_items"] = []
                context["pending_expiry_item"] = None
                new_response = self.process_message(raw_message, session_state)
                return f"*(Penambahan {cancelled_names} dibatalkan karena kamu beralih topik.)*\n\n" + new_response

            return (
                f"Aku masih menunggu tanggal kedaluwarsa untuk **{pending['name']} ({pending['qty']})**.\n\n"
                "Masukkan tanggal dengan format **DD-MM-YYYY**, misalnya **25-12-2026** (atau sebutkan *1 minggu lagi*, *besok*).\n"
                "Ketik **batal** jika ingin membatalkan bahan yang masih menunggu."
            )

        # Tambahkan item ke Shopping List melalui chat.
        # Diletakkan sebelum deteksi stok My Pantry agar tidak salah intent.
        shopping_match = re.search(
            r"(?:tolong\s+)?(?:tambahkan|tambah|masukkan|masukan|catat|simpan)\s+(.+?)\s+ke\s+(?:daftar belanja|shopping list)(?:\s+(?:saya|ku))?[.!?\s]*$",
            msg, re.IGNORECASE
        )
        if shopping_match:
            raw_items = shopping_match.group(1).strip(" .,!?")
            shopping_names = re.split(r"\s*,\s*|\s+dan\s+", raw_items, flags=re.IGNORECASE)
            added_names = []
            for item_name in shopping_names:
                item_name = item_name.strip(" .,!?")
                if item_name:
                    add_shopping_item(item_name.title())
                    added_names.append(item_name.title())
            session_state.shopping = get_shopping()
            context["last_intent"] = "SHOPPING_LIST"
            if added_names:
                return "Berhasil! " + ", ".join(f"**{name}**" for name in added_names) + " sudah ditambahkan ke daftar belanja. 🛒"

        # Tambah atau perbarui satu maupun beberapa bahan dari satu pesan.
        stock_intent = any(term in norm for term in [
            "stok", "pantry", "tambahkan", "tambah", "catat", "masukkan", "masukan", "simpan", "belanja", "beli", "baru belanja"
        ])
        parsed_items = self.extract_stock_pairs(msg) if stock_intent else []
        if parsed_items:
            pending_new = []
            updated = []
            for item_name, item_qty in parsed_items:
                existing = next((x for x in inventory if x["name"].lower() == item_name.lower()), None)
                if existing:
                    update_inventory_item(existing["id"], item_qty, existing["expiry"])
                    updated.append(f"{item_name} ({item_qty})")
                else:
                    pending_new.append({"name": item_name, "qty": item_qty})

            session_state.inventory = get_inventory()
            if pending_new:
                context["pending_expiry_items"] = pending_new
                context["pending_expiry_item"] = pending_new[0]
                context["last_intent"] = "WAITING_EXPIRY"
                parts = []
                if updated:
                    parts.append("Jumlah bahan yang sudah ada diperbarui: " + ", ".join(updated) + ".")
                new_text = ", ".join(f"**{x['name']} ({x['qty']})**" for x in pending_new)
                parts.append("Bahan baru yang menunggu tanggal kedaluwarsa: " + new_text + ".")
                parts.append(
                    f"Sebelum disimpan, masukkan tanggal kedaluwarsa untuk **{pending_new[0]['name']} ({pending_new[0]['qty']})** "
                    "dengan format **DD-MM-YYYY**, misalnya **25-12-2026**."
                )
                return "Siap, aku sudah memeriksa bahan yang kamu sebutkan. 😊\n\n" + "\n\n".join(parts)
            context["last_items"] = session_state.inventory
            context["last_intent"] = "UPDATE_ITEM"
            return "Jumlah stok berhasil diperbarui: " + ", ".join(updated) + ". Tanggal kedaluwarsa masing-masing bahan tetap seperti sebelumnya."

        add_match = re.search(
            r"(?:tambahkan|tambah|catat|masukkan|simpan)\s+(?:bahan\s+)?([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ ]*?)\s+(\d+\s*(?:butir|buah|kg|gram|gr|liter|ml|bungkus|pack|ikat|pcs|kaleng|botol|sachet|ons))\s*$",
            msg, re.IGNORECASE
        )
        if not add_match:
            add_match = re.search(
                r"(?:tambahkan|tambah|catat|masukkan|simpan)\s+(\d+\s*(?:butir|buah|kg|gram|gr|liter|ml|bungkus|pack|ikat|pcs|kaleng|botol|sachet|ons))\s+([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ ]*)\s*$",
                msg, re.IGNORECASE
            )
            if add_match:
                qty, name = add_match.group(1).strip(), add_match.group(2).strip().title()
            else:
                qty = name = None
        else:
            name, qty = add_match.group(1).strip().title(), add_match.group(2).strip()

        if name and qty:
            existing = next((x for x in inventory if x["name"].lower() == name.lower()), None)
            if existing:
                update_inventory_item(existing["id"], qty, existing["expiry"])
                session_state.inventory = get_inventory()
                context["active_item"] = next((x for x in session_state.inventory if x["id"] == existing["id"]), existing)
                context["last_intent"] = "UPDATE_ITEM"
                return (f"Jumlah **{name}** sudah diperbarui menjadi **{qty}**. 📝\n\n"
                        f"Tanggal kedaluwarsanya tetap **{existing['expiry'].strftime('%d-%m-%Y')}**.")
            context["pending_expiry_items"] = [{"name": name, "qty": qty}]
            context["pending_expiry_item"] = context["pending_expiry_items"][0]
            context["last_intent"] = "WAITING_EXPIRY"
            return (f"Siap, aku akan mencatat **{name} ({qty})**. 😊\n\n"
                    "Sebelum disimpan, aku perlu tanggal kedaluwarsanya dulu.\n\n"
                    "Silakan masukkan dengan format **DD-MM-YYYY**, misalnya **25-12-2026**.")

        # Tambah item ke Shopping List melalui chat.
        shopping_match = re.search(
            r"(?:tambahkan|tambah|masukkan|catat)\s+(.+?)\s+ke\s+(?:daftar belanja|shopping list)(?:\s+(?:saya|ku))?[.!?\s]*$",
            msg, re.IGNORECASE
        )
        if shopping_match:
            shopping_name = shopping_match.group(1).strip(" .,!").title()
            if shopping_name:
                add_shopping_item(shopping_name)
                session_state.shopping = get_shopping()
                context["last_intent"] = "SHOPPING_LIST"
                return f"Siap! **{shopping_name}** sudah aku tambahkan ke daftar belanja. 🛒"

        # Pilih resep dari daftar sebelumnya: angka atau frasa ordinal.
        recipe_options = context.get("last_recipes", [])
        selection = None
        if re.fullmatch(r"\s*[1-9]\s*[.!]?\s*", norm):
            selection = int(re.search(r"\d+", norm).group())
        else:
            ordinal_map = {"pertama": 1, "kesatu": 1, "nomor satu": 1, "no 1": 1,
                           "kedua": 2, "nomor dua": 2, "no 2": 2,
                           "ketiga": 3, "nomor tiga": 3, "no 3": 3}
            for phrase, number in ordinal_map.items():
                if phrase in norm:
                    selection = number
                    break
        if selection is not None and recipe_options:
            if 1 <= selection <= len(recipe_options):
                rec = recipe_options[selection - 1]
                context["active_recipe"] = rec
                context["last_intent"] = "RECIPE_DETAIL"
                steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(rec["steps"]))
                ingredients = rec.get("required", rec.get("ingredients", []))
                return (f"Siap! Ini cara membuat **{rec['name']}** {rec.get('emoji', '🍳')}. 😊\n\n"
                        f"**Bahan utama:** {', '.join(ingredients)}.\n\n**Cara membuat:**\n{steps_text}\n\n"
                        "Kamu bisa ketik nomor resep lain untuk melihat resep berikutnya.")
            return f"Di daftar tadi ada {len(recipe_options)} resep. Pilih angka 1 sampai {len(recipe_options)}, ya."

        # ----------------------------------------------------------------------
        # 2. SAPAAN & SOSIAL (GREETINGS, THANKS, IDENTITY)
        # ----------------------------------------------------------------------
        greetings = ["halo", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum", "hallo"]
        # Tangani sapaan pendek atau sapaan ke Foodsy (misal "hallo foodsy")
        if any(g in norm for g in greetings) and (len(norm.split()) <= 4 or "foodsy" in norm):
            # Pastikan bukan perintah yang hanya diawali halo
            if not any(k in norm for k in ["stok", "kedaluwarsa", "resep", "belanja", "tambah"]):
                context["last_intent"] = "GREETING"
                if "pagi" in norm:
                    return "Selamat pagi! ☀️ Senang bertemu kamu. Ada yang ingin kamu siapkan untuk sarapan atau cek stok pantry hari ini?"
                if "siang" in norm:
                    return "Selamat siang! 🌤️ Sudah siap makan siang? Mau cek bahan yang ada atau butuh ide resep masakan?"
                if "sore" in norm:
                    return "Selamat sore! ☕ Santai sejenak sambil cek stok bahan dapur yuk. Ada yang bisa aku bantu?"
                if "malam" in norm:
                    return "Selamat malam! 🌙 Mau merencanakan belanjaan besok atau cek bahan yang hampir kedaluwarsa?"
                return random.choice(GREETING_RESPONSES)

        if any(w in norm for w in ["terima kasih", "makasih", "thank you", "thanks"]):
            context["last_intent"] = "THANK"
            return random.choice(THANK_RESPONSES)

        if any(w in norm for w in ["siapa kamu", "nama kamu siapa", "tentang kamu", "kamu apa"]):
            return (
                "Aku **Foodsy**, asisten pantry pintar kamu! 🫙🌿\n\n"
                "Aku bertugas membantumu mencatat bahan makanan, memantau tanggal kedaluwarsa, "
                "mencari inspirasi masakan dari stok yang ada, dan merapikan daftar belanjaanmu."
            )

        # ----------------------------------------------------------------------
        # 3. REKOMENDASI RESEP DINAMIS DARI STOK PANTRY (PRIORITAS DI ATAS FOLLOW-UP)
        # ----------------------------------------------------------------------
        if context.get("active_recipe") and any(w in norm for w in ["cara membuat", "langkahnya", "resepnya", "bahan-bahannya", "jelaskan lagi"]):
            rec = context["active_recipe"]
            steps_text = "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(rec["steps"]))
            ingredients = rec.get("required", rec.get("ingredients", []))
            return f"Ini cara membuat **{rec['name']}**:\n\nBahan utama: {', '.join(ingredients)}.\n\n{steps_text}"

        is_recipe_query = any(w in norm for w in [
            "resep", "masak", "menu", "masakan", "ide makanan", "makan apa",
            "bisa buat apa", "bisa bikin apa", "mau masak", "ide resep"
        ])
        if is_recipe_query:
            # Cek apakah menanyakan langkah/cara masak untuk active_recipe
            if any(w in norm for w in ["langkah", "cara masak", "cara buat", "gimana caranya", "bagaimana"]) and context.get("active_recipe"):
                rec = context["active_recipe"]
                steps_text = "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(rec["steps"]))
                return f"Berikut langkah membuat **{rec['name']}** {rec['emoji']}:\n\n{steps_text}\n\nSelamat mencoba memasak ya! 🍳"

            recipe_matches = self.match_recipes(inventory)
            ready_recipes = [m for m in recipe_matches if m["ready"]]
            almost_recipes = [m for m in recipe_matches if not m["ready"] and m["score"] > 0]

            context["last_recipes"] = [m["recipe"] for m in ready_recipes] or [m["recipe"] for m in almost_recipes]
            context["last_intent"] = "RECIPE_LIST"

            if ready_recipes:
                recipe_list = [m["recipe"] for m in ready_recipes]
                context["last_recipes"] = recipe_list
                context["active_recipe"] = None
                choices = "\n".join(
                    f"{i+1}. **{r['name']}** {r.get('emoji', '🍳')} (menggunakan {', '.join(r['required'])})"
                    for i, r in enumerate(recipe_list)
                )
                return (
                    "Tentu! Ini pilihan resep yang bisa dibuat dari stok pantry kamu. 😊\n\n"
                    + choices
                    + "\n\nKetik angka resep yang ingin kamu lihat, misalnya **1**, **2**, atau **3**."
                )

            if almost_recipes:
                rec = almost_recipes[0]
                missing_str = ", ".join(rec["missing"])
                return (
                    f"Kamu punya sebagian bahan untuk membuat **{rec['recipe']['name']}** {rec['recipe']['emoji']}.\n\n"
                    f"- **Bahan tersedia:** {', '.join(rec['matched'])}\n"
                    f"- **Bahan yang kurang:** {missing_str}\n\n"
                    f"Mau aku catatkan **{missing_str}** ke dalam Shopping List kamu?"
                )

            return (
                "Saat ini bahan di pantry kamu belum mencukupi untuk membuat resep yang ada di katalog. 🍳\n\n"
                "Coba tambahkan bahan seperti telur, beras, wortel, atau kentang melalui chat "
                "(misal: *\"Tambahkan telur 6 butir\"*), nanti aku bantu carikan resep yang lezat!"
            )

        # ----------------------------------------------------------------------
        # 4. PENANGANAN RUJUKAN KONTEKS & PERTANYAAN LANJUTAN
        # ("yang tadi", "berapa jumlahnya?", "yang pertama", "yang mana?", "apa saja?")
        # ----------------------------------------------------------------------
        # A. Rujukan Ordinal (Urutan: pertama, kedua, ketiga, terakhir)
        if any(w in norm for w in ["pertama", "kesatu", "nomor 1", "no 1"]) and context.get("last_items"):
            selected = context["last_items"][0]
            context["active_item"] = selected
            d = self.days_left(selected)
            status_hari = f"kedaluwarsa dalam {d} hari lagi" if d >= 0 else "sudah lewat kedaluwarsa"
            return (
                f"Yang pertama adalah **{selected['name']}**.\n\n"
                f"- **Jumlah stok:** {selected['qty']}\n"
                f"- **Status kedaluwarsa:** {selected['expiry'].strftime('%d-%m-%Y')} ({status_hari})\n\n"
                f"Mau aku carikan ide resep untuk {selected['name']}?"
            )

        if any(w in norm for w in ["kedua", "nomor 2", "no 2"]) and len(context.get("last_items", [])) >= 2:
            selected = context["last_items"][1]
            context["active_item"] = selected
            d = self.days_left(selected)
            status_hari = f"kedaluwarsa dalam {d} hari lagi" if d >= 0 else "sudah lewat kedaluwarsa"
            return (
                f"Yang kedua adalah **{selected['name']}**.\n\n"
                f"- **Jumlah stok:** {selected['qty']}\n"
                f"- **Status kedaluwarsa:** {selected['expiry'].strftime('%d-%m-%Y')} ({status_hari})\n\n"
                f"Mau tahu ide olahan untuk {selected['name']}?"
            )

        if any(w in norm for w in ["ketiga", "nomor 3", "no 3"]) and len(context.get("last_items", [])) >= 3:
            selected = context["last_items"][2]
            context["active_item"] = selected
            d = self.days_left(selected)
            status_hari = f"kedaluwarsa dalam {d} hari lagi" if d >= 0 else "sudah lewat kedaluwarsa"
            return (
                f"Yang ketiga adalah **{selected['name']}**.\n\n"
                f"- **Jumlah stok:** {selected['qty']}\n"
                f"- **Status kedaluwarsa:** {selected['expiry'].strftime('%d-%m-%Y')} ({status_hari})"
            )

        if any(w in norm for w in ["terakhir", "paling akhir"]) and context.get("last_items"):
            selected = context["last_items"][-1]
            context["active_item"] = selected
            d = self.days_left(selected)
            status_hari = f"kedaluwarsa dalam {d} hari lagi" if d >= 0 else "sudah lewat kedaluwarsa"
            return (
                f"Yang paling terakhir di daftar adalah **{selected['name']}**.\n\n"
                f"- **Jumlah stok:** {selected['qty']}\n"
                f"- **Tanggal kedaluwarsa:** {selected['expiry'].strftime('%d-%m-%Y')} ({status_hari})"
            )

        # B. Rujukan "yang tadi" / "itu" / "tersebut"
        if any(w in norm for w in ["yang tadi", "itu", "tersebut", "tadi"]) and not any(k in norm for k in ["stok", "kedaluwarsa", "resep"]):
            target_item = context.get("active_item") or (context["last_items"][0] if context.get("last_items") else None)
            if target_item:
                fresh = next((x for x in inventory if x["id"] == target_item["id"]), target_item)
                context["active_item"] = fresh
                d = self.days_left(fresh)
                status_hari = f"kedaluwarsa dalam {d} hari lagi" if d >= 0 else "sudah lewat kedaluwarsa"
                return (
                    f"Bahan yang tadi kita bicarakan adalah **{fresh['name']}**.\n\n"
                    f"- **Jumlah stok:** {fresh['qty']}\n"
                    f"- **Status kedaluwarsa:** {fresh['expiry'].strftime('%d-%m-%Y')} ({status_hari})\n\n"
                    f"Ada yang ingin kamu tanyakan lagi tentang {fresh['name']}?"
                )

        # C. Pertanyaan Lanjutan Jumlah: "Berapa jumlahnya?", "Ada berapa stoknya?"
        if any(w in norm for w in ["berapa jumlahnya", "ada berapa", "jumlahnya berapa", "berapa banyak", "stoknya berapa"]):
            target_item = self.find_inventory_item(norm, inventory) or context.get("active_item")
            if target_item:
                fresh = next((x for x in inventory if x["id"] == target_item["id"]), target_item)
                context["active_item"] = fresh
                return f"Stok **{fresh['name']}** saat ini ada sebanyak **{fresh['qty']}** di database pantry kamu."
            if context.get("last_items"):
                lines = [f"- **{x['name']}**: {x['qty']}" for x in context["last_items"]]
                return "Ini rincian jumlah untuk bahan-bahan yang baru saja kita bahas:\n\n" + "\n".join(lines)
            return "Bahan mana yang ingin kamu ketahui jumlahnya? Sebutkan namanya ya, misalnya: *\"Telur berapa jumlahnya?\"*"

        # D. Pertanyaan Lanjutan Kedaluwarsa: "Kapan kedaluwarsanya?", "Kapan expired?"
        if any(w in norm for w in ["kapan kedaluwarsa", "kapan expired", "kapan basi", "expirednya kapan", "tanggal berapa expired"]):
            target_item = self.find_inventory_item(norm, inventory) or context.get("active_item")
            if target_item:
                fresh = next((x for x in inventory if x["id"] == target_item["id"]), target_item)
                d = self.days_left(fresh)
                if d < 0:
                    keterangan = f"⚠️ **Sudah lewat** {abs(d)} hari yang lalu ({fresh['expiry'].strftime('%d-%m-%Y')})"
                elif d == 0:
                    keterangan = "🚨 **Kedaluwarsa hari ini!** Segera gunakan ya."
                elif d <= 3:
                    keterangan = f"⏰ **Segera kedaluwarsa:** tinggal {d} hari lagi ({fresh['expiry'].strftime('%d-%m-%Y')})"
                else:
                    keterangan = f"✅ Masih aman, sekitar {d} hari lagi ({fresh['expiry'].strftime('%d-%m-%Y')})"
                return f"Tanggal kedaluwarsa untuk **{fresh['name']}**:\n\n{keterangan}"
            return "Bahan mana yang ingin kamu cek tanggal kedaluwarsanya? Sebutkan nama bahannya ya."

        # E. Pertanyaan "Apa saja?" / "Bahan apa saja?"
        if any(w in norm for w in ["apa saja", "bahan apa saja", "ada apa saja"]) and len(norm.split()) <= 4:
            if context.get("last_intent") == "EXPIRY_CHECK" and context.get("last_items"):
                lines = [f"- **{x['name']}** ({x['qty']}) — kedaluwarsa {x['expiry'].strftime('%d-%m-%Y')}" for x in context["last_items"]]
                return "Berikut daftar bahan yang hampir atau sudah kedaluwarsa tersebut:\n\n" + "\n".join(lines)
            if context.get("last_intent") == "RECIPE_LIST" and context.get("last_recipes"):
                lines = [f"- **{r['name']}** {r.get('emoji', '')} (Bahan: {', '.join(r['required'])})" for r in context["last_recipes"]]
                return "Ini rekomendasi resep masakan yang sesuai:\n\n" + "\n".join(lines)
            # Default fallback ke isi stok lengkap
            if not inventory:
                return "Pantry kamu saat ini masih kosong. Silakan tambahkan bahan terlebih dahulu ya!"
            lines = [f"- **{x['name']}** ({x['qty']})" for x in inventory]
            context["last_items"] = inventory
            context["last_intent"] = "INVENTORY_LIST"
            return "Ini semua bahan yang tersimpan di pantry kamu saat ini:\n\n" + "\n".join(lines)

        # ----------------------------------------------------------------------
        # 5. CEK SPESIFIK NAMA BAHAN ("Ada telur?", "Susu masih ada?")
        # ----------------------------------------------------------------------
        specific_item = self.find_inventory_item(norm, inventory)
        if specific_item and any(w in norm for w in ["ada", "punya", "stok", "masih", "cek", "berapa"]):
            context["active_item"] = specific_item
            context["last_intent"] = "ITEM_DETAIL"
            d = self.days_left(specific_item)
            if d < 0:
                exp_text = f"sudah lewat {abs(d)} hari lalu"
            elif d <= 3:
                exp_text = f"segera kedaluwarsa dalam {d} hari lagi"
            else:
                exp_text = f"aman sampai {d} hari lagi"

            return (
                f"Ya, **{specific_item['name']}** ada di pantry kamu! ✨\n\n"
                f"- **Jumlah:** {specific_item['qty']}\n"
                f"- **Kedaluwarsa:** {specific_item['expiry'].strftime('%d-%m-%Y')} ({exp_text})\n\n"
                f"Mau aku bantu carikan resep menggunakan {specific_item['name']}?"
            )

        # ----------------------------------------------------------------------
        # 6. CEK STOK / RINGKASAN PANTRY
        # ----------------------------------------------------------------------
        if any(w in norm for w in ["stok", "inventaris", "inventory", "persediaan", "isi pantry", "my pantry", "bahan yang ada"]):
            if not inventory:
                context["last_items"] = []
                context["last_intent"] = "INVENTORY_LIST"
                return "Saat ini belum ada bahan makanan yang tercatat di My Pantry. Yuk catat bahan pertamamu, misalnya: *\"Tambahkan telur 6 butir\"*!"

            context["last_items"] = inventory
            context["last_intent"] = "INVENTORY_LIST"
            summary_lines = [
                f"{i+1}. **{x['name']}** — {x['qty']} (kedaluwarsa {x['expiry'].strftime('%d-%m-%Y')})"
                for i, x in enumerate(inventory)
            ]
            intro = random.choice([
                "Ini daftar seluruh bahan yang tersimpan di pantry kamu saat ini:",
                "Berdasarkan data pantry aktual, ini stok makanan yang kamu miliki:",
                "Berikut stok makanan yang tercatat rapi di My Pantry:",
            ])
            return intro + "\n\n" + "\n".join(summary_lines) + "\n\n💡 *Kamu bisa tanya detail bahan tertentu, misalnya: \"Yang pertama berapa jumlahnya?\"*"

        # ----------------------------------------------------------------------
        # 7. CEK BAHAN KEDALUWARSA / EXPIRED
        # ----------------------------------------------------------------------
        if any(w in norm for w in ["kedaluwarsa", "expired", "basi", "kapan habis", "segera habis", "lewat tanggal"]):
            expired = [x for x in inventory if self.days_left(x) < 0]
            soon = [x for x in inventory if 0 <= self.days_left(x) <= 3]

            context["last_items"] = expired + soon
            context["last_intent"] = "EXPIRY_CHECK"

            if not expired and not soon:
                return (
                    "Kabar baik! 🎉 Tidak ada bahan yang tercatat kedaluwarsa atau akan kedaluwarsa dalam 3 hari ke depan.\n\n"
                    "Semua stokmu masih aman. Tetap periksa kondisi fisik makanan secara berkala ya!"
                )

            result_parts = []
            if expired:
                lines = [f"- **{x['name']}** ({x['qty']}) — lewat sejak {x['expiry'].strftime('%d-%m-%Y')}" for x in expired]
                result_parts.append("⚠️ **Sudah melewati tanggal:**\n" + "\n".join(lines))
            if soon:
                lines = [f"- **{x['name']}** ({x['qty']}) — sisa **{self.days_left(x)} hari lagi** ({x['expiry'].strftime('%d-%m-%Y')})" for x in soon]
                result_parts.append("⏰ **Segera kedaluwarsa (perlu diprioritaskan):**\n" + "\n".join(lines))

            return (
                "Ini bahan yang perlu kamu perhatikan di dapur:\n\n" +
                "\n\n".join(result_parts) +
                "\n\n💡 *Tips: Sebaiknya olah bahan-bahan di atas terlebih dahulu. Mau aku buatkan ide resepnya?*"
            )

        # ----------------------------------------------------------------------
        # 8. DAFTAR BELANJA / SHOPPING LIST
        # ----------------------------------------------------------------------
        if any(w in norm for w in ["daftar belanja", "shopping list", "belanja", "beli apa"]):
            context["last_intent"] = "SHOPPING_LIST"
            if not shopping:
                return "Daftar belanjaanmu saat ini masih kosong! Kamu bisa mencatat kebutuhan dapur di menu **Shopping List**."
            lines = [f"{i+1}. **{x['name']}**" for i, x in enumerate(shopping)]
            return (
                "Ini daftar kebutuhan belanja yang tercatat di Foodsy:\n\n" +
                "\n".join(lines) +
                "\n\n🛒 *Segera belanja sebelum persediaan di dapur benar-benar habis ya!*"
            )

        # ----------------------------------------------------------------------
        # 9. PERTANYAAN TIDAK DIKENALI -> KLARIFIKASI RAMAH (ANTI-HALLUCINATION)
        # ----------------------------------------------------------------------
        if context.get("active_item") and len(norm.split()) <= 3:
            item = context["active_item"]
            return f"Apakah kamu masih ingin membahas tentang **{item['name']}**? Kamu bisa tanyakan jumlah stoknya, tanggal kedaluwarsanya, atau ide resepnya!"

        return random.choice(CLARIFICATION_RESPONSES)
