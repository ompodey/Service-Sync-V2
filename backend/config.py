import os
class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///ServiceSyncDB.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "serivicesyncapp"
    UPLOAD_FOLDER=os.path.join(os.getcwd(),"uploadfiles")
    CELERY_BROKER_URL = 'redis://localhost:6379/1' #PORT FROM REDIS SERVER AND 1 IS THE DEFAULT(DATABASE : ALL WORKERS WORK ARE SAVED HERE)
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/2' #2: dB WHERE RESULT IS SAVED...
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    CACHE_TYPE="redis"
    CACHE_REDIS_URL="redis://localhost:6379/0"
    