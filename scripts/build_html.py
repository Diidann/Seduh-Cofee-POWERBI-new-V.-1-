"""Membangun public/index.html dari data/*.csv + scripts/template.html + scripts/chart.min.js.

Jalankan dari mana saja:   python scripts/build_html.py
Butuh: pandas, numpy
"""
import base64
import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
OUT = ROOT / 'public' / 'index.html'

o = pd.read_csv(DATA / 'orders.csv', parse_dates=['order_date'])
c = pd.read_csv(DATA / 'customers.csv', parse_dates=['signup_date'])
p = pd.read_csv(DATA / 'products.csv')
m = pd.read_csv(DATA / 'marketing_spend.csv', parse_dates=['month'])

ym = lambda s: (s.dt.year - 2024) * 12 + s.dt.month - 1
months = [f'{2024 + i // 12}-{i % 12 + 1:02d}' for i in range(24)]
channels = ['Tokopedia', 'Shopee', 'Webstore', 'TikTok Shop']
categories = ['Roasted Beans', 'Ready-to-Drink', 'Accessories', 'Brewing Equipment', 'Subscription', 'Gift Set']
provinces = sorted(o.province.unique())
pays = sorted(o.payment_method.unique())
statuses = ['Completed', 'Returned', 'Cancelled']
bands = [0, 5, 10, 15, 20, 25]
segments = ['Champions', 'Loyal', 'Cant Lose', 'At-Risk', 'Lost', 'Hibernating', 'New / Promising', 'Need Attention', 'Belum Beli']
genders = ['Female', 'Male']
ages = ['<25', '25-29', '30-34', '35-39', '40+']
acqs = ['Instagram Ads', 'TikTok Ads', 'Google Search', 'Marketplace', 'Organic Social', 'Referral']
assert set(o.channel) == set(channels) and set(c.rfm_segment) <= set(segments) and set(p.category) == set(categories)
assert set(c.age_group) <= set(ages) and set(c.acquisition_channel) == set(acqs)

idx = lambda lst: {v: i for i, v in enumerate(lst)}
pidx = {r.product_id: i for i, r in enumerate(p.itertuples())}
cidx = {cid: i for i, cid in enumerate(c.customer_id)}
dims = dict(months=months, channels=channels, categories=categories, provinces=provinces, pays=pays, statuses=statuses, bands=bands,
            segments=segments, genders=genders, ages=ages, acqs=acqs,
            products=[[r.product_id, r.product_name, categories.index(r.category)] for r in p.itertuples()])
cust = dict(seg=c.rfm_segment.map(idx(segments)).tolist(), gen=c.gender.map(idx(genders)).tolist(), age=c.age_group.map(idx(ages)).tolist(),
            acq=c.acquisition_channel.map(idx(acqs)).tolist(),
            sign=((c.signup_date.dt.year - 2024) * 12 + c.signup_date.dt.month - 1).clip(lower=-1).tolist())   # -1 = sebelum 2024
comp = o.is_completed == 1
ord_ = dict(ym=ym(o.order_date).tolist(), ch=o.channel.map(idx(channels)).tolist(), prov=o.province.map(idx(provinces)).tolist(),
            pay=o.payment_method.map(idx(pays)).tolist(), st=o.order_status.map(idx(statuses)).tolist(),
            prod=o.product_id.map(pidx).tolist(), cust=o.customer_id.map(cidx).tolist(), qty=o.quantity.tolist(),
            band=o.discount_pts.map(idx(bands)).tolist(), rating=o.rating.fillna(0).astype(int).tolist(),
            rev=o.revenue_idr.round(2).tolist(), prof=o.profit_idr.round(2).tolist(),
            disc=np.where(comp, o.discount_amount, 0).round(2).tolist(), gross=np.where(comp, o.gross_amount, 0).round(2).tolist())
mk = dict(ym=ym(m.month).tolist(), acq=m.channel_group.map(idx(acqs)).fillna(-1).astype(int).tolist(),
          spend=m.spend_idr.tolist(), impr=m.impressions.tolist(), clicks=m.clicks.tolist())

raw = json.dumps(dict(dims=dims, cust=cust, ord=ord_, mkt=mk), separators=(',', ':')).encode('utf-8')
co = zlib.compressobj(9, zlib.DEFLATED, -15)
b64 = base64.b64encode(co.compress(raw) + co.flush()).decode()
print(f'orders {len(o):,} | customers {len(c):,} | json {len(raw)/1e6:.2f} MB -> base64 {len(b64)/1e3:.0f} KB')

tpl = (ROOT / 'scripts' / 'template.html').read_text(encoding='utf-8')
chart = (ROOT / 'scripts' / 'chart.min.js').read_text(encoding='utf-8')
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(tpl.replace('/*__CHARTJS__*/', chart).replace('__DATA_B64__', b64), encoding='utf-8')
print('tersimpan:', OUT, f'({OUT.stat().st_size/1e3:.0f} KB)')
