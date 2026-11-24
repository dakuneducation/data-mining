# ==============================================================
# 03_evaluasi.R : Prediksi Uji, Soft Voting, Metrik, & CV 6 Model
# ==============================================================

if (!exists("urutan_model")) source("R/00_setup.R")
ds     <- readRDS("output/models/data_split.rds")
models <- readRDS("output/models/models_trained.rds")

test  <- ds$test
m_dt  <- models$dt
m_nb  <- models$nb
m_knn <- models$knn
m_svm <- models$svm
m_rf  <- models$rf

# --- 1. Prediksi probabilitas kelas M pada data uji ---
model_dasar <- list(
  "Decision Tree" = m_dt,
  "Naive Bayes"   = m_nb,
  "KNN"           = m_knn,
  "SVM"           = m_svm
)

prob <- lapply(model_dasar, function(m) {
  suppressWarnings(predict(m, test, type = "prob")[, "M"])
})

# Ensemble 1: Random Forest
prob[["Random Forest"]] <- predict(m_rf, test, type = "prob")[, "M"]

# Pengaman bila Naive Bayes menghasilkan NA/NaN pada sampel ekstrem
for (nm in names(prob)) {
  if (any(is.na(prob[[nm]]))) {
    warning(paste("Ditemukan NA pada probabilitas", nm, "- diganti 0.5"))
    prob[[nm]][is.na(prob[[nm]])] <- 0.5
  }
}

# Ensemble 2: Soft Voting (rata-rata probabilitas 4 model dasar)
prob[["Voting Ensemble"]] <- rowMeans(do.call(cbind, prob[1:4]))
prob <- prob[urutan_model]

pred <- lapply(prob, function(p) {
  factor(ifelse(p >= 0.5, "M", "B"), levels = c("M", "B"))
})

# --- 2. Hitung AUC 10-Fold CV untuk SEMUA 6 model (termasuk Voting) ---
rs <- resamples(list(
  "Decision Tree" = m_dt,
  "Naive Bayes"   = m_nb,
  "KNN"           = m_knn,
  "SVM"           = m_svm,
  "Random Forest" = m_rf
))

cv_5 <- pivot_longer(
  rs$values, -Resample,
  names_to = c("Model", "Metrik"), names_sep = "~",
  values_to = "Nilai"
) %>%
  filter(Metrik == "ROC") %>%
  select(Resample, Model, Nilai)

ambil_oof <- function(m, nama_col) {
  df_p <- m$pred[, c("rowIndex", "Resample", "obs", "M")]
  df_p$M[is.na(df_p$M)] <- 0.5
  names(df_p)[names(df_p) == "M"] <- nama_col
  df_p
}

oof <- ambil_oof(m_dt, "dt") %>%
  inner_join(ambil_oof(m_nb,  "nb")[,  c("rowIndex", "Resample", "nb")],  by = c("rowIndex", "Resample")) %>%
  inner_join(ambil_oof(m_knn, "knn")[, c("rowIndex", "Resample", "knn")], by = c("rowIndex", "Resample")) %>%
  inner_join(ambil_oof(m_svm, "svm")[, c("rowIndex", "Resample", "svm")], by = c("rowIndex", "Resample"))

oof$voting <- rowMeans(oof[, c("dt", "nb", "knn", "svm")])

cv_voting <- oof %>%
  group_by(Resample) %>%
  summarise(
    Nilai = as.numeric(auc(roc(obs, voting, levels = c("B", "M"),
                               direction = "<", quiet = TRUE))),
    .groups = "drop"
  ) %>%
  mutate(Model = "Voting Ensemble") %>%
  select(Resample, Model, Nilai)

cv_all <- bind_rows(cv_5, cv_voting)

ringkasan_cv <- cv_all %>%
  group_by(Model) %>%
  summarise(
    CV_AUC_Mean   = mean(Nilai),
    CV_AUC_SD     = sd(Nilai),
    CV_AUC_Median = median(Nilai),
    .groups = "drop"
  )

# --- 3. Evaluasi metrik pada data uji ---
hitung_metrik <- function(prediksi, peluang, aktual) {
  cm <- confusionMatrix(prediksi, aktual, positive = "M")
  nilai_auc <- as.numeric(auc(roc(aktual, peluang, levels = c("B", "M"),
                                  direction = "<", quiet = TRUE)))
  data.frame(
    Accuracy    = as.numeric(cm$overall["Accuracy"]),
    Kappa       = as.numeric(cm$overall["Kappa"]),
    Sensitivity = as.numeric(cm$byClass["Sensitivity"]),
    Specificity = as.numeric(cm$byClass["Specificity"]),
    Precision   = as.numeric(cm$byClass["Precision"]),
    F1          = as.numeric(cm$byClass["F1"]),
    AUC         = nilai_auc
  )
}

hasil <- do.call(rbind, lapply(urutan_model, function(n) {
  cbind(Model = n, hitung_metrik(pred[[n]], prob[[n]], test$diagnosis))
}))

hasil_lengkap <- left_join(hasil, ringkasan_cv, by = "Model")
hasil_bulat   <- hasil_lengkap
hasil_bulat[, -1] <- round(hasil_bulat[, -1], 4)

cat("\n===== HASIL EVALUASI DATA UJI & CV 10-FOLD =====\n")
print(hasil_bulat, row.names = FALSE)

write.csv(hasil_bulat, "output/tables/hasil_perbandingan.csv", row.names = FALSE)
write.csv(cv_all,      "output/tables/detail_cv_10fold_auc.csv", row.names = FALSE)

cat("\n===== CONFUSION MATRIX DATA UJI =====\n")
for (n in urutan_model) {
  cat("\n---", n, "---\n")
  print(table(Prediksi = pred[[n]], Aktual = test$diagnosis))
}

saveRDS(
  list(hasil = hasil, hasil_lengkap = hasil_lengkap, prob = prob,
       pred = pred, cv_all = cv_all, rs = rs),
  file = "output/models/evaluasi_hasil.rds"
)