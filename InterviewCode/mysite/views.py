import logging

from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Room, RoomParticipant, Solution, Task, TestCase, User
from .permissions import IsInterviewer
from .serializers import (
    RegistrationSerializer,
    RoomParticipantSerializer,
    RoomSerializer,
    SolutionSerializer,
    TaskSerializer,
    TestCaseSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)

class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class RoomViewSet(viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsInterviewer()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Room.objects.filter(users=self.request.user).prefetch_related('participants__user')

    def perform_create(self, serializer):
        room = serializer.save()
        RoomParticipant.objects.create(
            user=self.request.user,
            room=room,
            role=RoomParticipant.Roles.INTERVIEWER,
        )

    @action(detail=True, methods=['post'])
    def join(self, request, uuid=None):
        room = get_object_or_404(Room, uuid=uuid)

        if room.status in (Room.Status.COMPLETED, Room.Status.CANCELED):
            return Response({'detail': 'Комната недоступна'}, status=status.HTTP_400_BAD_REQUEST)

        participant, created = RoomParticipant.objects.get_or_create(
            room=room,
            user=request.user,
            defaults={'role': RoomParticipant.Roles.CANDIDATE}
        )

        if created and room.status == Room.Status.WAITING:
            room.status = Room.Status.PROCESSING
            room.save(update_fields=['status'])

            logger.info("The user %s joined the room %s", participant.user.id, room.uuid)

        return Response(
            self.get_serializer(room).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='finish')
    def finish(self, request, uuid=None):
        room = get_object_or_404(Room, uuid=uuid)
        user = get_object_or_404(RoomParticipant, room=room, user=request.user)

        if user.role != RoomParticipant.Roles.INTERVIEWER:
            return Response({'detail': 'Завершить собеседование может только интервьюер'},
                            status=status.HTTP_403_FORBIDDEN)

        if room.status != Room.Status.PROCESSING:
            return Response({'detail': 'Комнату можно завершить только в статусе Processing'},
                            status=status.HTTP_400_BAD_REQUEST)

        room.status = Room.Status.COMPLETED
        room.save(update_fields=['status'])

        logger.info("The user: %s finished the room: %s", request.user.id, room.uuid)

        return Response(
            RoomSerializer(room).data, status=status.HTTP_200_OK
        )


class RoomParticipantViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    def get_queryset(self):
        return RoomParticipant.objects.filter(room__users=self.request.user)

    serializer_class = RoomParticipantSerializer
    permission_classes = [IsAuthenticated]

class TaskViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Task.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

class TestCaseViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return TestCase.objects.filter(task__author=self.request.user).select_related('task')

    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]

class SolutionViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return (Solution.objects.filter(Q(users=self.request.user) |
                                        Q(room__participants__user=self.request.user,
                                          room__participants__role=RoomParticipant.Roles.INTERVIEWER)).
                select_related('room', 'task').prefetch_related('users').distinct())

    def perform_create(self, serializer):
        room = serializer.validated_data['room']
        solution = serializer.save(task=room.task)
        solution.users.add(self.request.user)

    serializer_class = SolutionSerializer
    permission_classes = [IsAuthenticated]


class RegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.none()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = RefreshToken.for_user(user)

        return Response({
            'user': {'id': user.id, 'username': user.username},
            'access': str(token.access_token),
            'refresh': str(token),
        }, status=status.HTTP_201_CREATED)
