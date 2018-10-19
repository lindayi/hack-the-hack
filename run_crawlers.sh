#!/bin/bash

screen python3 project_persistence.py
screen python3 hackathon_persistence.py

screen python3 project_detail_crawler.py
screen python3 project_crawler.py