#!/bin/bash
echo "Запуск Flask-приложения..."
export FLASK_APP=learn.py
flask run --host=0.0.0.0
