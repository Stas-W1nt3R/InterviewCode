from django.contrib import admin

from .models import Room, RoomParticipant, Solution, Task, TestCase, User

admin.site.register(User)
admin.site.register(Room)
admin.site.register(RoomParticipant)
admin.site.register(TestCase)
admin.site.register(Task)
admin.site.register(Solution)
