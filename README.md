# GETER IDX MVP 1.0.0

Dashboard saham Indonesia, terpisah dari Forex/Crypto. Satu server melayani frontend dan API.

## Pemasangan
Baca [PANDUAN_PASANG.md](PANDUAN_PASANG.md). Tidak perlu backend lokal untuk deploy Render.

## Fitur
- Market overview, tabel gainer/loser/teraktif sesuai data engine.
- Pencarian saham, quote, grafik candlestick dan volume, zoom/geser/crosshair.
- History harian/mingguan/bulanan, rentang 1 bulan sampai 5 tahun, maksimum 500 candle.
- Teknikal, fundamental, foreign, broker, bandarmology, corporate action dan berita.
- Screener value dan empat preset bandar (scan 20 kandidat).
- Watchlist browser sampai 40 saham.
- Metadata provider/cache/stale, error terpisah per panel, tidak memakai angka dummy.
- Cache memori terbatas, penggabungan request sama, dua proses engine bersamaan, timeout, rate limit sederhana.
- Login HTTP Basic opsional melalui APP_USER dan APP_PASSWORD. Gunakan HTTPS.
- Ownership tersedia tetapi nonaktif secara default; impor register membutuhkan resource tambahan.

## Batas MVP
- Tidak realtime, tidak ada transaksi/order, bukan sinyal profit.
- Data lanjutan memakai kartu/tabel adaptif dari field engine; sebagian nama field tetap mengikuti engine.
- Tidak menghitung smart score atau memalsukan nilai yang tidak ada.
- Watchlist tidak sinkron antarperangkat; cache server hilang saat restart.
- Rate limit bukan pengganti WAF; di belakang proxy dapat berlaku bersama.
- Health check memeriksa aplikasi dan keberadaan executable, bukan keberhasilan data live.
- Tidak ada scheduler permanen, database akun, atau realtime Stockbit.
- Ownership memakai impor latest saat diminta; disk Render tanpa persistent storage dapat terhapus saat redeploy.
- Data foreign saham mengikuti satuan sumber (termasuk shares); net x close bukan selalu nilai transaksi aktual.
- Label akumulasi/distribusi adalah interpretasi broker flow, bukan bukti satu pemilik/bandar tertentu.

## Engine
Sumber upstream: https://github.com/fzn0x/idx
Pin commit: 5b32d8cb1e6633656e6f23aca72568a8645ce2b7 (release 0.8.1).
Docker memasang npm launcher lalu menjalankan --version saat build untuk mengambil binary release.
Checksum binary ditangani launcher upstream. Node disertakan karena launcher memerlukannya.
Lisensi engine MIT. Kode engine tidak disalin ke repository ini; paket diunduh saat build.
Ketersediaan kode open-source tidak otomatis memberi hak redistribusi seluruh data provider.

## Pengujian
```sh
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
node --check frontend/app.js
node --check frontend/chart.js
```
Fixture tes sintetis hanya untuk pengujian, tidak ditampilkan di dashboard.
Build Docker dan data provider live harus dibuktikan pada GitHub Actions/Render.

## Lokal opsional
```sh
docker compose up --build
```
Buka http://localhost:8000. Tidak diperlukan jika menggunakan Render.

## API
- GET /api/health
- GET /api/market
- GET /api/market-foreign
- GET /api/stock/BBCA/quote
- GET /api/stock/BBCA/history?period=6mo&interval=1d
- GET /api/stock/BBCA/technical
- GET /api/stock/BBCA/fundamental
- GET /api/stock/BBCA/foreign
- GET /api/stock/BBCA/broker
- GET /api/stock/BBCA/bandar
- GET /api/stock/BBCA/ownership
- GET /api/stock/BBCA/actions
- GET /api/stock/BBCA/news
- GET /api/screen?preset=value

Endpoint quote/history/technical lama tetap tersedia. /docs tidak dibuka pada MVP ini.
