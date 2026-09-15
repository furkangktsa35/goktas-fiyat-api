from flask import Flask, request, jsonify
import math

app = Flask(__name__)

# =========================
# GOKTAS FIYAT MOTORU
# =========================

MDFLAM_TABAKA = 3500
ARKALIK_TABAKA = 1500
PVC_METRE = 15
MENTESE = 150
FRENLI_RAY = 350
TELESKOPIK_RAY = 250
KULP = 100
ASKI_BORUSU_METRE = 250
SARF_M2 = 300
NAKLIYE = 1000

AYNA_M2 = 4000
VAKUM_CNC_M2 = 5200
LAKE_M2 = 5200
ALUMINYUM_M2 = 5200
LED_METRE = 1600
LAMBRI_ADET = 700

GUNLUK_GIDER = 10000

UZAK_ILCELER = {
    "urla", "çeşme", "cesme", "seferihisar",
    "foça", "foca", "aliağa", "aliaga",
    "torbalı", "torbali", "menderes"
}


def yukari_bin(tutar):
    return int(math.ceil(tutar / 1000.0) * 1000)


def sayi(v, default=0):
    try:
        return float(v)
    except:
        return default


def kar_hedefi(gun):
    if gun <= 1:
        return 20000
    elif gun <= 1.5:
        return 25000
    elif gun <= 2:
        return 30000
    elif gun <= 2.5:
        return 40000
    elif gun <= 3:
        return 50000
    else:
        return 60000


def gardrop_gun(genislik_cm):
    metre = genislik_cm / 100

    if metre <= 2:
        return 1
    elif metre <= 4:
        return 1.5
    elif metre <= 5:
        return 2
    elif metre <= 6:
        return 3
    elif metre <= 7:
        return 3.5
    else:
        return 4


def gardrop_hesap(data):
    en = sayi(data.get("genislik"))
    boy = sayi(data.get("yukseklik"))
    derinlik = sayi(data.get("derinlik"), 60)

    cekmece = int(sayi(data.get("cekmece"), 4))
    led = sayi(data.get("led_metre"), 0)
    lambri = int(sayi(data.get("lambri_adet"), 0))

    kapak_turu = str(data.get("kapak_turu", "mdflam")).lower()
    ilce = str(data.get("ilce", "")).lower()

    sokum = bool(data.get("sokum", False))
    fatura = bool(data.get("fatura", False))
    taksit = int(sayi(data.get("taksit"), 1))
    nakit_indirim = bool(data.get("nakit_indirim", False))

    if en <= 0 or boy <= 0 or derinlik <= 0:
        return {"hata": "Genişlik, yükseklik ve derinlik gerekli."}

    on_alan = (en / 100) * (boy / 100)

    # Yaklaşık modül hesabı
    modul = max(1, math.ceil(en / 80))

    # Her modülü ayrı gövdeli kabul ediyoruz.
    # 2 yan + yaklaşık 5 yatay parça/modül
    yan_alan = modul * 2 * (boy / 100) * (derinlik / 100)
    yatay_alan = modul * 5 * (0.76) * (derinlik / 100)

    # 10 cm baza için yaklaşık malzeme
    baza_alan = (en / 100) * 0.10

    govde_alan = yan_alan + yatay_alan + baza_alan

    # MDFLAM standart kapak
    kapak_alan = on_alan

    alternatif_kapak = 0

    if kapak_turu in ["ayna", "aynalı", "aynali"]:
        alternatif_kapak = kapak_alan * AYNA_M2
        kapak_mdflam = 0
    elif kapak_turu in ["vakum", "cnc", "vakum cnc"]:
        alternatif_kapak = kapak_alan * VAKUM_CNC_M2
        kapak_mdflam = 0
    elif kapak_turu in ["lake"]:
        alternatif_kapak = kapak_alan * LAKE_M2
        kapak_mdflam = 0
    elif kapak_turu in ["alüminyum", "aluminyum"]:
        alternatif_kapak = kapak_alan * ALUMINYUM_M2
        kapak_mdflam = 0
    else:
        kapak_mdflam = kapak_alan

    # Çekmece kutuları için yaklaşık MDFLAM
    cekmece_alan = cekmece * 0.65

    toplam_mdflam_alan = (
        govde_alan +
        kapak_mdflam +
        cekmece_alan
    )

    # Önce gerçek kullanım alanına %10 fire,
    # sonra tabaka adedi yukarı yuvarlanır.
    toplam_mdflam_alan *= 1.10

    tabaka_alan = 2.10 * 2.80
    mdflam_adet = math.ceil(toplam_mdflam_alan / tabaka_alan)

    mdflam_maliyet = mdflam_adet * MDFLAM_TABAKA

    # Arkalık
    arkalik_alan = on_alan * 1.10
    arkalik_adet = math.ceil(arkalik_alan / tabaka_alan)
    arkalik_maliyet = arkalik_adet * ARKALIK_TABAKA

    # Kapak adedi
    kapak_adet = max(1, math.ceil(en / 55))

    # Uzun gardırop kapağında 6 menteşe
    if boy >= 220:
        mentese_kapak = 6
    elif boy >= 180:
        mentese_kapak = 5
    elif boy >= 150:
        mentese_kapak = 4
    else:
        mentese_kapak = 3

    mentese_maliyet = kapak_adet * mentese_kapak * MENTESE

    # Alternatif kapakta kulp varsayımı korunuyor
    kulp_adet = kapak_adet + cekmece
    kulp_maliyet = kulp_adet * KULP

    ray_maliyet = cekmece * FRENLI_RAY

    # Varsayılan 80 cm modülde 2 askı borusu
    aski_metre = modul * 2 * 0.76
    aski_maliyet = aski_metre * ASKI_BORUSU_METRE

    # Görünen kenarlar için yaklaşık PVC
    pvc_metre = (en / 100) * 4 + modul * (derinlik / 100) * 8
    pvc_maliyet = pvc_metre * PVC_METRE

    sarf = on_alan * SARF_M2

    malzeme = (
        mdflam_maliyet +
        arkalik_maliyet +
        mentese_maliyet +
        kulp_maliyet +
        ray_maliyet +
        aski_maliyet +
        pvc_maliyet +
        sarf +
        NAKLIYE +
        alternatif_kapak +
        led * LED_METRE +
        lambri * LAMBRI_ADET
    )

    gun = gardrop_gun(en)
    gider = gun * GUNLUK_GIDER
    kar = kar_hedefi(gun)

    hesaplanan = malzeme + gider + kar

    # Gardırop piyasa kontrolü: 9-12 bin TL/m2
    piyasa_min = on_alan * 9000
    piyasa_max = on_alan * 12000

    # Gerçek maliyet hesabı piyasa tabanından düşükse
    # taban fiyat korunur.
    satis = max(hesaplanan, piyasa_min)

    # Uzak ilçe
    if ilce in UZAK_ILCELER:
        satis *= 1.10

    # Söküm
    if sokum:
        satis *= 1.05

    # Nakit indirimi sadece açıkça istenirse
    if nakit_indirim and taksit <= 1:
        satis *= 0.95

    # Kart taksit farkı
    taksit_oranlari = {
        2: 0.03,
        3: 0.06,
        4: 0.09,
        5: 0.12,
        6: 0.15
    }

    if taksit in taksit_oranlari:
        satis *= (1 + taksit_oranlari[taksit])

    # Fatura
    if fatura:
        satis *= 1.20

    satis = yukari_bin(satis)

    return {
        "urun": "gardrop",
        "genislik_cm": en,
        "yukseklik_cm": boy,
        "derinlik_cm": derinlik,
        "alan_m2": round(on_alan, 2),
        "mdflam_tabaka": mdflam_adet,
        "arkalik_tabaka": arkalik_adet,
        "is_gunu": gun,
        "tahmini_malzeme": round(malzeme),
        "isletme_gideri": round(gider),
        "hedef_kar": round(kar),
        "piyasa_min": yukari_bin(piyasa_min),
        "piyasa_max": yukari_bin(piyasa_max),
        "fiyat": satis,
        "musteri_mesaji": f"Yaklaşık fiyatımız {satis:,.0f} TL'dir."
    }


def vestiyer_hesap(data):
    # Aynı gerçek maliyet mantığı.
    # Sadece piyasa kontrol bandı 8-11 bin TL/m2.
    sonuc = gardrop_hesap(data)

    if "hata" in sonuc:
        return sonuc

    alan = sonuc["alan_m2"]

    piyasa_min = alan * 8000
    piyasa_max = alan * 11000

    # Gardırop fonksiyonundaki 9k tabanı kaldırıp
    # gerçek hesap değerini tekrar oluşturuyoruz.
    gercek_hesap = (
        sonuc["tahmini_malzeme"] +
        sonuc["isletme_gideri"] +
        sonuc["hedef_kar"]
    )

    satis = max(gercek_hesap, piyasa_min)

    ilce = str(data.get("ilce", "")).lower()
    sokum = bool(data.get("sokum", False))
    fatura = bool(data.get("fatura", False))
    taksit = int(sayi(data.get("taksit"), 1))
    nakit_indirim = bool(data.get("nakit_indirim", False))

    if ilce in UZAK_ILCELER:
        satis *= 1.10

    if sokum:
        satis *= 1.05

    if nakit_indirim and taksit <= 1:
        satis *= 0.95

    taksit_oranlari = {
        2: 0.03, 3: 0.06, 4: 0.09,
        5: 0.12, 6: 0.15
    }

    if taksit in taksit_oranlari:
        satis *= (1 + taksit_oranlari[taksit])

    if fatura:
        satis *= 1.20

    satis = yukari_bin(satis)

    sonuc["urun"] = "vestiyer"
    sonuc["piyasa_min"] = yukari_bin(piyasa_min)
    sonuc["piyasa_max"] = yukari_bin(piyasa_max)
    sonuc["fiyat"] = satis
    sonuc["musteri_mesaji"] = f"Yaklaşık fiyatımız {satis:,.0f} TL'dir."

    return sonuc


def mutfak_hesap(data):
    alt_metre = sayi(data.get("alt_metre"))
    ust_metre = sayi(data.get("ust_metre"))

    if alt_metre <= 0 and ust_metre <= 0:
        return {"hata": "Alt veya üst dolap metresi gerekli."}

    toplam_metre = alt_metre + ust_metre

    # Mutfak piyasa sistemi:
    # toplam alt + üst metre x 9-12 bin TL
    minimum = toplam_metre * 9000
    maksimum = toplam_metre * 12000

    # Standart fiyat yaklaşık orta seviyede:
    # 10.500 TL / metre
    satis = toplam_metre * 10500

    kapak_turu = str(data.get("kapak_turu", "mdflam")).lower()

    # Standart dışı kapaklarda yaklaşık kapak alanı üzerinden
    # fark eklenir. MDFLAM kapak zaten standart fiyatta var.
    tahmini_kapak_alani = (
        alt_metre * 0.77 +
        ust_metre * 0.85
    )

    if kapak_turu in ["vakum", "cnc", "vakum cnc"]:
        satis += tahmini_kapak_alani * 1200
    elif kapak_turu == "lake":
        satis += tahmini_kapak_alani * 1200
    elif kapak_turu in ["alüminyum", "aluminyum"]:
        satis += tahmini_kapak_alani * 1200

    led = sayi(data.get("led_metre"), 0)
    satis += led * LED_METRE

    ilce = str(data.get("ilce", "")).lower()
    sokum = bool(data.get("sokum", False))
    fatura = bool(data.get("fatura", False))
    taksit = int(sayi(data.get("taksit"), 1))
    nakit_indirim = bool(data.get("nakit_indirim", False))

    if ilce in UZAK_ILCELER:
        satis *= 1.10

    if sokum:
        satis *= 1.05

    if nakit_indirim and taksit <= 1:
        satis *= 0.95

    taksit_oranlari = {
        2: 0.03, 3: 0.06, 4: 0.09,
        5: 0.12, 6: 0.15
    }

    if taksit in taksit_oranlari:
        satis *= (1 + taksit_oranlari[taksit])

    if fatura:
        satis *= 1.20

    satis = yukari_bin(satis)

    return {
        "urun": "mutfak",
        "alt_metre": alt_metre,
        "ust_metre": ust_metre,
        "toplam_metre": toplam_metre,
        "piyasa_min": yukari_bin(minimum),
        "piyasa_max": yukari_bin(maksimum),
        "fiyat": satis,
        "tezgah_dahil": False,
        "musteri_mesaji": f"Yaklaşık fiyatımız {satis:,.0f} TL'dir. Tezgâh fiyata dahil değildir."
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "durum": "ok",
        "servis": "Goktas Ic Mekan Fiyat API"
    })


@app.route("/fiyat-hesapla", methods=["POST"])
def fiyat_hesapla():
    data = request.get_json(silent=True) or {}

    urun = str(data.get("urun", "")).lower().strip()

    if urun in [
        "gardrop", "gardırop",
        "kiyafet dolabi", "kıyafet dolabı"
    ]:
        sonuc = gardrop_hesap(data)

    elif urun in [
        "vestiyer", "portmanto",
        "ayakkabilik", "ayakkabılık"
    ]:
        sonuc = vestiyer_hesap(data)

    elif urun in [
        "mutfak", "mutfak dolabi", "mutfak dolabı"
    ]:
        sonuc = mutfak_hesap(data)

    else:
        return jsonify({
            "hata": "Bu ürün için otomatik fiyat tanımlı değil.",
            "furkana_yonlendir": True
        }), 400

    return jsonify(sonuc)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
