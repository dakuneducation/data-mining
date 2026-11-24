# ==============================================================
# 04_visualisasi.R : Menghasilkan 10 Plot 300 DPI untuk Artikel/PPT
# Bisa dijalankan ulang kapan saja tanpa perlu melatih ulang model!
# ==============================================================

if (!exists("simpan_plot")) source("R/00_setup.R")

ds     <- readRDS("output/models/data_split.rds")
models <- readRDS("output/models/models_trained.rds")
ev     <- readRDS("output/models/evaluasi_hasil.rds")

data  <- ds$data
train <- ds$train
test  <- ds$test
m_dt  <- models$dt
m_knn <- models$knn
m_svm <- models$svm
m_rf  <- models$rf
hasil <- ev$hasil
prob  <- ev$prob
pred  <- ev$pred
cv_all <- ev$cv_all

# --- 1. Distribusi Kelas (jumlah + persentase) ---
df_kelas <- data %>%
  count(diagnosis) %>%
  mutate(
    persen = n / sum(n) * 100,
    label  = sprintf("%d\n(%.1f%%)", n, persen)
  )

p_kelas <- ggplot(df_kelas, aes(diagnosis, n, fill = diagnosis)) +
  geom_col(width = 0.55) +
  geom_text(aes(label = label), vjust = -0.25, fontface = "bold", size = 4) +
  scale_fill_manual(values = c(M = "#d1495b", B = "#2e86ab")) +
  scale_x_discrete(labels = c(M = "Malignant (M)\n[Ganas / Positif]",
                              B = "Benign (B)\n[Jinak / Negatif]")) +
  coord_cartesian(ylim = c(0, max(df_kelas$n) * 1.18)) +
  labs(title = "Distribusi Kelas Diagnosis (N = 569)",
       x = NULL, y = "Jumlah Sampel") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none", plot.title = element_text(face = "bold"))
simpan_plot(p_kelas, "01_distribusi_kelas.png", 6.5, 4.5)

# --- 2. Perbandingan Metrik Evaluasi ---
hasil_long <- pivot_longer(hasil, -Model, names_to = "Metrik", values_to = "Nilai")
hasil_long$Model <- factor(hasil_long$Model, levels = urutan_model)

p_metrik <- ggplot(hasil_long, aes(Metrik, Nilai, fill = Model)) +
  geom_col(position = position_dodge(0.85), width = 0.8) +
  scale_fill_manual(values = warna_model) +
  coord_cartesian(ylim = c(0.75, 1)) +
  labs(title = "Perbandingan Metrik Evaluasi pada Data Uji",
       x = NULL, y = "Nilai Metrik") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom", plot.title = element_text(face = "bold"))
simpan_plot(p_metrik, "02_perbandingan_metrik.png", 10.5, 5.5)

# --- 3. Kurva ROC Semua Model (dengan nilai AUC di legenda) ---
roc_list <- lapply(prob, function(p) {
  roc(test$diagnosis, p, levels = c("B", "M"), direction = "<", quiet = TRUE)
})
label_roc <- setNames(
  sprintf("%s (AUC = %.4f)", urutan_model, as.numeric(sapply(roc_list, auc))),
  urutan_model
)

p_roc <- ggroc(roc_list, legacy.axes = TRUE, linewidth = 1.05) +
  geom_abline(slope = 1, intercept = 0, linetype = 2, colour = "grey50") +
  scale_colour_manual(values = warna_model, labels = label_roc) +
  labs(title = "Kurva ROC Semua Model pada Data Uji",
       x = "1 - Spesifisitas (False Positive Rate)",
       y = "Sensitivitas (True Positive Rate)",
       colour = "Model") +
  theme_minimal(base_size = 11) +
  guides(colour = guide_legend(ncol = 2)) +
  theme(plot.title = element_text(face = "bold"),
        legend.position = "bottom")
simpan_plot(p_roc, "03_kurva_roc.png", 7.2, 6)

# --- 4. Confusion Matrix Semua Model ---
cm_df <- do.call(rbind, lapply(urutan_model, function(n) {
  t <- as.data.frame(table(Prediksi = pred[[n]], Aktual = test$diagnosis))
  t$Model <- n
  t
}))
cm_df$Model <- factor(cm_df$Model, levels = urutan_model)

p_cm <- ggplot(cm_df, aes(Aktual, Prediksi, fill = Freq)) +
  geom_tile(colour = "white", linewidth = 1) +
  geom_text(aes(label = Freq), size = 5, fontface = "bold") +
  scale_fill_gradient(low = "#f2f7fb", high = "#2e86ab") +
  facet_wrap(~Model, ncol = 3) +
  labs(title = "Confusion Matrix per Model (Data Uji)") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none",
        plot.title = element_text(face = "bold"),
        strip.text = element_text(face = "bold"))
simpan_plot(p_cm, "04_confusion_matrix.png", 9.5, 6)

# --- 5. Sebaran AUC Cross Validation 10-Fold (SEMUA 6 Model) ---
p_cv <- ggplot(cv_all, aes(reorder(Model, Nilai, median), Nilai, fill = Model)) +
  geom_boxplot(alpha = 0.85, outlier.shape = NA) +
  geom_jitter(width = 0.1, size = 1.8, alpha = 0.65) +
  scale_fill_manual(values = warna_model) +
  labs(title = "Sebaran AUC pada 10-Fold Cross Validation (6 Model)",
       x = NULL, y = "AUC (ROC)") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "none", plot.title = element_text(face = "bold"))
simpan_plot(p_cv, "05_cross_validation_auc.png", 8.5, 5)

# --- 6. Pohon Keputusan (dilatih pada skala asli agar ambang mudah dibaca) ---
# Warna konsisten: Merah = Malignant (M), Biru = Benign (B)
pohon <- rpart(diagnosis ~ ., data = train, method = "class",
               control = rpart.control(cp = m_dt$bestTune$cp))
png("output/plots/06_pohon_keputusan.png", width = 2600, height = 1650, res = 250)
rpart.plot(pohon, type = 4, extra = 104,
           box.palette = list("Reds", "Blues"),
           main = "Struktur Decision Tree Optimal (Merah = M, Biru = B)")
dev.off()

# --- 7. Tuning Parameter k pada KNN ---
p_knn <- ggplot(m_knn$results, aes(x = k, y = ROC)) +
  geom_line(color = "#2a9d8f", linewidth = 1) +
  geom_point(color = "#2a9d8f", size = 2.5) +
  theme_minimal(base_size = 11) +
  labs(title = "Pengaruh Nilai k terhadap AUC 10-Fold CV (KNN)",
       x = "Jumlah Tetangga (k)", y = "AUC (10-Fold CV)") +
  theme(plot.title = element_text(face = "bold"))
simpan_plot(p_knn, "07_tuning_knn.png", 7.2, 4.5)

# --- 8. Tuning Parameter Cost (C) pada SVM RBF ---
p_svm <- ggplot(m_svm$results, aes(x = C, y = ROC)) +
  geom_line(color = "#264653", linewidth = 1) +
  geom_point(color = "#264653", size = 2.5) +
  scale_x_log10() +
  theme_minimal(base_size = 11) +
  labs(title = "Pengaruh Cost (C) terhadap AUC 10-Fold CV (SVM RBF)",
       x = "Cost (C) [Skala Log]", y = "AUC (10-Fold CV)") +
  theme(plot.title = element_text(face = "bold"))
simpan_plot(p_svm, "08_tuning_svm.png", 7.2, 4.5)

# --- 9. 15 Variabel Terpenting Random Forest ---
imp <- as.data.frame(randomForest::importance(m_rf$finalModel))
imp$Variabel <- rownames(imp)
imp <- imp %>% arrange(desc(MeanDecreaseGini)) %>% head(15)

p_imp <- ggplot(imp, aes(reorder(Variabel, MeanDecreaseGini), MeanDecreaseGini)) +
  geom_col(fill = "#d1495b") +
  coord_flip() +
  labs(title = "15 Variabel Terpenting (Random Forest)",
       x = NULL, y = "Mean Decrease Gini") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(face = "bold"))
simpan_plot(p_imp, "09_variabel_penting_rf.png", 8.2, 5.5)

# --- 10. Heatmap Korelasi Antar Fitur ---
fitur_numerik <- data[, setdiff(names(data), "diagnosis")]
kor <- cor(fitur_numerik)
kor_df <- as.data.frame(as.table(kor))

p_kor <- ggplot(kor_df, aes(Var1, Var2, fill = Freq)) +
  geom_tile() +
  scale_fill_gradient2(low = "#2e86ab", mid = "white", high = "#d1495b",
                       limits = c(-1, 1)) +
  labs(title = "Heatmap Korelasi Antar 30 Fitur Numerik",
       x = NULL, y = NULL, fill = "r") +
  theme_minimal(base_size = 10) +
  theme(plot.title = element_text(face = "bold"),
        axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5, size = 6.5),
        axis.text.y = element_text(size = 6.5))
simpan_plot(p_kor, "10_korelasi_fitur.png", 9.5, 8.5)

cat("10 plot resolusi 300 DPI berhasil disimpan di folder 'output/plots/'.\n")