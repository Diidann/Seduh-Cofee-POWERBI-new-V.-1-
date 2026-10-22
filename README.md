# Seduh Coffee Dashboard

Dashboard interaktif (HTML statis) untuk proyek akhir Data Analyst **Seduh Coffee**.
Tiga halaman: **Overview**, **Produk & Diskon**, **Pelanggan & Marketing**, dengan slicer, klik-untuk-filter, dan KPI.

- Satu file `public/index.html`, tanpa backend, tanpa API, tanpa internet.
- Data (fiktif, untuk pembelajaran) sudah tertanam di dalam file dan dihitung di browser pengunjung.
- Grafik memakai [Chart.js](https://www.chartjs.org/) (lisensi MIT), sudah disertakan di dalam file.

## Struktur

```
public/index.html        halaman yang dipublikasikan (hasil build)
data/*.csv               data sumber (orders, customers, products, marketing_spend)
scripts/build_html.py    pembuat index.html dari CSV
scripts/template.html    template tampilan + logika dashboard
scripts/chart.min.js     pustaka Chart.js
vercel.json              konfigurasi Vercel (folder output = public)
```

## Deploy ke Vercel

1. Upload folder ini ke GitHub (lihat bagian di bawah).
2. Di [vercel.com](https://vercel.com): **Add New → Project** → impor repo ini.
3. Biarkan pengaturan bawaan: *Framework Preset* = **Other**, *Build Command* kosong, *Output Directory* otomatis `public` (dari `vercel.json`).
4. Klik **Deploy**. Selesai.

Hanya isi folder `public/` yang dipublikasikan. Folder `data/` dan `scripts/` tidak ikut disajikan.

## Upload ke GitHub

```bash
git init
git add .
git commit -m "Seduh Coffee dashboard"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA-REPO.git
git push -u origin main
```

## Menjalankan lokal

Buka `public/index.html` dengan klik dua kali, atau:

```bash
python -m http.server 8000 --directory public
```

lalu buka http://localhost:8000.

## Memperbarui data

Ubah file di `data/`, lalu bangun ulang halaman:

```bash
pip install pandas numpy
python scripts/build_html.py
```

Commit dan push; Vercel akan men-deploy ulang otomatis.

## Catatan metodologi

- Revenue dan profit hanya dari order berstatus **Completed**.
- Revenue = qty × harga × (1 − diskon). Profit = qty × (harga neto − unit_cost), jadi hanya memperhitungkan COGS (belum ongkir, fee marketplace, biaya operasional).
- CAC = spend ÷ pelanggan baru (signup di rentang tahun terpilih). `Marketplace` diasumsikan sama dengan `Marketplace Ads`; Organic Social dan Referral tidak punya data spend.
- Filter tidak disimpan; halaman kembali ke "Semua" saat dimuat ulang.
- Browser yang didukung: Chrome, Edge, Firefox, Safari versi terbaru (memakai `DecompressionStream`).

Semua data bersifat fiktif dan tidak merepresentasikan bisnis atau merek tertentu.
