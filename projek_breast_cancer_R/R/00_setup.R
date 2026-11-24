# ==============================================================
# 00_setup.R : Instalasi/muat paket, folder output, & fungsi bantu
# ==============================================================

paket <- c(
  "caret", "rpart", "rpart.plot", "e1071", "klaR", "kernlab",
  "randomForest", "pROC", "ggplot2", "tidyr", "dplyr"
)

baru <- paket[!(paket %in% installed.packages()[, "Package"])]
if (length(baru) > 0) {
  install.packages(baru, dependencies = TRUE)
}
invisible(lapply(paket, library, character.only = TRUE))

# Buat struktur folder output otomatis
dir.create("output/models", recursive = TRUE, showWarnings = FALSE)
dir.create("output/tables", recursive = TRUE, showWarnings = FALSE)
dir.create("output/plots",  recursive = TRUE, showWarnings = FALSE)

# Urutan dan palet warna konsisten untuk artikel & PPT
urutan_model <- c(
  "Decision Tree", "Naive Bayes", "KNN", "SVM",
  "Random Forest", "Voting Ensemble"
)

warna_model <- c(
  "Decision Tree"   = "#f4a261",
  "Naive Bayes"     = "#e9c46a",
  "KNN"             = "#2a9d8f",
  "SVM"             = "#264653",
  "Random Forest"   = "#d1495b",
  "Voting Ensemble" = "#7b2d8e"
)

# Fungsi simpan plot resolusi tinggi (300 DPI)
simpan_plot <- function(p, nama_file, w = 8, h = 5) {
  ggsave(
    filename = file.path("output/plots", nama_file),
    plot     = p,
    width    = w,
    height   = h,
    dpi      = 300,
    bg       = "white"
  )
}