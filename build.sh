#!/usr/bin/env bash
set -e

cd frontend
npm install
npm run build
cd ..

cd backend
pip install -r requirements.txt
python -m app.ingest
