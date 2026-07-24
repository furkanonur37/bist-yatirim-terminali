import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
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
st.set_page_config(page_title="Yatırım Terminali BOSS SEVİYESİ", layout="wide")
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
        pass

st.markdown("---")

# --- GELİŞMİŞ VERİ TABANI ---
def portfoyu_yukle():
    if not os.path.exists(VERI_DOSYASI):
        return {"Ana Portföy": {}, "Geçmiş İşlemler": []} 
    with open(VERI_DOSYASI, "r") as file:
        data = json.load(file)
    if "Geçmiş İşlemler" not in data:
        data["Geçmiş İşlemler"] = []
    if "Ana Portföy" not in data and len(data) > 0 and isinstance(list(data.values())[0], dict) and "Adet" in list(data.values())[0]:
        yeni_format = {"Ana Portföy": data, "Geçmiş İşlemler": []}
        portfoyu_kaydet(yeni_format)
        return yeni_format
    return data

def portfoyu_kaydet(data):
    with open(VERI_DOSYASI, "w") as file:
        json.dump(data, file, indent=4)

portfoyler = portfoyu_yukle()
guncel_listeler = [k for k in portfoyler.keys() if k != "Geçmiş İşlemler"]

# --- SİDEBAR: LİSTE VE VARLIK YÖNETİMİ ---
st.sidebar.title("🗂️ Terminal Yönetimi")

yeni_liste_adi = st.sidebar.text_input("Yeni Liste Oluştur", placeholder="Örn: Bebek Hisseler...")
if st.sidebar.button("➕ Liste Ekle") and yeni_liste_adi:
    if yeni_liste_adi not in portfoyler:
        portfoyler[yeni_liste_adi] = {}
        portfoyu_kaydet(portfoyler)
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
    portfoyu_kaydet(portfoyler) 
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
        portfoyu_kaydet(portfoyler)
        st.rerun()

bist_populer = ["AKBNK.IS", "ASELS.IS", "BIMAS.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "ISCTR.IS", "KCHOL.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS", "YKBNK.IS"]

def soft_color_kâr(val):
    if val > 0: return 'color: #81c784; font-weight: 500; background-color: rgba(129, 199, 132, 0.1)'
    elif val < 0: return 'color: #e57373; font-weight: 500; background-color: rgba(229, 115, 115, 0.1)'
    else: return 'color: #9e9e9e; font-weight: 500'

# --- ANA EKRAN SEKMELERİ ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([f"📊 {aktif_liste} Özeti", "🤖 Zeka Asistanı", "🏆 Geçmiş", "📈 Canlı Grafik", "⚙️ İleri Analiz (DCA & Simülasyon)", "📸 Profesyonel Rapor"])

with tab1:
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
                
                veri_listesi.append({
                    "VARLIK": v.replace(".IS", ""), "ADET": adet, "MALİYET": maliyet, 
                    "GÜNCEL FİYAT": guncel_fiyat, "KÂR/ZARAR": kar_zarar, 
                    "KÂR(%)": kar_yuzde, "TOPLAM DEĞER": guncel_deger, 
                    "HACİM": f"{gunluk_hacim:,}", "TREND": "🟢 SMA Üstü" if guncel_fiyat > sma20 else "🔴 Negatif", "DURUM": durum
                })
            except: pass
                
        if hedef_vuruldu and 'kutlama' not in st.session_state:
            st.balloons()
            st.session_state['kutlama'] = True
            
        if veri_listesi:
            df_portfoy = pd.DataFrame(veri_listesi)
            top_kasa = df_portfoy["TOPLAM DEĞER"].sum()
            top_kar = df_portfoy["KÂR/ZARAR"].sum()
            top_maliyet_genel = top_kasa - top_kar
            genel_kar_yuzde = (top_kar / top_maliyet_genel) * 100 if top_maliyet_genel > 0 else 0
            
            col1, col2 = st.columns(2)
            col1.metric("LİSTE TOPLAM DEĞERİ", f"{top_kasa:,.2f} ₺")
            col2.metric("LİSTE NET KÂR/ZARAR", f"{top_kar:,.2f} ₺", f"% {genel_kar_yuzde:,.2f}")
            
            st.markdown("---")
            st.dataframe(df_portfoy.style.map(soft_color_kâr, subset=['KÂR/ZARAR', 'KÂR(%)']).format({"MALİYET": "{:.2f} ₺", "GÜNCEL FİYAT": "{:.2f} ₺", "KÂR/ZARAR": "{:.2f} ₺", "KÂR(%)": "% {:.2f}", "TOPLAM DEĞER": "{:.2f} ₺"}), width="stretch", hide_index=True)
            
            # Ortak veriler
            st.session_state['yapay_zeka_verisi'] = df_portfoy
            st.session_state['toplam_kasa'] = top_kasa
            st.session_state['toplam_kar'] = top_kar
            st.session_state['genel_kar_yuzde'] = genel_kar_yuzde

with tab2:
    st.subheader("🤖 Portföy Zeka Asistanı")
    if 'yapay_zeka_verisi' in st.session_state and not st.session_state['yapay_zeka_verisi'].empty:
        df_yz = st.session_state['yapay_zeka_verisi']
        toplam_kasa = st.session_state['toplam_kasa']
        uyari_sayisi = 0
        for idx, row in df_yz.iterrows():
            agirlik = (row['TOPLAM DEĞER'] / toplam_kasa) * 100
            if agirlik > 40:
                st.warning(f"⚠️ **Konsantrasyon Riski ({row['VARLIK']}):** Portföyün **%{agirlik:.1f}'si**. Sepeti çeşitlendirmek güvenlidir.")
                uyari_sayisi += 1
            if row['TREND'] == "🔴 Negatif":
                st.info(f"📉 **Teknik Zayıflık ({row['VARLIK']}):** Hisse 20 günlük ortalamasının altında, güç toplaması gerekebilir.")
                uyari_sayisi += 1
            if row['KÂR(%)'] < -15:
                st.error(f"🩸 **Stop-Loss ({row['VARLIK']}):** %15'ten fazla zarar. Sermaye koruma stratejisini düşün.")
                uyari_sayisi += 1
        if uyari_sayisi == 0: st.success("✅ Portföy mühendislik harikası gibi optimize! Risk dağılımı harika.")
    else: st.info("Veri yok.")

with tab3:
    st.subheader("🏆 Arşiv & İstatistikler")
    gecmis = portfoyler.get("Geçmiş İşlemler", [])
    if len(gecmis) > 0:
        df_gecmis = pd.DataFrame(gecmis)
        toplam_realize_kar = df_gecmis["Kâr/Zarar"].sum()
        basarili_islem = len(df_gecmis[df_gecmis["Kâr/Zarar"] > 0])
        win_rate = (basarili_islem / len(gecmis)) * 100
        st.session_state['win_rate'] = win_rate # Rapor için
        c1, c2, c3 = st.columns(3)
        c1.metric("Gerçekleşen Kâr", f"{toplam_realize_kar:,.2f} ₺")
        c2.metric("İşlem Sayısı", f"{len(gecmis)} Adet")
        c3.metric("Kazanma Oranı (Win-Rate)", f"% {win_rate:.1f}")
        st.markdown("---")
        st.dataframe(df_gecmis, width="stretch", hide_index=True)
    else: st.info("Henüz kapatılmış işlem yok.")

with tab4:
    st.subheader("📈 Profesyonel Canlı Grafik Terminali")
    kullanici_hisseleri = [h.replace(".IS", "") for h in aktif_portfoy.keys()]
    tum_grafik_secenekleri = sorted(list(set(kullanici_hisseleri + [h.replace(".IS", "") for h in bist_populer])))
    col_secim, col_motor = st.columns([1, 1])
    secilen_grafik_adi = col_secim.selectbox("🔍 Grafiğini Açmak İstediğin Varlığı Seç:", tum_grafik_secenekleri)
    grafik_motoru = col_motor.radio("⚙️ Motor:", ["Yerli Motor (BİST Uyumlu)", "TradingView"], horizontal=True)
    if grafik_motoru == "Yerli Motor (BİST Uyumlu)":
        with st.spinner("Grafik hazırlanıyor..."):
            yf_kod = f"{secilen_grafik_adi}.IS" if "-" not in secilen_grafik_adi else secilen_grafik_adi
            mum_veri = yf.download(yf_kod, period="6mo", progress=False)
            if not mum_veri.empty:
                fig_candle = go.Figure(data=[go.Candlestick(x=mum_veri.index, open=mum_veri['Open'].squeeze(), high=mum_veri['High'].squeeze(), low=mum_veri['Low'].squeeze(), close=mum_veri['Close'].squeeze(), increasing_line_color='#26a69a', decreasing_line_color='#ef5350')])
                sma20 = mum_veri['Close'].squeeze().rolling(window=20).mean()
                fig_candle.add_trace(go.Scatter(x=mum_veri.index, y=sma20, mode='lines', name='SMA 20 (Trend)', line=dict(color='#ffb74d', width=2)))
                fig_candle.update_layout(title=f"{secilen_grafik_adi} Mum Grafiği", height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig_candle, use_container_width=True)
    else:
        tv_sembol = f"BIST:{secilen_grafik_adi}" if "-" not in secilen_grafik_adi else secilen_grafik_adi
        tv_sembol_son_hali = st.text_input("💡 Kod:", value=tv_sembol)
        tv_widget = f'<div class="tradingview-widget-container" style="height:600px;width:100%"><div id="tv_chart_custom" style="height: 100%;"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script type="text/javascript">new TradingView.widget({{"autosize": true, "symbol": "{tv_sembol_son_hali}", "interval": "D", "theme": "dark", "style": "1", "locale": "tr", "container_id": "tv_chart_custom"}});</script></div>'
        components.html(tv_widget, height=600)

# SEKME 5: MONTE CARLO & DCA SİHİRBAZI
with tab5:
    st.subheader("⚙️ İleri Düzey Mühendislik Analizleri")
    
    col_dca, col_mc = st.columns(2)
    
    with col_dca:
        st.markdown("### 🧮 Maliyet Düşürme (DCA) Sihirbazı")
        st.markdown("*Zararda olduğun hissede hedefine ulaşmak için ne kadar lot/nakit gerektiğini hesaplar.*")
        if not aktif_portfoy:
            st.info("Portföy boş.")
        else:
            secili_hisse = st.selectbox("Hisse Seçin", list(aktif_portfoy.keys()), format_func=lambda x: x.replace(".IS", ""))
            hedef_maliyet = st.number_input("İnmek İstediğiniz Hedef Maliyet (₺)", min_value=0.01, step=0.1, value=float(aktif_portfoy[secili_hisse]["Maliyet"]))
            
            if st.button("Hesapla"):
                hisse_obj = aktif_portfoy[secili_hisse]
                mevcut_maliyet = hisse_obj["Maliyet"]
                mevcut_adet = hisse_obj["Adet"]
                
                try:
                    anlik_fiyat = float(yf.download(secili_hisse, period="1d", progress=False)['Close'].iloc[-1])
                    if anlik_fiyat >= mevcut_maliyet:
                        st.success(f"Bu hissede zaten kârdasın (Fiyat: {anlik_fiyat:.2f} ₺ > Maliyet: {mevcut_maliyet:.2f} ₺). Maliyet düşürmeye gerek yok!")
                    elif hedef_maliyet >= mevcut_maliyet:
                        st.warning("Hedef maliyetiniz, mevcut maliyetinizden düşük olmalıdır.")
                    elif anlik_fiyat >= hedef_maliyet:
                        st.error(f"Hissenin anlık fiyatı ({anlik_fiyat:.2f} ₺), inmek istediğiniz hedeften yüksek. Matematiksel olarak ulaşılamaz.")
                    else:
                        gerekli_adet = (mevcut_adet * (mevcut_maliyet - hedef_maliyet)) / (hedef_maliyet - anlik_fiyat)
                        gerekli_nakit = gerekli_adet * anlik_fiyat
                        st.success(f"✅ **Hedef Maliyet ({hedef_maliyet:.2f} ₺) İçin Gerekenler:**")
                        st.write(f"- Alınması Gereken Yeni Lot: **{int(gerekli_adet):,} Adet**")
                        st.write(f"- Gereken Ek Nakit: **{gerekli_nakit:,.2f} ₺**")
                        st.write(f"- İşlem Sonrası Toplam Lot: **{int(mevcut_adet + gerekli_adet):,} Adet**")
                except:
                    st.error("Fiyat çekilemedi.")

    with col_mc:
        st.markdown("### 🎲 Monte Carlo Gelecek Simülasyonu")
        st.markdown("*Mevcut kasanın 1 yıllık (252 işlem günü) istatistiksel projeksiyonu.*")
        beklenen_getiri = st.slider("Tahmini Yıllık Büyüme (%)", min_value=0, max_value=200, value=60)
        volatilite = st.slider("Portföy Dalgalanması (Volatilite %)", min_value=10, max_value=100, value=30)
        
        if st.button("Simülasyonu Başlat"):
            if 'toplam_kasa' in st.session_state and st.session_state['toplam_kasa'] > 0:
                kasa = st.session_state['toplam_kasa']
                gunluk_getiri = (beklenen_getiri / 100) / 252
                gunluk_volatilite = (volatilite / 100) / np.sqrt(252)
                
                sim_sayisi = 500
                gun_sayisi = 252
                sonuclar = []
                
                # İstatistiksel Yürüyüş Motoru
                for i in range(sim_sayisi):
                    fiyat_yolu = [kasa]
                    for d in range(gun_sayisi):
                        # Rastgele şok + trend
                        sok = np.random.normal(0, 1)
                        degisim = gunluk_getiri + gunluk_volatilite * sok
                        yeni_deger = fiyat_yolu[-1] * (1 + degisim)
                        fiyat_yolu.append(yeni_deger)
                    sonuclar.append(fiyat_yolu[-1])
                
                percentile_10 = np.percentile(sonuclar, 10)
                percentile_50 = np.percentile(sonuclar, 50)
                percentile_90 = np.percentile(sonuclar, 90)
                
                st.write(f"💵 **Güncel Kasa:** {kasa:,.2f} ₺")
                st.error(f"🌪️ En Kötü Senaryo (Alt %10): **{percentile_10:,.2f} ₺**")
                st.warning(f"⚖️ Ortalama Beklenti (Medyan): **{percentile_50:,.2f} ₺**")
                st.success(f"🚀 En İyi Senaryo (Üst %10): **{percentile_90:,.2f} ₺**")
            else:
                st.warning("Simülasyon için portföyde varlık bulunmalıdır.")

# SEKME 6: PROFESYONEL KARİYER RAPORU
with tab6:
    st.subheader("📸 Profesyonel Performans Raporu (Export)")
    st.markdown("*Mac'inde Command (⌘) + Shift + 4 yaparak bu şık alanı kesip direkt LinkedIn'de, 'Python & Streamlit ile kendi fon yönetim algoritmamı yazdım' notuyla paylaşabilirsin.*")
    
    if 'toplam_kasa' in st.session_state:
        rapor_kasa = st.session_state['toplam_kasa']
        rapor_kar = st.session_state['toplam_kar']
        rapor_yuzde = st.session_state['genel_kar_yuzde']
        rapor_win = st.session_state.get('win_rate', 0.0)
        
        # HTML ile özel şık bir Rapor Kartı çizimi
        rapor_html = f"""
        <div style="background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); color: #ffffff; font-family: 'Helvetica Neue', sans-serif; border: 1px solid #444; max-width: 800px; margin: auto;">
            <div style="text-align: center; border-bottom: 2px solid #81c784; padding-bottom: 20px; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #81c784; font-weight: 300; letter-spacing: 2px;">QUANTITATIVE ALGORITHMIC PORTFOLIO</h2>
                <p style="margin: 5px 0 0 0; color: #aaa; font-size: 14px;">Automated Tracking & Analysis System</p>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
                <div style="text-align: center; width: 33%;">
                    <h4 style="margin: 0; color: #aaa; font-size: 12px; text-transform: uppercase;">Total Asset Value</h4>
                    <p style="margin: 10px 0 0 0; font-size: 28px; font-weight: bold;">{rapor_kasa:,.2f} ₺</p>
                </div>
                <div style="text-align: center; width: 33%; border-left: 1px solid #444; border-right: 1px solid #444;">
                    <h4 style="margin: 0; color: #aaa; font-size: 12px; text-transform: uppercase;">Net Profit / Loss</h4>
                    <p style="margin: 10px 0 0 0; font-size: 28px; font-weight: bold; color: {'#81c784' if rapor_kar > 0 else '#e57373'};">{rapor_kar:,.2f} ₺</p>
                </div>
                <div style="text-align: center; width: 33%;">
                    <h4 style="margin: 0; color: #aaa; font-size: 12px; text-transform: uppercase;">Return on Investment</h4>
                    <p style="margin: 10px 0 0 0; font-size: 28px; font-weight: bold; color: {'#81c784' if rapor_yuzde > 0 else '#e57373'};">% {rapor_yuzde:,.2f}</p>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-around; background-color: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;">
                <div style="text-align: center;">
                    <span style="font-size: 12px; color: #aaa;">ALGORITHM WIN-RATE</span><br>
                    <span style="font-size: 20px; font-weight: bold; color: #64b5f6;">% {rapor_win:,.1f}</span>
                </div>
                <div style="text-align: center;">
                    <span style="font-size: 12px; color: #aaa;">SYSTEM UPTIME</span><br>
                    <span style="font-size: 20px; font-weight: bold; color: #ffb74d;">100% ONLINE</span>
                </div>
            </div>
            <div style="text-align: center; margin-top: 20px; font-size: 10px; color: #666;">
                Generated by Python, Pandas & Streamlit | Industrial Engineering Precision
            </div>
        </div>
        """
        components.html(rapor_html, height=450)
    else:
        st.info("Rapor oluşturabilmek için portföyünüze veri eklemeniz gerekmektedir.")