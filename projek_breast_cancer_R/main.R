# ==============================================================
# MAIN SCRIPT - Perbandingan Algoritma Data Mining (Breast Cancer)
# Buka file '.Rproj' di RStudio terlebih dahulu
# agar working directory otomatis mengarah ke folder projek ini.
# ==============================================================

waktu_mulai <- Sys.time()

cat("=== [1/5] Setup Paket & Konfigurasi ===\n")
source("R/00_setup.R")

cat("\n=== [2/5] Preprocessing & Pembagian Data ===\n")
source("R/01_preprocessing.R")

cat("\n=== [3/5] Pelatihan & Tuning Model (10-Fold CV) ===\n")
source("R/02_modeling.R")

cat("\n=== [4/5] Evaluasi Model & Ensemble ===\n")
source("R/03_evaluasi.R")

cat("\n=== [5/5] Pembuatan Visualisasi (300 DPI) ===\n")
source("R/04_visualisasi.R")

durasi <- round(as.numeric(difftime(Sys.time(), waktu_mulai, units = "secs")), 1)
cat("\n==============================================================\n")
cat("SELURUH PROSES SELESAI dalam", durasi, "detik.\n")
cat("- Model tersimpan di : output/models/\n")
cat("- Tabel tersimpan di : output/tables/\n")
cat("- Plot tersimpan di  : output/plots/\n")
cat("==============================================================\n")