# settings.py
TORTOISE_ORM = {
    "connections": {
        "default": "mysql://root:123456@127.0.0.1:3306/fastapi"
    },
    "apps": {
        "models": {
            "models": ["model", "aerich.models"],
            "default_connection": "default",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai"
}

# 开发环境登录配置。正式环境请改为环境变量或数据库账号。
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"
JWT_SECRET_KEY = "please-change-this-secret-key-32"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60
