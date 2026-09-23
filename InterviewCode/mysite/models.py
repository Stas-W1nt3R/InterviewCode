from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        db_table = 'users'


class Room(models.Model):
    name = models.CharField(max_length=40)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    users = models.ManyToManyField(User, related_name='rooms', through='RoomParticipant')


    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Ожидание'
        PROCESSING = 'PROCESSING', 'В процессе'
        COMPLETED = 'COMPLETED', 'Завершено'
        CANCELED = 'CANCELED', 'Отменено'

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.WAITING)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name}, {self.uuid}, {self.status}"

    class Meta:
        db_table = 'rooms'


class RoomParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='participants')
    room = models.ForeignKey(Room, on_delete=models.CASCADE,related_name='participants')

    class Roles(models.TextChoices):
        INTERVIEWER = 'INTERVIEWER', 'Интервьюер'
        CANDIDATE = 'CANDIDATE', 'Кандидат'

    role = models.CharField(choices=Roles.choices, max_length=20, default='CANDIDATE')

    def __str__(self):
        return f"{self.user.username},  {self.role}, {self.room.slug_id}"

    class Meta:
        unique_together = ('room', 'user')
        db_table = 'participants'


class Task(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}, {self.description}"

    class Meta:
        db_table = 'tasks'


class TestCase(models.Model):
    enter_values = models.TextField()
    exit_values = models.TextField()
    expected_values = models.TextField()
    task = models.ForeignKey(Task, related_name='test_cases',on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.task}, {self.enter_values}, {self.expected_values}, {self.exit_values}"

    class Meta:
        db_table = 'test_cases'


class Solution(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name='solutions')
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    code = models.TextField()

    class Status(models.TextChoices):
        SUCCESSFUL = "SUCCESSFUL", "Успешно"
        UNSUCCESSFUL = "UNSUCCESSFUL", "Не успешно"

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.UNSUCCESSFUL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.room}, {self.task}, {self.code}, {self.status}"

    class Meta:
        db_table = 'solutions'