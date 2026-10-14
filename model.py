from tortoise import fields, models


class Room(models.Model):
    room_id = fields.IntField(pk=True)
    status = fields.CharField(max_length=20)


class Admin(models.Model):
    """管理员账号，密码只保存哈希值，不保存明文。"""

    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    password_hash = fields.CharField(max_length=256)
