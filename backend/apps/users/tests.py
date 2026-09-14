"""用户模块测试：注册、登录、刷新 token、个人资料、后台用户管理。

运行方式（容器内）：
    docker compose exec backend python manage.py test apps.users
"""
from rest_framework import status as http_status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
ME_URL = "/api/v1/users/me/"
ADMIN_USERS_URL = "/api/v1/admin/users/"


def _register_payload(username: str = "alice", password: str = "pass123456") -> dict:
    return {
        "username": username,
        "password": password,
        "confirm_password": password,
        "email": f"{username}@campus.edu.cn",
        "phone": "13800000000",
        "nickname": "爱丽丝",
        "student_no": "20260001",
    }


class RegisterLoginTest(APITestCase):
    """注册与登录。"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_register_success(self) -> None:
        resp = self.client.post(REGISTER_URL, _register_payload(), format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(resp.data["code"], 0)
        self.assertIn("access", resp.data["data"])
        self.assertIn("refresh", resp.data["data"])
        self.assertEqual(resp.data["data"]["user"]["username"], "alice")
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_register_password_mismatch(self) -> None:
        payload = _register_payload()
        payload["confirm_password"] = "different1"
        resp = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(resp.data["code"], 0)

    def test_register_duplicate_username(self) -> None:
        self.client.post(REGISTER_URL, _register_payload(), format="json")
        resp = self.client.post(REGISTER_URL, _register_payload(), format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn("已被注册", resp.data["message"])

    def test_login_success_and_failure(self) -> None:
        User.objects.create_user(username="bob", password="pass123456")
        ok = self.client.post(
            LOGIN_URL, {"username": "bob", "password": "pass123456"}, format="json"
        )
        self.assertEqual(ok.status_code, http_status.HTTP_200_OK)
        self.assertEqual(ok.data["code"], 0)
        self.assertIn("access", ok.data["data"])

        bad = self.client.post(
            LOGIN_URL, {"username": "bob", "password": "wrongpass"}, format="json"
        )
        self.assertEqual(bad.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_login_refresh_flow(self) -> None:
        """用 refresh token 刷新 access。"""
        User.objects.create_user(username="carol", password="pass123456")
        login = self.client.post(
            LOGIN_URL, {"username": "carol", "password": "pass123456"}, format="json"
        )
        refresh = login.data["data"]["refresh"]
        resp = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertIn("access", resp.data["data"])


class UserMeTest(APITestCase):
    """个人资料。"""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="dave", password="pass123456", nickname="戴夫"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_me(self) -> None:
        resp = self.client.get(ME_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.assertEqual(resp.data["data"]["username"], "dave")

    def test_update_profile(self) -> None:
        resp = self.client.patch(ME_URL, {"nickname": "新昵称", "phone": "13900001111"}, format="json")
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, "新昵称")
        self.assertEqual(self.user.phone, "13900001111")


class AdminUserTest(APITestCase):
    """后台用户管理：列表、禁用/启用、禁用后 token 失效。"""

    def setUp(self) -> None:
        self.admin = User.objects.create_superuser(username="root", password="Admin123456")
        self.user = User.objects.create_user(
            username="target", password="pass123456", nickname="目标用户", student_no="20260099"
        )
        self.client = APIClient()

    def test_admin_requires_staff(self) -> None:
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(ADMIN_USERS_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_admin_user_list_search(self) -> None:
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(ADMIN_USERS_URL, {"search": "20260099"})
        self.assertEqual(resp.status_code, http_status.HTTP_200_OK)
        results = resp.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["username"], "target")

    def test_toggle_active_disables_login_and_token(self) -> None:
        # 先登录拿 token
        login_resp = self.client.post(
            LOGIN_URL, {"username": "target", "password": "pass123456"}, format="json"
        )
        access = login_resp.data["data"]["access"]

        # 管理员禁用
        self.client.force_authenticate(user=self.admin)
        toggle = self.client.post(f"{ADMIN_USERS_URL}{self.user.id}/toggle_active/")
        self.assertEqual(toggle.status_code, http_status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        # 旧 token 立即失效
        anon = APIClient()
        anon.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        resp = anon.get(ME_URL)
        self.assertEqual(resp.status_code, http_status.HTTP_401_UNAUTHORIZED)

        # 无法再登录
        login_again = self.client.post(
            LOGIN_URL, {"username": "target", "password": "pass123456"}, format="json"
        )
        self.assertEqual(login_again.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_cannot_disable_self(self) -> None:
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(f"{ADMIN_USERS_URL}{self.admin.id}/toggle_active/")
        self.assertEqual(resp.status_code, http_status.HTTP_400_BAD_REQUEST)