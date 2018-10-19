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
confusionMatrix(nnet_opt_pred, data$winner)
model_stat <- confusionMatrix(nnet_opt_pred, data$winner)$byClass

data$pred <- nnet_opt_pred[,1]

# NN visualization
library(NeuralNetTools)
plotnet(nnetmodel.opt)

# Predicting new project
new_data <- data[0,]
new_data[1,] = list("hack_the_hack",2, NA, 0.02951171, -0.02751057, -0.0127445, -0.00399104, 0.01925625, 0.04828535, 0.01840951, -0.03288313, -0.06317613, 0.00282095, 0.01774944, 0.02368211, -0.0168776, -0.0227201, -0.04356241, -0.02177912, 0.01007551, -0.01193871, 0.0473227, 0.01261428, 0.00385552, -0.01944466, 0.02179701, -0.0313975, 0.03166671, 0.0036163, -0.03545361, -0.00669269, -0.00621628, 0.0232108, 0.06211591, -0.05432852, 0.04074468, 0.0049867, 0.00994793, 0.01110999, -0.00565953, -0.05453094, -0.00617957, -0.01996304, 0.01292003, -0.03403559, -0.05475428, 0.03188324, -0.01728744, 0.00066403, -0.01594708, 0.03637906, 0.01052289, 0.00309592, 0.01980237, -0.01631954, 0.00059264, -0.00417876, -0.01155209, 0.03286837, 0.04300068, 0.03599982, -0.01938996, -0.04843812, 0.05734062, 0.00485453, -0.02292114, 0.03464464, -0.00702507, 0.03501536, 0.0396248, -0.03096544, -0.00422176, -0.01501595, 0.01562308, 0.02692674, -0.03933189, -0.00186513, -0.03551459, -0.0074444, 0.03076474, 0.01696223, 0.0193924, -0.02792185, -0.06203755, -0.00670211, -0.01258545, -0.03614749, 0.01058846, -0.01570737, 0.03408062, -0.00346502, 0.08028342, 0.02980755, 0.01095959, 0.02177899, 0.02528169, 0.03155649, 0.002756, -0.02444374, 0.00449536, -0.01021246, 0.01426874, -0.00359984, NA)
predict(nnetmodel.opt$finalModel, newdata = predict(tmp_test_data, subset(new_data, select = -c(project_slug, winner))), type="raw")
