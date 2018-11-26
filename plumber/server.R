library(plumber)

serve_model <- plumb("plumber/hth-api.R")
serve_model$run(host="0.0.0.0", port = 8000)