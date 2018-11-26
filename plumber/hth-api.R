library(plumber)
library(reticulate)
use_python("/usr/bin/python3")
source_python("plumber/new_doc.py")
model <- readRDS("plumber/nnetmodel.Rds")
tmp_test_data <- readRDS("plumber/tmp_test_data.Rds")
new_data_tmpl <- readRDS("plumber/new_data.Rds")

MODEL_VERSION <- "0.0.1"

#* @filter cors
cors <- function(res) {
  res$setHeader("Access-Control-Allow-Origin", "*")
  plumber::forward()
}

#* @get /healthcheck
health_check <- function() {
  result <- data.frame(
    "input" = "",
    "status" = 200,
    "model_version" = MODEL_VERSION
  )
  
  return(result)
}

#* @post /newidea
#* @get /newidea
predict_newidea <- function(text="", slug="", teamsize=1) {
  teamsize = as.integer(teamsize)
  doc_vec = infer_new_doc(text, slug)
  
  new_data <- new_data_tmpl
  new_data[1,] = c(list(slug, teamsize, NA), doc_vec, NA)
  result_prob <- predict(model, newdata = predict(tmp_test_data, subset(new_data, select = -c(project_slug, winner))), type="raw")
  result_prob <- as.numeric(result_prob)
  
  payload <- data.frame(text=text, slug=slug, teamsize=teamsize)
  result_list <- list(
    input = list(payload),
    response = list("winning_probability" = result_prob,
                    "winning_prediction" = (result_prob >= 0.5)),
    status = 200,
    model_version = MODEL_VERSION)
  
  return(result_list)
}