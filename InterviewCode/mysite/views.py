from rest_framework import viewsets, mixins, status
from .serializers import *
from .models import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import IsInterviewer


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
            return Response({'detail': 'Комнату можно завершить только в статусе Processing'}, status=status.HTTP_400_BAD_REQUEST)

        room.status = Room.Status.COMPLETED
        room.save(update_fields=['status'])

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
        task = serializer.save(author=self.request.user)

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]

class SolutionViewSet(viewsets.ModelViewSet):
    queryset = Solution.objects.all()
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
