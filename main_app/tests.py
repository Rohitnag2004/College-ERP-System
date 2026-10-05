import time
from datetime import date

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Course, CustomUser, FeePayment, Session, Semester, Staff, StudentGradeCard, Subject


@override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies")
class PublicPortalSmokeTests(SimpleTestCase):
    def test_login_page_renders_brand_roles_and_security_check(self):
        response = self.client.get(reverse("login_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Velocity Tech University")
        self.assertContains(response, "Student")
        self.assertContains(response, "Teacher")
        self.assertContains(response, "Admin")
        self.assertContains(response, "Security check:")
        self.assertContains(response, "Velocity Tech University crest")

    def test_legacy_role_login_url_returns_to_shared_login_page(self):
        response = self.client.get(reverse("role_login_page", args=["student"]))

        self.assertRedirects(response, reverse("login_page"))

    def test_unknown_role_login_url_returns_not_found(self):
        response = self.client.get(reverse("role_login_page", args=["librarian"]))

        self.assertEqual(response.status_code, 404)


@override_settings(SESSION_IDLE_TIMEOUT_SECONDS=300)
class LibraryGradeCardAndSessionTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(name="B.Tech CSE AI-ML", duration="4 years", total_semesters=8)
        self.session = Session.objects.create(start_year=date(2023, 1, 1), end_year=date(2027, 12, 31))
        self.semester_one = Semester.objects.create(course=self.course, number=1, name="Semester 1")
        self.semester_two = Semester.objects.create(course=self.course, number=2, name="Semester 2")
        self.admin_user = CustomUser.objects.create_user(
            email="admin-smoke@example.test", password="test-password", user_type="1", first_name="Portal", last_name="Admin",
        )
        self.teacher_user = CustomUser.objects.create_user(
            email="teacher-smoke@example.test", password="test-password", user_type="2", first_name="Portal", last_name="Teacher",
        )
        self.teacher = self.teacher_user.staff
        self.teacher.approval_status = Staff.ApprovalStatus.APPROVED
        self.teacher.save(update_fields=["approval_status"])
        self.student_user = CustomUser.objects.create_user(
            email="student-smoke@example.test", password="test-password", user_type="3", first_name="Portal", last_name="Student",
        )
        self.other_student_user = CustomUser.objects.create_user(
            email="other-student-smoke@example.test", password="test-password", user_type="3", first_name="Other", last_name="Student",
        )
        for user in (self.student_user, self.other_student_user):
            profile = user.student
            profile.course = self.course
            profile.session = self.session
            profile.save(update_fields=["course", "session"])
        Subject.objects.create(name="Assigned subject", course=self.course, semester=self.semester_one, staff=self.teacher)
        self.student_card = StudentGradeCard.objects.create(
            student=self.student_user.student, semester=self.semester_one,
            title="Student semester one", file="grade_cards/student-one.pdf", uploaded_by=self.admin_user,
        )
        StudentGradeCard.objects.create(
            student=self.student_user.student, semester=self.semester_two,
            title="Student semester two", file="grade_cards/student-two.pdf", uploaded_by=self.admin_user,
        )
        self.other_student_card = StudentGradeCard.objects.create(
            student=self.other_student_user.student, semester=self.semester_one,
            title="Other student card", file="grade_cards/other-student.pdf", uploaded_by=self.admin_user,
        )

    def test_admin_and_teacher_can_manage_books_but_student_cannot(self):
        for user in (self.admin_user, self.teacher_user):
            self.client.force_login(user)
            response = self.client.get(reverse("manage_books"))
            self.assertEqual(response.status_code, 200)
            if user == self.admin_user:
                dashboard = self.client.get(reverse("admin_home"))
                self.assertContains(dashboard, "Manage Library Books")
                self.assertContains(dashboard, 'data-idle-timeout-seconds="300"')
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("manage_books"))
        self.assertRedirects(response, reverse("student_home"), fetch_redirect_response=False)

    def test_teacher_grade_cards_are_limited_to_assigned_semesters(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("grade_cards"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student semester one")
        self.assertNotContains(response, "Student semester two")
        form = response.context["form"]
        self.assertQuerySetEqual(form.fields["semester"].queryset, [self.semester_one], transform=lambda semester: semester)

    def test_student_only_sees_and_can_request_their_own_grade_cards(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("grade_cards"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student semester one")
        self.assertContains(response, "Student semester two")
        self.assertNotContains(response, "Other student card")
        response = self.client.get(reverse("download_grade_card", args=[self.other_student_card.pk]))
        self.assertEqual(response.status_code, 404)

    def test_idle_student_session_expires_at_five_minutes(self):
        self.client.force_login(self.student_user)
        session = self.client.session
        session["last_activity"] = time.time() - 301
        session.save()

        response = self.client.get(reverse("grade_cards"))

        self.assertRedirects(response, reverse("login_page"), fetch_redirect_response=False)

    def test_heartbeat_keeps_session_alive_only_when_recent_activity_is_reported(self):
        self.client.force_login(self.student_user)
        session = self.client.session
        session["last_activity"] = time.time() - 240
        session.save()

        response = self.client.post(
            reverse("session_activity"),
            {"last_activity": str(time.time() - 15)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreater(float(self.client.session["last_activity"]), time.time() - 30)

    def test_idle_heartbeat_does_not_extend_session(self):
        self.client.force_login(self.student_user)
        session = self.client.session
        session["last_activity"] = time.time() - 290
        session.save()

        response = self.client.post(
            reverse("session_activity"),
            {"last_activity": str(time.time() - 301)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 401)
