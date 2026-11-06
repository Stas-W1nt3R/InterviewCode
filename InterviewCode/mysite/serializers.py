from rest_framework import serializers
from .models import User, Room, RoomParticipant, Task, TestCase, Solution
from django.contrib.auth.password_validation import validate_password


class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    password_confirm = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm')
        read_only_fields = ('id',)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Это имя уже занято!")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Этот email уже указан!")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Пароли не совпадают!'
            })
        return attrs

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


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
        write_only=True,
        required=False
    )

    class Meta:
        model = Room
        fields = ['id', 'name', 'uuid', 'users', 'users_ids', 'task', 'status']
        read_only_fields = ('status',)


class RoomParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    room = RoomSerializer(read_only=True)

    class Meta:
        model = RoomParticipant
        fields = ['id', 'user', 'room','role']


class TaskSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = Task
        fields = ['id', 'author', 'name', 'description', 'created_at', 'updated_at']


class TestCaseSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        source='task',
        write_only=True,
    )

    class Meta:
        model = TestCase
        fields = ['id', 'task', 'task_id', 'enter_values', 'exit_values','expected_values']

    def validate_task_id(self, value):
        if value.author != self.context['request'].user:
            raise serializers.ValidationError('Это не ваша задача!')
        return value


class SolutionSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        source='room',
        write_only=True
    )
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Solution
        fields = ['id', 'task', 'room','room_id', 'users', 'code', 'status']
        read_only_fields = ('status',)

    def validate_room_id(self, value):
        if not value.participants.filter(user=self.context['request'].user).exists():
            raise serializers.ValidationError('Вы не участник этой комнаты')

        if value.task is None:
            raise serializers.ValidationError('Вы не указали задачу для комнаты')

        return value
