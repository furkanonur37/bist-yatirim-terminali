import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import warnings
import json
import os
import datetime

warnings.filterwarnings('ignore')

# --- SAYFA AYARLARI ---
VERI_DOSYASI = "portfoy_verisi.json"
st.set_page_config(page_title="Yatırım Dashboard GOD TIER", layout="wide")

# --- 🔐 KULLANICI GİRİŞ SİSTEMİ (LOGIN) ---
if 'aktif_kullanici' not in st.session_state:
    st.session_state['aktif_kullanici'] = None

if st.session_state['aktif_kullanici'] is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🚀 BİST & Global Yatırım Terminali</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9e9e9e;'>Kendi portföyünüze ulaşmak için giriş yapın veya yeni bir kullanıcı adı belirleyin.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form(key="giris_formu"):
            giris_adi = st.text_input("👤 Kullanıcı Adı (Örn: ahmet123)", placeholder="Kullanıcı adınızı yazın...")
            giris_btn = st.form_submit_button("Giriş Yap / Hesabımı Oluştur", use_container_width=True)
            
            if giris_btn:
                if giris_adi.strip() != "":
                    st.session_state['aktif_kullanici'] = giris_adi.strip().lower()
                    st.rerun()
                else:
                    st.error("Lütfen geçerli bir kullanıcı adı girin!")
    st.stop() 

# Giriş yapılmışsa aktif kullanıcıyı al
aktif_kullanici = st.session_state['aktif_kullanici']

st.title("🚀 BİST & Global Yatırım Terminali")

# --- ÜST BAR: CANLI PİYASA NABZI (TICKER) ---
with st.container():
    col_b100, col_b30, col_usd = st.columns(3)
    try:
        endeksler = yf.download(["XU100.IS", "XU030.IS", "USDTRY=X"], period="5d", progress=False)['Close']
        
        b100_fiyatlar = endeksler["XU100.IS"].dropna()
        b100_son = float(b100_fiyatlar.iloc[-1])
        b100_dun = float(b100_fiyatlar.iloc[-2]) if len(b100_fiyatlar) > 1 else b100_son
        b100_yuzde = ((b100_son - b100_dun) / b100_dun) * 100 if b100_dun > 0 else 0

        b30_fiyatlar = endeksler["XU030.IS"].dropna()
        b30_son = float(b30_fiyatlar.iloc[-1])
        b30_dun = float(b30_fiyatlar.iloc[-2]) if len(b30_fiyatlar) > 1 else b30_son
        b30_yuzde = ((b30_son - b30_dun) / b30_dun) * 100 if b30_dun > 0 else 0

        usd_fiyatlar = endeksler["USDTRY=X"].dropna()
        usd_son = float(usd_fiyatlar.iloc[-1])
        usd_dun = float(usd_fiyatlar.iloc[-2]) if len(usd_fiyatlar) > 1 else usd_son
        usd_yuzde = ((usd_son - usd_dun) / usd_dun) * 100 if usd_dun > 0 else 0

        col_b100.metric("BİST 100", f"{b100_son:,.2f}", f"% {b100_yuzde:.2f}")
        col_b30.metric("BİST 30", f"{b30_son:,.2f}", f"% {b30_yuzde:.2f}")
        col_usd.metric("USD / TRY", f"{usd_son:.4f} ₺", f"% {usd_yuzde:.2f}") 
    except:
        st.warning("⚠️ Piyasa özet verileri anlık olarak çekilemedi.")

st.markdown("---")

# --- GELİŞMİŞ VERİ TABANI ---
def tum_veritabanini_yukle():
    if not os.path.exists(VERI_DOSYASI):
        return {} 
    with open(VERI_DOSYASI, "r") as file:
        try:
            data = json.load(file)
            if "Ana Portföy" in data:
                return {"kurucu_hesap": data}
            return data
        except:
            return {}

def tum_veritabanini_kaydet(data):
    with open(VERI_DOSYASI, "w") as file:
        json.dump(data, file, indent=4)

tum_veritabani = tum_veritabanini_yukle()

if aktif_kullanici not in tum_veritabani:
    tum_veritabani[aktif_kullanici] = {"Ana Portföy": {}, "Geçmiş İşlemler": []}
    tum_veritabanini_kaydet(tum_veritabani)

portfoyler = tum_veritabani[aktif_kullanici]
guncel_listeler = [k for k in portfoyler.keys() if k != "Geçmiş İşlemler"]

# --- SİDEBAR YÖNETİMİ ---
st.sidebar.title("🗂️ Terminal Yönetimi")

yeni_liste_adi = st.sidebar.text_input("Yeni Liste Oluştur", placeholder="Örn: Bebek Hisseler...")
if st.sidebar.button("➕ Liste Ekle") and yeni_liste_adi:
    if yeni_liste_adi not in portfoyler:
        portfoyler[yeni_liste_adi] = {}
        tum_veritabanini_kaydet(tum_veritabani)
        st.rerun()

aktif_liste = st.sidebar.selectbox("📌 Çalıştığın Listeyi Seç", guncel_listeler)
aktif_portfoy = portfoyler.get(aktif_liste, {})
st.sidebar.markdown("---")

with st.sidebar.form(key="ekleme_formu", clear_on_submit=True):
    st.subheader(f"[{aktif_liste}] Ekle / Güncelle")
    varlik_tipi = st.selectbox("Sınıf", ["BİST Hisse", "Kripto / Döviz / Altın"])
    varlik_kod_input = st.text_input("Kod (Örn: LOGO)", value="").strip().upper()
    col_adet, col_maliyet = st.columns(2)
    varlik_adet_input = col_adet.number_input("Adet", min_value=0.01, step=1.0, value=1.0)
    varlik_maliyet_input = col_maliyet.number_input("Maliyet", min_value=0.01, step=0.01, format="%.2f", value=10.00)
    hedef_fiyat = st.number_input("Kâr Al (Hedef Fiyat ₺)", min_value=0.0, step=0.1, format="%.2f", value=0.0)
    ekle_btn = st.form_submit_button(label="Kaydet / Güncelle")

if ekle_btn and varlik_kod_input:
    islem_kodu = f"{varlik_kod_input}.IS" if varlik_tipi == "BİST Hisse" and not varlik_kod_input.endswith(".IS") else varlik_kod_input
    portfoyler[aktif_liste][islem_kodu] = {"Adet": varlik_adet_input, "Maliyet": varlik_maliyet_input, "Hedef": hedef_fiyat, "Tip": varlik_tipi}
    tum_veritabanini_kaydet(tum_veritabani) 
    st.rerun() 

if aktif_portfoy:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 Varlık Sat & Kapat")
    satilacak_varlik = st.sidebar.selectbox("Kapatılacak Varlık", options=["Seçiniz..."] + list(aktif_portfoy.keys()))
    satis_fiyati = st.sidebar.number_input("Satış Fiyatı (₺)", min_value=0.0, step=0.1, format="%.2f")
    
    if st.sidebar.button("İşlemi Kapat ve Arşivle") and satilacak_varlik != "Seçiniz...":
        maliyet = portfoyler[aktif_liste][satilacak_varlik]["Maliyet"]
        adet = portfoyler[aktif_liste][satilacak_varlik]["Adet"]
        kar_zarar = (satis_fiyati - maliyet) * adet
        yuzde = ((satis_fiyati - maliyet) / maliyet) * 100 if maliyet > 0 else 0
        islem_kaydi = {"Tarih": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "Varlık": satilacak_varlik, "Adet": adet, "Maliyet": maliyet, "Satış": satis_fiyati, "Kâr/Zarar": kar_zarar, "Yüzde": yuzde, "Durum": "Kazanıldı 🟢" if kar_zarar > 0 else "Kaybedildi 🔴"}
        portfoyler["Geçmiş İşlemler"].append(islem_kaydi)
        del portfoyler[aktif_liste][satilacak_varlik]
        tum_veritabanini_kaydet(tum_veritabani)
        st.sidebar.success(f"İşlem kapatıldı! Kâr/Zarar: {kar_zarar:.2f} ₺")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(f"👤 Aktif Hesap: **{aktif_kullanici.upper()}**")
if st.sidebar.button("🚪 Hesaptan Çıkış Yap", type="primary"):
    st.session_state['aktif_kullanici'] = None
    st.rerun()

bist_populer = ["AKBNK.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "ISCTR.IS", "KCHOL.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", "YKBNK.IS"]

def soft_color_kâr(val):
    if val > 0: return 'color: #81c784; font-weight: 500; background-color: rgba(129, 199, 132, 0.1)'
    elif val < 0: return 'color: #e57373; font-weight: 500; background-color: rgba(229, 115, 115, 0.1)'
    else: return 'color: #9e9e9e; font-weight: 500'

def soft_highlight_degisim(val):
    if val > 0: return 'color: #81c784; font-weight: bold; background-color: rgba(129, 199, 132, 0.1)'
    elif val < 0: return 'color: #e57373; font-weight: bold; background-color: rgba(229, 115, 115, 0.1)'
    else: return 'color: #9e9e9e; font-weight: bold'

# --- ANA EKRAN SEKMELERİ VE GİZLİ PATRON MODU MANTIĞI ---
sekme_listesi = [f"📊 {aktif_liste} Özeti", "🤖 Algoritmik Asistan", "🏆 İşlem Geçmişi", "🏢 Canlı Piyasa", "📈 Grafik Terminali"]

# Eğer giren kişi patronsa, 6. sekmeyi ekle!
if aktif_kullanici == "patron":
    sekme_listesi.append("👑 Patron Paneli")

sekmeler = st.tabs(sekme_listesi)

with sekmeler[0]:
    if not aktif_portfoy:
        st.info("Bu liste şu an boş. Sol menüden varlık ekleyebilirsin.")
    else:
        varliklar = list(aktif_portfoy.keys())
        with st.spinner('Fiyatlar, hacimler ve temel veriler çekiliyor...'):
            gecmis_veri = yf.download(varliklar, period="20d", progress=False) 
            fiyat_veri = gecmis_veri['Close']
            hacim_veri = gecmis_veri['Volume']
            
        veri_listesi = []
        hedef_vuruldu = False 
        
        for v in varliklar:
            try:
                fiyatlar = fiyat_veri[v].dropna() if isinstance(fiyat_veri, pd.DataFrame) else fiyat_veri.dropna()
                hacimler = hacim_veri[v].dropna() if isinstance(hacim_veri, pd.DataFrame) else hacim_veri.dropna()
                guncel_fiyat = float(fiyatlar.iloc[-1])
                gunluk_hacim = int(hacimler.iloc[-1]) if not hacimler.empty else 0
                sma20 = float(fiyatlar.rolling(20).mean().iloc[-1]) if len(fiyatlar) >= 20 else guncel_fiyat
                
                adet = aktif_portfoy[v].get("Adet", 1)
                maliyet = aktif_portfoy[v].get("Maliyet", 0.0)
                hedef = aktif_portfoy[v].get("Hedef", 0.0)
                
                toplam_maliyet = adet * maliyet
                guncel_deger = adet * guncel_fiyat
                kar_zarar = guncel_deger - toplam_maliyet
                kar_yuzde = (kar_zarar / toplam_maliyet) * 100 if toplam_maliyet > 0 else 0
                
                durum = "⏳ Beklemede"
                if hedef > 0 and guncel_fiyat >= hedef:
                    durum = "🎯 HEDEF VURULDU!"
                    hedef_vuruldu = True
                
                veri_listesi.append({"VARLIK": v.replace(".IS", ""), "ADET": adet, "MALİYET": maliyet, "GÜNCEL FİYAT": guncel_fiyat, "KÂR/ZARAR": kar_zarar, "KÂR(%)": kar_yuzde, "TOPLAM DEĞER": guncel_deger, "HACİM (LOT)": f"{gunluk_hacim:,}", "TEKNİK DURUM": "🟢 Pozitif (SMA Üstü)" if guncel_fiyat > sma20 else "🔴 Negatif", "DURUM": durum})
            except:
                pass
                
        if hedef_vuruldu and 'kutlama' not in st.session_state:
            st.balloons()
            st.session_state['kutlama'] = True
            st.success("Tebrikler! Belirlediğin hedef fiyata ulaşan hisselerin var! 🎯")
            
        if veri_listesi:
            df_portfoy = pd.DataFrame(veri_listesi)
            top_kasa = df_portfoy["TOPLAM DEĞER"].sum()
            top_kar = df_portfoy["KÂR/ZARAR"].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("LİSTE TOPLAM DEĞERİ", f"{top_kasa:,.2f} ₺ / $")
            col2.metric("LİSTE NET KÂR/ZARAR", f"{top_kar:,.2f} ₺", f"{top_kar:,.2f} ₺")
            
            st.markdown("---")
            st.dataframe(df_portfoy.style.map(soft_color_kâr, subset=['KÂR/ZARAR', 'KÂR(%)']).format({"MALİYET": "{:.2f} ₺", "GÜNCEL FİYAT": "{:.2f} ₺", "KÂR/ZARAR": "{:.2f} ₺", "KÂR(%)": "% {:.2f}", "TOPLAM DEĞER": "{:.2f} ₺"}), width="stretch", hide_index=True)
            st.session_state['yapay_zeka_verisi'] = df_portfoy
            st.session_state['toplam_kasa'] = top_kasa

with sekmeler[1]:
    st.subheader("🤖 Portföy Zeka Asistanı")
    st.markdown("Algoritmamız portföyündeki verileri tarayarak sana stratejik geri bildirimler sunar.")
    if 'yapay_zeka_verisi' in st.session_state and not st.session_state['yapay_zeka_verisi'].empty:
        df_yz = st.session_state['yapay_zeka_verisi']
        toplam_kasa = st.session_state['toplam_kasa']
        uyari_sayisi = 0
        for idx, row in df_yz.iterrows():
            agirlik = (row['TOPLAM DEĞER'] / toplam_kasa) * 100
            if agirlik > 40:
                st.warning(f"⚠️ **Risk Uyarısı ({row['VARLIK']}):** Bu varlık portföyünün **%{agirlik:.1f}'sini** oluşturuyor. Yumurtaları aynı sepete koymak konsantrasyon riski yaratır. Kâr alıp çeşitlendirme yapmayı düşünebilirsin.")
                uyari_sayisi += 1
            if row['TEKNİK DURUM'] == "🔴 Negatif":
                st.info(f"📉 **Teknik Not ({row['VARLIK']}):** Varlık kısa vadeli 20 günlük ortalamasının altında seyrediyor. Yeni alım yapmak için trendin yukarı dönmesini beklemek mantıklı olabilir.")
                uyari_sayisi += 1
            if row['KÂR(%)'] < -15:
                st.error(f"🩸 **Stop-Loss Önerisi ({row['VARLIK']}):** %15'ten fazla zarardasın. Eğer uzun vadeli değer yatırımı değilse, sermayeni korumak için işlemi kapatmayı gözden geçirmelisin.")
                uyari_sayisi += 1
            if row['KÂR(%)'] > 50:
                st.success(f"🏆 **Kâr Alma Önerisi ({row['VARLIK']}):** %50'nin üzerinde efsanevi bir kâr oranın var! En azından ana paranı içeriden çıkarıp 'bedava' hisselerle yola devam etmeyi düşünebilirsin.")
                uyari_sayisi += 1
        if uyari_sayisi == 0:
            st.success("✅ Harika iş çıkarıyorsun! Portföyün gayet dengeli, ağırlıklar ideal seviyede ve trendler seninle. Böyle devam!")
    else:
        st.info("Asistanın çalışması için portföyüne varlık eklemelisin.")

with sekmeler[2]:
    st.subheader("🏆 Arşiv & Trade İstatistikleri")
    gecmis = portfoyler.get("Geçmiş İşlemler", [])
    if len(gecmis) > 0:
        df_gecmis = pd.DataFrame(gecmis)
        toplam_realize_kar = df_gecmis["Kâr/Zarar"].sum()
        basarili_islem = len(df_gecmis[df_gecmis["Kâr/Zarar"] > 0])
        win_rate = (basarili_islem / len(gecmis)) * 100
        c1, c2, c3 = st.columns(3)
        c1.metric("Gerçekleşen Toplam Kâr", f"{toplam_realize_kar:,.2f} ₺")
        c2.metric("Toplam İşlem Sayısı", f"{len(gecmis)} Adet")
        c3.metric("Kazanma Oranı (Win-Rate)", f"% {win_rate:.1f}", "Algoritma Başarısı")
        st.markdown("---")
        st.dataframe(df_gecmis, width="stretch", hide_index=True)
    else:
        st.info("Henüz kapatılmış (satılmış) bir işlemin yok.")

with sekmeler[3]:
    st.subheader("🏢 Türkiye'nin En Hacimli Şirketleri (Günlük Performans)")
    if st.button("🔄 Piyasa Verilerini Çek / Güncelle"):
        with st.spinner("Borsa İstanbul verileri hesaplanıyor..."):
            bist_data = yf.download(bist_populer, period="5d", progress=False)['Close']
            piyasa_listesi = []
            for hisse in bist_populer:
                try:
                    fiyatlar = bist_data[hisse].dropna()
                    if len(fiyatlar) >= 2:
                        fiyat_bugun, fiyat_dun = float(fiyatlar.iloc[-1]), float(fiyatlar.iloc[-2])
                        degisim_yuzde = ((fiyat_bugun - fiyat_dun) / fiyat_dun) * 100
                    else:
                        fiyat_bugun, degisim_yuzde = float(fiyatlar.iloc[-1]) if not fiyatlar.empty else 0.0, 0.0
                    piyasa_listesi.append({"ŞİRKET": hisse.replace(".IS", ""), "GÜNCEL FİYAT (₺)": fiyat_bugun, "GÜNLÜK DEĞİŞİM (%)": degisim_yuzde})
                except:
                    pass
            if piyasa_listesi:
                df_piyasa = pd.DataFrame(piyasa_listesi).sort_values(by="GÜNLÜK DEĞİŞİM (%)", ascending=False)
                st.dataframe(df_piyasa.style.map(soft_highlight_degisim, subset=['GÜNLÜK DEĞİŞİM (%)']).format({"GÜNCEL FİYAT (₺)": "{:.2f} ₺", "GÜNLÜK DEĞİŞİM (%)": "% {:.2f}"}), width="stretch", hide_index=True)

with sekmeler[4]:
    st.subheader("📈 Profesyonel Canlı Grafik Terminali")
    kullanici_hisseleri = [h.replace(".IS", "") for h in aktif_portfoy.keys()]
    bist_kisaltmalar = [h.replace(".IS", "") for h in bist_populer]
    tum_grafik_secenekleri = sorted(list(set(kullanici_hisseleri + bist_kisaltmalar)))
    col_secim, col_motor = st.columns([1, 1])
    secilen_grafik_adi = col_secim.selectbox("🔍 Grafiğini Açmak İstediğin Varlığı Seç:", tum_grafik_secenekleri)
    grafik_motoru = col_motor.radio("⚙️ Grafik Motoru (Altyapı):", ["Yerli Motor (BİST Uyumlu)", "TradingView (Kripto & Global)"], horizontal=True)
    st.markdown("---")
    
    if grafik_motoru == "Yerli Motor (BİST Uyumlu)":
        with st.spinner(f"{secilen_grafik_adi} grafik verileri çekiliyor..."):
            yf_kod = f"{secilen_grafik_adi}.IS" if "-" not in secilen_grafik_adi else secilen_grafik_adi
            mum_veri = yf.download(yf_kod, period="6mo", progress=False)
            if not mum_veri.empty:
                fig_candle = go.Figure(data=[go.Candlestick(x=mum_veri.index, open=mum_veri['Open'].squeeze(), high=mum_veri['High'].squeeze(), low=mum_veri['Low'].squeeze(), close=mum_veri['Close'].squeeze(), name="Fiyat", increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
                sma20 = mum_veri['Close'].squeeze().rolling(window=20).mean()
                fig_candle.add_trace(go.Scatter(x=mum_veri.index, y=sma20, mode='lines', name='SMA 20 (Trend)', line=dict(color='#ffb74d', width=2)))
                fig_candle.update_layout(title=f"{secilen_grafik_adi} - Günlük Mum Grafiği", height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig_candle, use_container_width=True)
    else:
        tv_sembol_son_hali = st.text_input("💡 TradingView Sembol Kodu:", value=f"BIST:{secilen_grafik_adi}" if "-" not in secilen_grafik_adi else secilen_grafik_adi)
        tv_widget = f"""<div class="tradingview-widget-container" style="height:100%;width:100%"><div id="tv_chart_custom" style="height: 600px;"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script type="text/javascript">new TradingView.widget({{"autosize": true, "symbol": "{tv_sembol_son_hali}", "interval": "D", "timezone": "Europe/Istanbul", "theme": "dark", "style": "1", "locale": "tr", "enable_publishing": false, "backgroundColor": "rgba(0, 0, 0, 1)", "container_id": "tv_chart_custom"}});</script></div>"""
        components.html(tv_widget, height=600)

# --- GİZLİ PATRON MODU EKRANI ---
if aktif_kullanici == "patron":
    with sekmeler[5]:
        st.subheader("👑 Sistemdeki Tüm Hesaplar ve Portföyler (God Mode)")
        st.markdown("Aşağıda bu terminali kullanan herkesin oluşturduğu gizli listeleri ve portföy verilerini canlı olarak görüyorsun:")
        
        # Sadece Patronun görebileceği çiğ veritabanı dökümü
        st.json(tum_veritabani)