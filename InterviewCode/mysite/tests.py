from rest_framework import status
from rest_framework.test import APITestCase

from .code_runner import run_code
from .models import Room, RoomParticipant, Solution, Task, TestCase, User


class ClientTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="test", email="test@gmail.com", password="password123")
        self.user2 = User.objects.create_user(username="test2", email="test2@gmail.com", password="password123")
        self.outsider = User.objects.create(
            username="anonymous", email="anonymous@gmail.com", password="passwordanonymous"
        )

        self.task = Task.objects.create(author=self.user1, name="test task", description="Task for tests")
        self.room = Room.objects.create(name="test_room", status=Room.Status.PROCESSING, task=self.task)

        self.participant1 = RoomParticipant.objects.create(
            room=self.room, user=self.user1, role=RoomParticipant.Roles.INTERVIEWER
        )
        self.participant2 = RoomParticipant.objects.create(room=self.room, user=self.user2)

        self.solution = Solution.objects.create(room=self.room, task=self.task, code="print(52)")
        self.solution.users.add(self.user1, self.user2)

    def test_delete_room_by_candidate(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f"/api/rooms/{self.room.uuid}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Room.objects.all().count(), 1)

    def test_delete_room_by_interviewer(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f"/api/rooms/{self.room.uuid}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Room.objects.all().count(), 0)

    def test_finish_room_by_candidate(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f"/api/rooms/{self.room.uuid}/finish/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finish_room_by_interviewer(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(f"/api/rooms/{self.room.uuid}/finish/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.room.refresh_from_db()
        self.assertEqual(self.room.status, Room.Status.COMPLETED)

    def test_outsider_check_room(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(f"/api/rooms/{self.room.uuid}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_test_case_not_for_another_user_problem(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            "/api/test_cases/",
            data={
                "task_id": self.task.id,
                "enter_values": "string",
                "exit_values": "string",
                "expected_values": "string",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_test_case_for_myself_task(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            "/api/test_cases/",
            data={
                "task_id": self.task.id,
                "enter_values": "string",
                "exit_values": "string",
                "expected_values": "string",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(TestCase.objects.all().count(), 1)

    def test_create_solution_by_participant(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post("/api/solutions/", data={"room_id": self.room.id, "code": "print(52)"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_solution_by_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post("/api/solutions/", data={"room_id": self.room.id, "code": "print(52)"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_view_solutions_by_interviewer(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/solutions/{self.solution.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_solutions_by_outsider(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(f"/api/solutions/{self.solution.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_joined_in_room(self):
        room2 = Room.objects.create(name="test_room2")
        RoomParticipant.objects.create(room=room2, user=self.user1, role=RoomParticipant.Roles.INTERVIEWER)

        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f"/api/rooms/{room2.uuid}/join/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        room2.refresh_from_db()
        self.assertEqual(room2.status, Room.Status.PROCESSING)

    def test_create_code_runner(self):
        res = "".join(run_code("print(1)", self.room.uuid))
        self.assertIn("1", res)

    def test_not_authenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_room_without_task(self):
        room2 = Room.objects.create(name="test_room2")
        RoomParticipant.objects.create(room=room2, user=self.user1, role=RoomParticipant.Roles.INTERVIEWER)

        self.client.force_authenticate(user=self.user1)
        response = self.client.post("/api/solutions/", data={"room_id": room2.id, "code": "print(52)"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
