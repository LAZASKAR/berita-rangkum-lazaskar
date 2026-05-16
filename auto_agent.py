import os
import json
import datetime
import feedparser
import google.generativeai as genai

# Ambil API Key dari brankas Rahasia GitHub
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("❌ Error: GEMINI_API_KEY tidak ditemukan!")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

FILE_JSON = "arsip_berita.json"
FILE_HTML = "arsip_berita.html"

NAMA_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

def baca_database():
    if os.path.exists(FILE_JSON):
        with open(FILE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def simpan_database(data):
    with open(FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def perbarui_halaman_web(data):
    # Struktur HTML & Komponen CSS Premium interaktif
    html_awal = """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI News Agent Logbook</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #f8fafc; --text: #0f172a; --muted: #64748b;
                --card: rgba(255, 255, 255, 0.85); --border: rgba(0, 0, 0, 0.06);
                --accent: #3b82f6; --badge-bg: #e0e7ff; --badge-text: #4338ca;
                --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            }
            @media (prefers-color-scheme: dark) {
                :root {
                    --bg: #0f172a; --text: #f8fafc; --muted: #94a3b8;
                    --card: rgba(30, 41, 59, 0.7); --border: rgba(255, 255, 255, 0.08);
                    --accent: #60a5fa; --badge-bg: #1e3a8a; --badge-text: #bfdbfe;
                    --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
                }
            }
            * { box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 40px 20px; line-height: 1.6; transition: 0.3s; background-image: radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.03), transparent 25%), radial-gradient(circle at 85% 30%, rgba(59, 130, 246, 0.03), transparent 25%); background-attachment: fixed; }
            .container { max-width: 800px; margin: 0 auto; }
            header { text-align: center; margin-bottom: 40px; }
            h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; letter-spacing: -0.5px; }
            .subtitle { color: var(--muted); font-size: 1rem; margin-top: 0; }
            
            details > summary { list-style: none; }
            details > summary::-webkit-details-marker { display: none; }
            
            .accordion-item { background: var(--card); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 20px; box-shadow: var(--shadow); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: 0.2s ease; }
            .accordion-item:hover { transform: translateY(-2px); box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.1); }
            .accordion-header { padding: 20px 25px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: space-between; user-select: none; }
            .accordion-header::after { content: '↓'; font-size: 1.2rem; color: var(--accent); transition: 0.3s ease; }
            details[open] > .accordion-header::after { transform: rotate(180deg); }
            
            .bulan-header { font-size: 1.25rem; }
            .bulan-content { padding: 5px 20px 20px 20px; }
            
            .hari-item { margin-bottom: 12px; border-radius: 12px; background: rgba(0, 0, 0, 0.015); border: 1px solid rgba(128, 128, 128, 0.08); box-shadow: none; }
            @media (prefers-color-scheme: dark) { .hari-item { background: rgba(255, 255, 255, 0.02); } }
            .hari-header { font-size: 1.05rem; padding: 15px 20px; color: var(--accent); }
            .hari-content { padding: 0 15px 15px 15px; }
            
            .berita-card { padding: 20px; background: rgba(0, 0, 0, 0.01); border-radius: 12px; margin-bottom: 15px; border-left: 4px solid var(--accent); }
            @media (prefers-color-scheme: dark) { .berita-card { background: rgba(255, 255, 255, 0.015); } }
            
            .jam-badge { display: inline-flex; align-items: center; background: var(--badge-bg); color: var(--badge-text); padding: 5px 12px; border-radius: 30px; font-size: 0.8rem; font-weight: 600; margin-bottom: 15px; }
            
            .konten-text { font-size: 0.95rem; }
            .konten-text h3 { margin-top: 15px; margin-bottom: 8px; font-size: 1.1rem; color: var(--text); }
            .konten-text h3:first-child { margin-top: 0; }
            .konten-text ul { margin-top: 0; padding-left: 20px; color: var(--muted); }
            .konten-text li { margin-bottom: 6px; }
            .konten-text li::marker { color: var(--accent); }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📰 Logbook AI News</h1>
                <p class="subtitle">Arsip rangkuman berita otomatis harian Anda</p>
            </header>
    """
    
    html_isi = ""
    if not data:
        html_isi = '<div style="text-align:center; padding: 50px; color: var(--muted); border: 2px dashed var(--accent); border-radius: 16px;">Belum ada berita terarsip.</div>'
    else:
        for i, (bulan, hari_dict) in enumerate(sorted(data.items(), reverse=True)):
            open_bulan = "open" if i == 0 else ""
            html_isi += f'<details class="accordion-item bulan-item" {open_bulan}><summary class="accordion-header bulan-header">📅 {bulan}</summary><div class="bulan-content">'
            
            for j, (hari, jam_dict) in enumerate(sorted(hari_dict.items(), reverse=True)):
                open_hari = "open" if i == 0 and j == 0 else ""
                html_isi += f'<details class="accordion-item hari-item" {open_hari}><summary class="accordion-header hari-header">📆 {hari}</summary><div class="hari-content">'
                
                for jam, isi_berita in sorted(jam_dict.items(), reverse=True):
                    html_isi += f'''
                    <div class="berita-card">
                        <span class="jam-badge">⏰ {jam}</span>
                        <div class="konten-text">{isi_berita}</div>
                    </div>
                    '''
                html_isi += '</div></details>'
            html_isi += '</div></details>'

    html_akhir = """
        </div>
        <script>
            const detailsElements = document.querySelectorAll('details');
            detailsElements.forEach((targetDetail) => {
                targetDetail.addEventListener('click', () => {
                    if (!targetDetail.hasAttribute('open')) {
                        const parent = targetDetail.parentElement;
                        const siblings = parent.querySelectorAll(`:scope > details`);
                        siblings.forEach((detail) => {
                            if (detail !== targetDetail && detail.hasAttribute('open')) {
                                detail.removeAttribute('open');
                            }
                        });
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    with open(FILE_HTML, "w", encoding="utf-8") as f:
        f.write(html_awal + html_isi + html_akhir)

def tugas_merangkum():
    sekarang = datetime.datetime.now()
    str_bulan = f"{NAMA_BULAN[sekarang.month]} {sekarang.year}"
    str_hari = f"{NAMA_HARI[sekarang.weekday()]}, {sekarang.day} {NAMA_BULAN[sekarang.month]} {sekarang.year}"
    str_jam = sekarang.strftime("%H:00 WIB")
    
    try:
        url_berita = "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id"
        feed = feedparser.parse(url_berita)
        daftar_berita = [f"- {entry.title}" for entry in feed.entries[:10]]
        konteks_berita = "\n".join(daftar_berita)
        
        prompt = f"""
        Buat rangkuman terstruktur dari 10 berita terkini ini:
        {konteks_berita}
        Output WAJIB HANYA dalam format tag HTML (Gunakan <h3> untuk nama kategori, dan <ul><li> untuk isi beritanya). Jangan sertakan bungkusan markdown ```html.
        Gunakan bahasa Indonesia yang santai tapi tetap informatif.
        """
        respon = model.generate_content(prompt)
        teks_html_berita = respon.text.replace("```html", "").replace("```", "").strip()
        
        db = baca_database()
        if str_bulan not in db: db[str_bulan] = {}
        if str_hari not in db[str_bulan]: db[str_bulan][str_hari] = {}
        db[str_bulan][str_hari][str_jam] = teks_html_berita
        
        simpan_database(db)
        perbarui_halaman_web(db)
        print("✅ Sukses memperbarui database dan tampilan UI web!")
    except Exception as e:
        print(f"❌ Gagal mengeksekusi rangkuman: {e}")

if __name__ == "__main__":
    tugas_merangkum()
