# hack-the-hack
Backend of hack-the-hack, using Kafka and NN to predict winning hackathon projects

Demo: https://lindayi.me/projects/hack-the-hack/

## Architecture

## Requirements
Python 3
Kafka (0.9+)
MySQL

## Configuration
`hth.properties`

## Starting the crawler
Run `sh run_crawlers.sh` to start the pipeline

Create cron job for `hackathon_crawler.py` to run it once a day

Create cron job for `project_analyzer.py` to run it once a day
