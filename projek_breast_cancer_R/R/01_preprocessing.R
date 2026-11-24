# ==============================================================
# 01_preprocessing.R : Baca data.csv, pembersihan, & split 80:20
# ==============================================================

if (!exists("simpan_plot")) source("R/00_setup.R")

# Baca dataset versi Kaggle (memiliki header)
data <- read.csv("data/data.csv", header = TRUE, check.names = TRUE)

# Hapus kolom ID jika ada
if ("id" %in% names(data)) data$id <- NULL

# Hapus kolom kosong (misal 'Unnamed: 32' yang terbaca 'X' di R)
kolom_kosong <- colSums(is.na(data)) == nrow(data)
if (any(kolom_kosong)) {
  cat("Menghapus kolom kosong:", paste(names(data)[kolom_kosong], collapse = ", "), "\n")
  data <- data[, !kolom_kosong, drop = FALSE]
}

# Rapikan nama kolom (contoh: concave.points_mean -> concave_points_mean)
names(data) <- gsub("\\.", "_", names(data))

# Pastikan kelas target faktor dengan M (Malignant) sebagai kelas positif
data$diagnosis <- factor(data$diagnosis, levels = c("M", "B"))

cat("Dimensi data bersih :", nrow(data), "baris x", ncol(data), "kolom\n")
cat("Jumlah missing value:", sum(is.na(data)), "\n")
cat("Distribusi kelas:\n")
print(table(data$diagnosis))

# Split data 80:20 secara stratified
set.seed(123)
idx   <- createDataPartition(data$diagnosis, p = 0.8, list = FALSE)
train <- data[idx, ]
test  <- data[-idx, ]

cat("Data latih:", nrow(train), "| Data uji:", nrow(test), "\n")

# Simpan hasil preprocessing agar skrip berikutnya bisa jalan mandiri
saveRDS(
  list(data = data, train = train, test = test),
  file = "output/models/data_split.rds"
)