"""Membangun public/index.html dari data/*.csv + scripts/template.html + scripts/chart.min.js.

Jalankan dari mana saja:   python scripts/build_html.py
Hanya memakai pustaka standar Python 3.8+ (tanpa pandas/numpy, tanpa pip install),
sehingga bisa dijalankan di laptop mana pun maupun di build Vercel.
"""
import base64
import csv
import json
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
OUT = ROOT / 'public' / 'index.html'


def read(name):
    with open(DATA / f'{name}.csv', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


o = read('orders')
c = read('customers')
p = read('products')
m = read('marketing_spend')

# Urutan di sini = urutan tampil di slicer dan grafik. Nilai baru di CSV harus ditambahkan ke daftar ini.
channels = ['Tokopedia', 'Shopee', 'Webstore', 'TikTok Shop']
categories = ['Roasted Beans', 'Ready-to-Drink', 'Accessories', 'Brewing Equipment', 'Subscription', 'Gift Set']
statuses = ['Completed', 'Returned', 'Cancelled']
bands = [0, 5, 10, 15, 20, 25]
segments = ['Champions', 'Loyal Customers', 'Potential Loyalist', 'New Customers', 'Need Attention', 'At Risk', 'Hibernating',
            'Belum pernah beli']
genders = ['Female', 'Male']
ages = ['<25', '25-29', '30-34', '35-39', '40+', 'Tidak diketahui']
acqs = ['Instagram Ads', 'TikTok Ads', 'Google Search', 'Marketplace', 'Organic Social', 'Referral']
provinces = sorted({r['province'] for r in o})
pays = sorted({r['payment_method'] for r in o})
months = [f'{2024 + i // 12}-{i % 12 + 1:02d}' for i in range(24)]


def check(name, values, allowed, exact=False):
    values, allowed = set(values), set(allowed)
    bad = values - allowed if not exact else values ^ allowed
    if bad:
        sys.exit(f'GAGAL: nilai {name} di CSV tidak ada di daftar build_html.py: {sorted(map(str, bad))}')


check('channel', (r['channel'] for r in o), channels)
check('order_status', (r['order_status'] for r in o), statuses)
check('discount_pts', (int(r['discount_pts']) for r in o), bands)
check('category', (r['category'] for r in p), categories)
check('rfm_segment', (r['rfm_segment'] for r in c), segments)
check('gender', (r['gender'] for r in c), genders)
check('age_group', (r['age_group'] for r in c), ages)
check('acquisition_channel', (r['acquisition_channel'] for r in c), acqs)
check('channel_group', (r['channel_group'] for r in m), acqs)


def idx(lst):
    return {v: i for i, v in enumerate(lst)}


def ym(date):  # 'YYYY-MM-DD' -> nomor bulan sejak Jan 2024 (bisa negatif untuk sebelum 2024)
    return (int(date[:4]) - 2024) * 12 + int(date[5:7]) - 1


for r in o:
    if not 0 <= ym(r['order_date']) < 24:
        sys.exit(f"GAGAL: order {r['order_id']} di luar 2024-2025 ({r['order_date']}); dashboard hanya mendukung 24 bulan")

pidx = {r['product_id']: i for i, r in enumerate(p)}
cidx = {r['customer_id']: i for i, r in enumerate(c)}
seg_i, gen_i, age_i, acq_i = idx(segments), idx(genders), idx(ages), idx(acqs)
ch_i, st_i, band_i = idx(channels), idx(statuses), idx(bands)
prov_i, pay_i = idx(provinces), idx(pays)

dims = dict(months=months, channels=channels, categories=categories, provinces=provinces, pays=pays, statuses=statuses, bands=bands,
            segments=segments, genders=genders, ages=ages, acqs=acqs,
            products=[[r['product_id'], r['product_name'], categories.index(r['category'])] for r in p])
cust = dict(seg=[seg_i[r['rfm_segment']] for r in c], gen=[gen_i[r['gender']] for r in c], age=[age_i[r['age_group']] for r in c],
            acq=[acq_i[r['acquisition_channel']] for r in c],
            sign=[max(ym(r['signup_date']), -1) for r in c])   # -1 = sebelum 2024
ord_ = dict(ym=[ym(r['order_date']) for r in o], ch=[ch_i[r['channel']] for r in o], prov=[prov_i[r['province']] for r in o],
            pay=[pay_i[r['payment_method']] for r in o], st=[st_i[r['order_status']] for r in o],
            prod=[pidx[r['product_id']] for r in o], cust=[cidx[r['customer_id']] for r in o], qty=[int(r['quantity']) for r in o],
            band=[band_i[int(r['discount_pts'])] for r in o], rating=[int(float(r['rating'])) if r['rating'] else 0 for r in o],
            rev=[round(float(r['revenue_idr']), 2) for r in o], prof=[round(float(r['profit_idr']), 2) for r in o],
            disc=[round(float(r['discount_amount']), 2) if r['is_completed'] == '1' else 0.0 for r in o],
            gross=[round(float(r['gross_amount']), 2) if r['is_completed'] == '1' else 0.0 for r in o])
mk = dict(ym=[ym(r['month']) for r in m], acq=[acq_i[r['channel_group']] for r in m],
          spend=[int(float(r['spend_idr'])) for r in m], impr=[int(float(r['impressions'])) for r in m],
          clicks=[int(float(r['clicks'])) for r in m])

raw = json.dumps(dict(dims=dims, cust=cust, ord=ord_, mkt=mk), separators=(',', ':')).encode('utf-8')
co = zlib.compressobj(9, zlib.DEFLATED, -15)
b64 = base64.b64encode(co.compress(raw) + co.flush()).decode()
print(f'orders {len(o):,} | customers {len(c):,} | json {len(raw)/1e6:.2f} MB -> base64 {len(b64)/1e3:.0f} KB')

tpl = (ROOT / 'scripts' / 'template.html').read_text(encoding='utf-8')
chart = (ROOT / 'scripts' / 'chart.min.js').read_text(encoding='utf-8')
assert '/*__CHARTJS__*/' in tpl and '__DATA_B64__' in tpl, 'penanda di template.html hilang'
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(tpl.replace('/*__CHARTJS__*/', chart).replace('__DATA_B64__', b64), encoding='utf-8')
print('tersimpan:', OUT, f'({OUT.stat().st_size/1e3:.0f} KB)')
