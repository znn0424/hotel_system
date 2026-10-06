from tortoise import fields, models
class Room(models.Model):
    room_id = fields.IntField(pk=True)
    status =  fields.CharField(max_length=20)