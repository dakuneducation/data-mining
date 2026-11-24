# Speaker Notes

## Slide 1: (cover)

Buka dengan pertanyaan: kalau dua model sama-sama akurasi 98%, apakah keduanya sama baiknya? Jawabannya tidak selalu, dan itu inti penelitian ini.

## Slide 2: Akurasi Sama, Risiko Klinis Bisa Berbeda

Tekankan penyebut: akurasi dibagi 113, sensitivitas dibagi 42. Satu kasus ganas yang terlewat menggeser sensitivitas hampir tiga kali lebih besar daripada akurasi.

## Slide 3: Dataset: Breast Cancer Wisconsin (Diagnostic)

Fitur worst nanti muncul lagi sebagai feature importance teratas Random Forest.

## Slide 4: Alur Metodologi End-to-End di R

Rujukan data leakage: Kapoor dan Narayanan (2023).

## Slide 5: Enam Metode dan Konfigurasi Pelatihan

k pada KNN mengatur jumlah neighbors; mtry pada RF mengatur jumlah fitur kandidat per split; jumlah trees tetap 500.

## Slide 6: Soft Voting: Rata-rata Probabilitas, Threshold Keputusan

Random Forest dinilai sebagai ensemble tersendiri, bukan anggota voting.

## Slide 7: Membaca Metrik: Penyebut Menentukan Makna

Sensitivitas dan presisi punya penyebut berbeda, jadi bisa berbeda meski akurasi tinggi.

## Slide 8: Eksplorasi Data: Ukuran Inti Sel Membedakan Kelas

Median hanya dipakai untuk deskripsi data, bukan untuk memilih fitur atau menetapkan threshold.

## Slide 9: Cross Validation: SVM Tertinggi, RF dan SVM Paling Stabil

Fold yang sama dipakai semua model, jadi turunnya AUC di fold 2 terjadi pada observasi validasi yang sama. Mean AUC CV menggambarkan proses pemilihan model, bukan estimasi bebas bias.

## Slide 10: Tuning Hiperparameter: KNN dan SVM

Gambar diambil dari folder output/plots hasil 04_visualisasi.R (300 DPI).

## Slide 11: Data Uji: Tiga Metode dengan Akurasi Sama 98,23%

Voting tidak mengungguli KNN pada akurasi.

## Slide 12: Sensitivitas, Spesifisitas, dan Presisi

Presisi 1,0 tidak berarti model aman: ia hanya bicara tentang prediksi ganas yang dibuat, bukan yang terlewat.

## Slide 13: Jenis dan Jumlah Kesalahan pada 113 Sampel Uji

NB dan SVM akurasinya sama (0,9735) tetapi Kappa berbeda karena distribusi kelas prediksinya berbeda. Pengujian selisih antarmodel memerlukan paired test pada sampel yang sama.

## Slide 14: Feature Importance Random Forest

Hati-hati dengan klaim kausal: peringkat Gini impurity bukan pengaruh biologis terpisah.

## Slide 15: Keterbatasan dan Ketidakpastian Estimasi

Sumber: Collins dkk. (2024) BMJ, TRIPOD+AI, Riley dkk., Moons dkk. PROBAST+AI.

## Slide 16: Kesimpulan

Tutup dengan pesan inti: pilih model berdasarkan jenis kesalahan yang diprioritaskan, dan laporkan hitungan kesalahan, bukan hanya akurasi.
