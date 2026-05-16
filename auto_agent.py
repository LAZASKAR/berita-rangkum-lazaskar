import os
import time
import json
import datetime
import schedule
import feedparser
import google.generativeai as genai

# ==========================================
# 1. KONFIGURASI API GEMINI
# ==========================================
# Ganti dengan API Key "BERITA SUMMARY" lu
API_KEY = "AIzaSyDBj0DjmySZNlKyq-S8hlHd2_iwkNSr_wc"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')

FILE_JSON = "arsip_berita.json"
FILE_HTML = "arsip_berita.html"

# Daftar nama bulan & hari untuk Bahasa Indonesia
NAMA_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# ==========================================
# 2. FUNGSI DATABASE LOKAL (Menyimpan Riwayat)
# ==========================================
def baca_database():
    """Membaca data berita yang sudah pernah dirangkum sebelumnya"""
    if os.path.exists(FILE_JSON):
        with open(FILE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def simpan_database(data):
    """Menyimpan data berita baru ke dalam file JSON"""
    with open(FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 3. FUNGSI PEMBUAT HALAMAN WEB (HTML & CSS)
# ==========================================
def perbarui_halaman_web(data):
    """Membuat file arsip_berita.html dengan desain yang rapi dan terstruktur"""
    html_awal = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Logbook AI News Agent</title>
        <style>
            * { box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 20px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            h1 { text-align: center; color: #2563eb; font-size: 28px; border-bottom: 2px solid #e5e7eb; padding-bottom: 15px; margin-top: 0; }
            
            /* Styling untuk Level Bulan */
            .bulan-details { background: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; margin-bottom: 15px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            .bulan-summary { background: #f9fafb; padding: 15px; font-size: 20px; font-weight: bold; cursor: pointer; color: #111827; outline: none; transition: background 0.2s; }
            .bulan-summary:hover { background: #f3f4f6; }
            
            /* Styling untuk Level Hari */
            .hari-details { margin: 10px 15px; border: 1px solid #e5e7eb; border-radius: 6px; }
            .hari-summary { background: #ffffff; padding: 12px; font-size: 16px; font-weight: bold; cursor: pointer; color: #3b82f6; border-bottom: 1px solid #e5e7eb; }
            
            /* Styling untuk Konten Berita */
            .berita-konten { padding: 15px; background: #fcfcfd; font-size: 15px; }
            .jam-badge { display: inline-block; background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 12px; }
            
            .konten-text ul { margin-top: 0; padding-left: 20px; }
            .konten-text li { margin-bottom: 8px; }
            .konten-text h3 { margin-top: 15px; margin-bottom: 5px; color: #1f2937; font-size: 16px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📰 Logbook Rangkuman Berita Harian</h1>
    """
    
    html_isi = ""
    # Urutkan bulan dari yang terbaru
    for bulan, hari_dict in sorted(data.items(), reverse=True):
        html_isi += f'<details class="bulan-details" open><summary class="bulan-summary">📅 {bulan}</summary>'
        
        # Urutkan hari dari yang terbaru
        for hari, jam_dict in sorted(hari_dict.items(), reverse=True):
            html_isi += f'<details class="hari-details" open><summary class="hari-summary">📆 {hari}</summary>'
            
            # Urutkan jam dari yang terbaru
            for jam, isi_berita in sorted(jam_dict.items(), reverse=True):
                html_isi += f'''
                <div class="berita-konten">
                    <span class="jam-badge">⏰ {jam}</span>
                    <div class="konten-text">{isi_berita}</div>
                </div>
                '''
            html_isi += '</details>'
        html_isi += '</details>'

    html_akhir = """
        </div>
    </body>
    </html>
    """
    
    with open(FILE_HTML, "w", encoding="utf-8") as f:
        f.write(html_awal + html_isi + html_akhir)

# ==========================================
# 4. TUGAS UTAMA (Mengambil & Merangkum Berita)
# ==========================================
def tugas_merangkum():
    sekarang = datetime.datetime.now()
    # Format kategori waktu untuk hierarki web
    str_bulan = f"{NAMA_BULAN[sekarang.month]} {sekarang.year}"
    str_hari = f"{NAMA_HARI[sekarang.weekday()]}, {sekarang.day} {NAMA_BULAN[sekarang.month]} {sekarang.year}"
    str_jam = sekarang.strftime("%H:00 WIB") # Dibulatkan ke jam
    
    print(f"\n[{sekarang.strftime('%H:%M:%S')}] 🤖 Agent mulai merangkum berita...")
    
    try:
        url_berita = "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id"
        feed = feedparser.parse(url_berita)
        
        daftar_berita = [f"- {entry.title}" for entry in feed.entries[:10]]
        konteks_berita = "\n".join(daftar_berita)
        
        prompt = f"""
        Buat rangkuman dari 10 berita terkini ini:
        {konteks_berita}
        
        TUGAS PENTING: 
        1. Buat rangkuman poin per poin (bullet points).
        2. Kelompokkan berdasarkan kategori (contoh: Nasional, Ekonomi, Teknologi, dll).
        3. Output HANYA dalam format tag HTML (Gunakan <h3> untuk nama kategori, dan <ul><li> untuk isi beritanya). Jangan gunakan markdown seperti ```html.
        4. Gunakan bahasa Indonesia yang santai tapi informatif.
        """
        
        respon = model.generate_content(prompt)
        teks_html_berita = respon.text.replace("```html", "").replace("```", "").strip()
        
        # Simpan ke Database JSON
        db = baca_database()
        if str_bulan not in db: db[str_bulan] = {}
        if str_hari not in db[str_bulan]: db[str_bulan][str_hari] = {}
        
        db[str_bulan][str_hari][str_jam] = teks_html_berita
        simpan_database(db)
        
        # Build ulang Web HTML-nya
        perbarui_halaman_web(db)
        print(f"✅ Rangkuman berhasil! Web [arsip_berita.html] sudah diupdate.")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")

# ==========================================
# 5. JADWAL (SCHEDULER)
# ==========================================
# 1. Kita panggil satu kali saat file ini dijalankan pertama kali (untuk testing)
tugas_merangkum()

# 2. Daftarkan jadwal regulernya
schedule.every().day.at("04:00").do(tugas_merangkum)
schedule.every().day.at("16:00").do(tugas_merangkum)

print("------------------------------------------------------")
print("⏰ AI Agent Automation aktif dan siap siaga!")
print("File web [arsip_berita.html] sudah dibuat di folder ini.")
print("Menunggu jam 04:00 dan 16:00 untuk update selanjutnya...")
print("(Biarkan terminal/VS Code ini tetap terbuka agar jadwal berjalan)")
print("------------------------------------------------------")

while True:
    schedule.run_pending()
    time.sleep(60) # Pengecekan waktu dilakukan setiap 1 menit