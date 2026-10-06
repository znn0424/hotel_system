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
