#!/bin/bash

# for mac/linux

# 1. Update packages
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
if [ -f "package.json" ]; then
    npm install
fi

# 2. Run both together
uvicorn main:app --reload --port 8000 & npm run dev
