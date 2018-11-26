# Set working directory to that of the current file
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))  # Only when using RStudio

# Read data
library(readxl)
data <- read_excel("data.xlsx")
data$winner <- as.factor(data$winner)
levels(data$winner)[levels(data$winner)=="0"] <- "Lose"
levels(data$winner)[levels(data$winner)=="1"] <- "Win"
data$teamsize <- as.numeric(data$teamsize)

# Data balancing with SMOTE
library(DMwR)
balancedset <- SMOTE(winner~., as.data.frame(data[,-1]))
levels(balancedset$winner)[levels(balancedset$winner)=="0"] <- "Lose"
levels(balancedset$winner)[levels(balancedset$winner)=="1"] <- "Win"

# 10 fold CV + grid search for parameter tuning
library(nnet)
library(caret)
library(ROCR)
library(doParallel)
registerDoParallel(cores = 8)

numFolds <- trainControl(method = 'cv', number = 10, classProbs = TRUE, verboseIter = TRUE,
                         preProcOptions = list(thresh = 0.75, ICAcomp = 3, k = 5))

nnetmodel.opt <- train(winner ~ ., data=balancedset, method='nnet', trace=F,
                       preProcess = c('center', 'scale'), trControl = numFolds, 
                       tuneGrid=expand.grid(.size=c(5,6,7,8,9), .decay=c(0.001,0.01,0.1)))

# Prediction with final model
tmp_test_data <- preProcess(subset(balancedset, select = -c(winner)), method = c('center', 'scale'), thresh = 0.75, ICAcomp = 3, k = 5)
nnet_opt_pred <- predict(nnetmodel.opt$finalModel, newdata = predict(tmp_test_data, subset(data, select = -c(project_slug, winner))), type="raw")
nnet_opt_perf <- performance(prediction(nnet_opt_pred, data$winner), "auc")
confusionMatrix(nnet_opt_pred, balancedset$winner)
model_stat <- confusionMatrix(nnet_opt_pred, data$winner)$byClass

data$pred <- nnet_opt_pred[,1]

# Persistent final model
saveRDS(nnetmodel.opt$finalModel, file = "plumber/nnetmodel.Rds", compress = TRUE)
saveRDS(tmp_test_data, file = "plumber/tmp_test_data.Rds", compress = TRUE)
saveRDS(new_data, file = "plumber/new_data.Rds", compress = TRUE)