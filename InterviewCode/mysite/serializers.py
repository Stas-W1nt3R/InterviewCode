from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RoomSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    users_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        source='users',
        write_only=True
    )

    class Meta:
        model = Room
        fields = ['id', 'name', 'uuid', 'users', 'users_ids', 'task', 'status']


class RoomParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = RoomSerializer(read_only=True)

    class Meta:
        model = RoomParticipant
        fields = ['id', 'user', 'room','role']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class TestCaseSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    class Meta:
        model = TestCase
        fields = ['id', 'task', 'enter_values', 'exit_values','expected_values']


class SolutionSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        source='task',
        write_only=True
    )
    room = RoomSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        source='room',
        write_only=True
    )
    users = UserSerializer(many=True, read_only=True)
    users_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        source='users',
        write_only=True
    )

    class Meta:
        model = Solution
        fields = ['id', 'task', 'task_id', 'room','room_id', 'users', 'users_ids', 'code', 'status']