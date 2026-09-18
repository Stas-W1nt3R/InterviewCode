from django.contrib import admin

from .models import *


admin.site.register(Room)
admin.site.register(RoomParticipant)
admin.site.register(TestCase)
admin.site.register(Task)
admin.site.register(Solution)