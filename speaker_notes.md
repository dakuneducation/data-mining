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

## Slide 6: Decision Tree

Pecahan dari slide metode. recursive partitioning memilih fitur dan ambang terbaik di tiap simpul; cp menolak pemecahan yang manfaatnya kecil supaya pohon tidak terlalu rinci.

## Slide 7: Naive Bayes

Pecahan dari slide metode. Menghitung posterior kelas dengan asumsi fitur saling bebas; konfigurasi yang diuji: fL, usekernel, adjust = 1.

## Slide 8: KNN

Pecahan dari slide metode. Tidak ada tahap pelatihan, model hanya menyimpan data latih; k diuji ganjil dari 3 sampai 25 (12 nilai).

## Slide 9: SVM (RBF)

Pecahan dari slide metode. svmRadial dengan tuneLength = 8; hasil tuning KNN dan SVM ada pada slide 16.

## Slide 10: Random Forest

Pecahan dari slide metode. Bagging dengan subset fitur acak per split; 500 pohon, mtry 2 sampai 16. Feature importance ada pada slide 20.

## Slide 11: Soft Voting

Pecahan dari slide metode. Empat anggota berbobot sama (1/4); angka pada ilustrasi hanya contoh. Threshold keputusan dan AUC out-of-fold dibahas pada slide berikutnya.

## Slide 12: Soft Voting: Rata-rata Probabilitas, Threshold Keputusan

Random Forest dinilai sebagai ensemble tersendiri, bukan anggota voting.

## Slide 13: Membaca Metrik: Penyebut Menentukan Makna

Sensitivitas dan presisi punya penyebut berbeda, jadi bisa berbeda meski akurasi tinggi.

## Slide 14: Eksplorasi Data: Ukuran Inti Sel Membedakan Kelas

Median hanya dipakai untuk deskripsi data, bukan untuk memilih fitur atau menetapkan threshold.

## Slide 15: Cross Validation: SVM Tertinggi, RF dan SVM Paling Stabil

Fold yang sama dipakai semua model, jadi turunnya AUC di fold 2 terjadi pada observasi validasi yang sama. Mean AUC CV menggambarkan proses pemilihan model, bukan estimasi bebas bias.

## Slide 16: Tuning Hiperparameter: KNN dan SVM

Gambar diambil dari folder output/plots hasil 04_visualisasi.R (300 DPI).

## Slide 17: Data Uji: Tiga Metode dengan Akurasi Sama 98,23%

Voting tidak mengungguli KNN pada akurasi.

## Slide 18: Sensitivitas, Spesifisitas, dan Presisi

Presisi 1,0 tidak berarti model aman: ia hanya bicara tentang prediksi ganas yang dibuat, bukan yang terlewat.

## Slide 19: Jenis dan Jumlah Kesalahan pada 113 Sampel Uji

NB dan SVM akurasinya sama (0,9735) tetapi Kappa berbeda karena distribusi kelas prediksinya berbeda. Pengujian selisih antarmodel memerlukan paired test pada sampel yang sama.

## Slide 20: Feature Importance Random Forest

Hati-hati dengan klaim kausal: peringkat Gini impurity bukan pengaruh biologis terpisah.

## Slide 21: Keterbatasan dan Ketidakpastian Estimasi

Sumber: Collins dkk. (2024) BMJ, TRIPOD+AI, Riley dkk., Moons dkk. PROBAST+AI.

## Slide 22: Kesimpulan

Tutup dengan pesan inti: pilih model berdasarkan jenis kesalahan yang diprioritaskan, dan laporkan hitungan kesalahan, bukan hanya akurasi.
