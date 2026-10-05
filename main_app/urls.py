"""college_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from main_app.EditResultView import EditResultView

from . import hod_views, staff_views, student_views, views
from . import portal_views

urlpatterns = [
    path("", views.login_page, name='login_page'),
    path("login/<str:role>/", views.role_login_page, name="role_login_page"),
    path("register/", views.register_page, name="register_page"),
    path("register/<str:role>/", views.role_register_page, name="role_register_page"),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("session-activity/", views.session_activity, name="session_activity"),
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification,
         name='send_student_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification,
         name='send_staff_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student,
         name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff,
         name='admin_notify_staff'),
    path("admin_view_profile", hod_views.admin_view_profile,
         name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability,
         name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>",
         hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message,
         name="student_feedback_message",),
    path("staff/view/feedback/", hod_views.staff_feedback_message,
         name="staff_feedback_message",),
    path("student/view/leave/", hod_views.view_student_leave,
         name="view_student_leave",),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave",),
    path("attendance/view/", hod_views.admin_view_attendance,
         name="admin_view_attendance",),
    path("attendance/subjects/", hod_views.get_admin_attendance_subjects,
         name="get_admin_attendance_subjects"),
    path("attendance/fetch/", hod_views.get_admin_attendance,
         name='get_admin_attendance'),
    path("attendance/save-admin/", hod_views.admin_save_attendance, name="admin_save_attendance"),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("admin/teacher-approvals/", portal_views.manage_teacher_approvals, name="manage_teacher_approvals"),
    path("admin/portal-availability/", portal_views.admin_portal_availability, name="admin_portal_availability"),
    path("admin/payment-department/salaries/", portal_views.admin_salary_payments, name="admin_salary_payments"),
    path("admin/admin-accounts/", portal_views.manage_admin_accounts, name="manage_admin_accounts"),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>",
         hod_views.delete_staff, name='delete_staff'),

    path("course/delete/<int:course_id>",
         hod_views.delete_course, name='delete_course'),

    path("subject/delete/<int:subject_id>",
         hod_views.delete_subject, name='delete_subject'),

    path("session/delete/<int:session_id>",
         hod_views.delete_session, name='delete_session'),

    path("student/delete/<int:student_id>",
         hod_views.delete_student, name='delete_student'),
    path("student/edit/<int:student_id>",
         hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>",
         hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>",
         hod_views.edit_subject, name='edit_subject'),


    # Staff
    path("staff/home/", staff_views.staff_home, name='staff_home'),
    path("staff/apply/leave/", staff_views.staff_apply_leave,
         name='staff_apply_leave'),
    path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
    path("staff/view/profile/", staff_views.staff_view_profile,
         name='staff_view_profile'),
    path("staff/work-attendance/", staff_views.staff_work_attendance, name="staff_work_attendance"),
    path("staff/work-attendance/mark/", staff_views.mark_work_attendance, name="mark_work_attendance"),
    path("staff/attendance/take/", staff_views.staff_take_attendance,
         name='staff_take_attendance'),
    path("staff/attendance/update/", staff_views.staff_update_attendance,
         name='staff_update_attendance'),
    path("staff/get_students/", staff_views.get_students, name='get_students'),
    path("staff/addbook/", portal_views.manage_books, name="add_book"),
    path("library/manage/", portal_views.manage_books, name="manage_books"),
    path("library/manage/<int:book_id>/", portal_views.manage_books, name="edit_book"),
    path("staff/issue_book/", staff_views.issue_book, name="issue_book"),
    path("staff/view_issued_book/", staff_views.view_issued_book, name="view_issued_book"),



    path("staff/attendance/fetch/", staff_views.get_student_attendance,
         name='get_student_attendance'),
    path("staff/attendance/save/",
         staff_views.save_attendance, name='save_attendance'),
    path("staff/attendance/update_save/",
         staff_views.update_attendance, name='update_attendance'),
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name='staff_fcmtoken'),
    path("staff/view/notification/", staff_views.staff_view_notification,
         name="staff_view_notification"),
    path("staff/result/add/", staff_views.staff_add_result, name='staff_add_result'),
    path("staff/result/edit/", EditResultView.as_view(),
         name='edit_student_result'),
    path('staff/result/fetch/', staff_views.fetch_student_result,
         name='fetch_student_result'),



    # Student
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/view/attendance/", student_views.student_view_attendance,
         name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave,
         name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback,
         name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile,
         name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken,
         name='student_fcmtoken'),
     # path('student/todo',student_views.todo,name='todo'),

     
     path("student/viewbooks/", student_views.view_books, name="view_books"),

    path("student/view/notification/", student_views.student_view_notification,
         name="student_view_notification"),
    path('student/view/result/', student_views.student_view_result,
         name='student_view_result'),

    # Course registration, fees, and notice board
    path("student/courses/register/", portal_views.student_course_registration, name="student_course_registration"),
    path("admin/course-registrations/", portal_views.admin_course_registrations, name="admin_course_registrations"),
    path("admin/course-registrations/<int:registration_id>/review/", portal_views.review_course_registration, name="review_course_registration"),
    path("student/fees/", portal_views.student_fees, name="student_fees"),
    path("fees/payment/<int:payment_id>/receipt/", portal_views.fee_payment_receipt, name="fee_payment_receipt"),
    path("admin/fees/", portal_views.admin_fees, name="admin_fees"),
    path("admin/fee-payment-reviews/", portal_views.admin_payment_reviews, name="admin_payment_reviews"),
    path("admin/teacher-assignments/", portal_views.admin_teacher_assignments, name="admin_teacher_assignments"),
    path("admin/semesters/", portal_views.admin_semesters, name="admin_semesters"),
    path("admin/teacher-attendance/", portal_views.admin_teacher_attendance, name="admin_teacher_attendance"),
    path("student/fees/<int:payment_id>/demo-checkout/", portal_views.demo_fee_checkout, name="demo_fee_checkout"),
    path("notices/", portal_views.notice_board, name="notice_board"),
    path("admin/notices/", portal_views.manage_notices, name="manage_notices"),
    path("admin/learning-resources/", portal_views.admin_learning_resources, name="admin_learning_resources"),
    path("teacher/learning-resources/", portal_views.teacher_learning_resources, name="teacher_learning_resources"),
    path("student/learning-resources/", portal_views.student_learning_resources, name="student_learning_resources"),
    path("learning-resources/<int:resource_id>/download/", portal_views.download_learning_resource, name="download_learning_resource"),
    path("grade-cards/", portal_views.grade_cards, name="grade_cards"),
    path("grade-cards/<int:grade_card_id>/download/", portal_views.download_grade_card, name="download_grade_card"),
    path("portal/maintenance/", portal_views.portal_maintenance, name="portal_maintenance"),
    path("teacher/salary/", portal_views.teacher_salary_payments, name="teacher_salary_payments"),
    path("salary/receipt/<int:salary_id>/", portal_views.salary_payment_receipt, name="salary_payment_receipt"),

]
