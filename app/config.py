import os
from datetime import timedelta

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SUPER_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 часа