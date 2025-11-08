# config.py
import os

class Config:
    SECRET_KEY = "datelock2025gold"
    SQLALCHEMY_DATABASE_URI = "sqlite:///girls.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "app/static/uploads"
