# Arunika Office

Paket perkantoran bawaan **Arunika Linux**: fork [LibreOffice](https://github.com/LibreOffice/core)
26.8 dengan antarmuka yang dibuat semirip mungkin dengan Microsoft Office 365.

| Aplikasi | Modul LibreOffice | Ribbon | Aksen |
|---|---|---|---|
| Arunika Dokumen | Writer | File · Beranda · Sisipkan · Menggambar · Desain · Tata Letak · Referensi · Surat · Tinjau · Tampilan · Bantuan | `#185ABD` |
| Arunika Lembar Kerja | Calc | File · Beranda · Sisipkan · Menggambar · Tata Letak Halaman · Rumus · Data · Tinjau · Tampilan · Bantuan | `#107C41` |
| Arunika Presentasi | Impress | File · Beranda · Sisipkan · Menggambar · Desain · Transisi · Animasi · Peragaan Slide · Tinjau · Tampilan · Bantuan | `#C43E1C` |

## Yang diubah dari LibreOffice

- **Ribbon ala Office** (`arunika/ribbon/`): generator yang menyusun tab → grup → tombol persis
  seperti Word/Excel/PowerPoint (tombol besar 32 px dengan label di bawah, tumpukan tombol kecil,
  nama grup di bawah, grup menciut saat jendela sempit). Hasilnya `notebookbar_arunika.ui` untuk
  Writer, Calc, Impress, dan menjadi mode UI bawaan "Ribbon (Office)". Tab kontekstual
  (Tabel, Format Gambar, Format Bentuk, …) muncul otomatis seperti di Office.
- **Tampilan tab** (`vcl/source/control/tabctrl.cxx`, `notebookbar.cxx`): tab datar, garis bawah
  berwarna aksen pada tab aktif, tab kontekstual berwarna aksen, latar ribbon putih (gelap saat
  dark mode), keterangan grup abu-abu.
- **Label kustom** (`vcl/source/window/builder.cxx`): label di `.ui` menimpa label perintah UNO,
  sehingga tombol bertuliskan "Tabel", "Margin", "Pewarna Format" — bukan "Insert Table...".
- **Bawaan Office**: simpan sebagai .docx/.xlsx/.pptx tanpa peringatan format, templat
  `Normal.ott`/`Book.ots`/`Blank.otp` (Carlito 11 pt, spasi Word 2013+, margin 2,54 cm, kolom
  Excel 64 px, slide 16:9), ikon Colibre, tanpa Tip of the Day.
- **Judul & nama**: "Dokumen1 - Arunika Dokumen", "Buku1 - Arunika Lembar Kerja",
  "Presentasi1 - Arunika Presentasi"; WM_CLASS `arunika-<app>` cocok dengan berkas `.desktop`.
- **Start Center**: "Dokumen Kosong", "Buku Kerja Kosong", "Presentasi Kosong", area terang.
- **Branding & ikon** (`arunika/branding`, `arunika/icons`): splash, logo, ikon gaya Fluent.
- **Bahasa Indonesia**: semua label baru diterjemahkan (`arunika/l10n`, spesifikasi ribbon).

Ikon, nama, dan logo Microsoft **tidak** disalin: ikon perintah memakai tema Colibre (MPL),
ikon aplikasi digambar sendiri, dan nama produk memakai istilah generik Bahasa Indonesia.

## Membangun

Tanpa root — build-deps diunduh ke `../sysroot` lalu di-overlay ke `/usr` di user namespace:

```bash
arunika/build.sh --deps          # pertama kali: unduh build-deps, configure, make, paket .deb
arunika/build.sh                 # selanjutnya (incremental)
```

Hasil: `~/aruni-build/debs-out/arunika-office_<versi>_amd64.deb`, lalu terbitkan ke
`repo.arunika.cloud` dengan `packaging/publish.sh debs` dari repo `aruni-os`.

Pratinjau ribbon tanpa build (memakai LibreOffice sistem di Xvfb):

```bash
python3 arunika/tools/preview-tab.py word Insert /tmp/insert.png
```

Mengubah ribbon: sunting `arunika/ribbon/{word,excel,powerpoint}.py`, jalankan
`python3 arunika/ribbon/generate.py` (memvalidasi perintah UNO dan ikon).

## Lisensi

MPL-2.0, sama dengan LibreOffice. Berbasis kode The Document Foundation dan kontributor LibreOffice.
