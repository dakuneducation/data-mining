# ==============================================================
# 02_modeling.R : 10-Fold Cross Validation & Pelatihan 5 Model
# ==============================================================

if (!exists("simpan_plot")) source("R/00_setup.R")
if (!exists("train")) {
  ds <- readRDS("output/models/data_split.rds")
  train <- ds$train
}

# Buat 10 fold sekali agar semua model dibandingkan pada lipatan yang sama
set.seed(123)
lipatan <- createFolds(train$diagnosis, k = 10, returnTrain = TRUE)

ctrl <- trainControl(
  method          = "cv",
  number          = 10,
  index           = lipatan,
  classProbs      = TRUE,
  summaryFunction = twoClassSummary,
  savePredictions = "final"
)

# Standardisasi dilakukan di dalam setiap fold CV (bebas data leakage)
# Catatan: KNN & SVM sangat bergantung pada skala fitur; DT & RF invarian
pra <- c("center", "scale")

cat("Melatih Decision Tree (rpart)...\n")
set.seed(123)
m_dt <- train(
  diagnosis ~ ., data = train, method = "rpart",
  trControl = ctrl, metric = "ROC", tuneLength = 10,
  preProcess = pra
)

cat("Melatih Naive Bayes (klaR)...\n")
set.seed(123)
m_nb <- suppressWarnings(train(
  diagnosis ~ ., data = train, method = "nb",
  trControl = ctrl, metric = "ROC", preProcess = pra,
  tuneGrid = expand.grid(fL = c(0, 1), usekernel = c(TRUE, FALSE), adjust = 1)
))

cat("Melatih KNN...\n")
set.seed(123)
m_knn <- train(
  diagnosis ~ ., data = train, method = "knn",
  trControl = ctrl, metric = "ROC", preProcess = pra,
  tuneGrid = data.frame(k = seq(3, 25, 2))
)

cat("Melatih SVM (Kernel RBF)...\n")
set.seed(123)
m_svm <- train(
  diagnosis ~ ., data = train, method = "svmRadial",
  trControl = ctrl, metric = "ROC", preProcess = pra,
  tuneLength = 8
)

cat("Melatih Random Forest (Ensemble Bagging)...\n")
set.seed(123)
m_rf <- train(
  diagnosis ~ ., data = train, method = "rf",
  trControl = ctrl, metric = "ROC", preProcess = pra,
  tuneGrid = data.frame(mtry = c(2, 4, 6, 8, 12, 16)),
  ntree = 500, importance = TRUE
)

cat("\n--- Parameter Optimal (10-Fold CV) ---\n")
cat("Decision Tree : cp   =", m_dt$bestTune$cp, "\n")
cat("Naive Bayes   : fL   =", m_nb$bestTune$fL,
    "| usekernel =", m_nb$bestTune$usekernel, "\n")
cat("KNN           : k    =", m_knn$bestTune$k, "\n")
cat("SVM (RBF)     : C    =", m_svm$bestTune$C,
    "| sigma =", round(m_svm$bestTune$sigma, 4), "\n")
cat("Random Forest : mtry =", m_rf$bestTune$mtry, "\n")

# Simpan semua model terlatih ke file .rds
models <- list(
  dt = m_dt, nb = m_nb, knn = m_knn, svm = m_svm, rf = m_rf
)
saveRDS(models, file = "output/models/models_trained.rds")