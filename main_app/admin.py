from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin

from .models import (
    Admin, Attendance, AttendanceReport, Book, Course, CourseRegistration,
    FeePayment, FeeStructure, IssuedBook, LeaveReportStaff, LeaveReportStudent,
    Library, Notice, Session, Staff, Student, StudentResult, Subject,
)
from .models import CustomUser, FeedbackStaff, FeedbackStudent, NotificationStaff, NotificationStudent

admin.site.site_header = "Velocity Tech University Administration"
admin.site.site_title = "Velocity Tech University"
admin.site.index_title = "University administration"


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "user_type", "is_staff", "is_superuser")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = "__all__"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "user_type", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("first_name", "last_name", "gender", "address", "profile_pic")}),
        ("Portal access", {"fields": ("user_type",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "user_type", "password1", "password2", "is_staff", "is_superuser")}),
    )


@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "session", "status", "submitted_at", "reviewed_by")
    list_filter = ("status", "session", "course")
    search_fields = ("student__admin__email", "student__admin__first_name", "course__name")
    readonly_fields = ("submitted_at", "reviewed_at")


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "fee", "status", "payment_reference", "submitted_at", "reviewed_by")
    list_filter = ("status", "fee__session", "fee__course")
    search_fields = ("student__admin__email", "payment_reference", "fee__title")
    readonly_fields = ("submitted_at", "reviewed_at")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "published", "created_by", "created_at")
    list_filter = ("audience", "published")
    search_fields = ("title", "message")


admin.site.register([
    Admin, Attendance, AttendanceReport, Book, Course, FeeStructure, IssuedBook,
    LeaveReportStaff, LeaveReportStudent, Library, NotificationStaff,
    NotificationStudent, Session, Staff, Student, StudentResult, Subject,
    FeedbackStaff, FeedbackStudent,
])
