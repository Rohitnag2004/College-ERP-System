from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Q
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone
from .storage import PrivateResourceStorage




class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required")
        email = self.normalize_email(email).lower()
        user = CustomUser(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", "1")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return f"{self.start_year.year}-{self.end_year.year}"


class CustomUser(AbstractUser):
    USER_TYPE = (("1", "Admin"), ("2", "Teacher"), ("3", "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default="1", choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER, blank=True)
    profile_pic = models.ImageField(upload_to="profiles/", blank=True, null=True)
    address = models.TextField(blank=True)
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.get_full_name() or self.email


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)



class Course(models.Model):
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    degree_level = models.CharField(max_length=40, blank=True)
    entry_type = models.CharField(max_length=40, blank=True)
    syllabus_year = models.PositiveSmallIntegerField(null=True, blank=True)
    duration = models.CharField(max_length=80, blank=True)
    total_semesters = models.PositiveSmallIntegerField(default=0)
    total_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fee_source_status = models.CharField(max_length=180, blank=True)
    lateral_entry_applicable = models.BooleanField(default=False)
    lateral_entry_admission_year = models.CharField(max_length=40, blank=True)
    lateral_entry_semester = models.PositiveSmallIntegerField(null=True, blank=True)
    lateral_entry_continuation = models.CharField(max_length=120, blank=True)
    lateral_entry_duration = models.CharField(max_length=80, blank=True)
    lateral_entry_total_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tuition_fee_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tuition_fee_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.tuition_fee_min is not None and self.tuition_fee_max is not None and self.tuition_fee_min > self.tuition_fee_max:
            raise ValidationError({"tuition_fee_max": "Maximum tuition must be at least the minimum tuition."})


class Semester(models.Model):
    """Editable semester plan; fee amounts are planning estimates until confirmed by Admin."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="semesters")
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=80)
    fee_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("course__name", "number")
        constraints = [models.UniqueConstraint(fields=("course", "number"), name="unique_course_semester_number")]

    def __str__(self):
        return f"{self.course.name} — {self.name}"

class Book(models.Model):
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.PositiveIntegerField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name) + " ["+str(self.isbn)+']'


class Student(models.Model):
    class EntryType(models.TextChoices):
        REGULAR = "regular", "Regular entry"
        LATERAL = "lateral", "Lateral entry"

    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    admission_type = models.CharField(max_length=10, choices=EntryType.choices, default=EntryType.REGULAR)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrolled_students")
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)
    can_edit_profile = models.BooleanField(
        default=False,
        help_text="When enabled, the student may update limited personal contact details.",
    )

    def __str__(self):
        return " ".join(part for part in (self.admin.first_name, self.admin.last_name) if part).strip()

class Library(models.Model):
    student = models.ForeignKey(Student,  on_delete=models.CASCADE, null=True, blank=False)
    book = models.ForeignKey(Book,  on_delete=models.CASCADE, null=True, blank=False)
    def __str__(self):
        return str(self.student)

def expiry():
    return timezone.localdate() + timedelta(days=14)
class IssuedBook(models.Model):
    student_id = models.CharField(max_length=100, blank=True) 
    isbn = models.CharField(max_length=13)
    issued_date = models.DateField(auto_now=True)
    expiry_date = models.DateField(default=expiry)



class Staff(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    approval_status = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey("main_app.CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_teacher_accounts")

    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"

    def __str__(self):
        return self.admin.first_name + " " +  self.admin.last_name


class Subject(models.Model):
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=40, blank=True, db_index=True)
    subject_type = models.CharField(max_length=40, blank=True)
    syllabus_year = models.PositiveSmallIntegerField(null=True, blank=True)
    source = models.CharField(max_length=180, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Teacher")
    co_teachers = models.ManyToManyField(Staff, blank=True, related_name="co_taught_subjects", verbose_name="Additional teachers")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name="subjects")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_sessions")
    class_topic = models.CharField(max_length=180, blank=True)
    starts_at = models.TimeField(null=True, blank=True)
    ends_at = models.TimeField(null=True, blank=True)
    created_by = models.ForeignKey("main_app.CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_class_attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    attendance_status = models.CharField(max_length=10, choices=Status.choices, default=Status.ABSENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("student", "attendance"), name="unique_attendance_per_student")
        ]


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    test = models.FloatField(default=0)
    exam = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CourseRegistration(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="course_registrations")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="registrations")
    session = models.ForeignKey(Session, on_delete=models.PROTECT, related_name="registrations", null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_course_registrations")
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ("-submitted_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "course", "session"),
                condition=Q(status="pending"),
                name="unique_pending_course_registration",
            ),
            models.UniqueConstraint(
                fields=("student",),
                condition=Q(status="approved"),
                name="unique_approved_course_per_student",
            ),
        ]

    def __str__(self):
        return f"{self.student} — {self.course} ({self.get_status_display()})"


class FeeStructure(models.Model):
    class EntryType(models.TextChoices):
        REGULAR = "regular", "Regular entry"
        LATERAL = "lateral", "Lateral entry"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="fee_structures")
    entry_type = models.CharField(max_length=10, choices=EntryType.choices, default=EntryType.REGULAR)
    session = models.ForeignKey(Session, on_delete=models.PROTECT, related_name="fee_structures", null=True, blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="fee_structures", null=True, blank=True)
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("due_date", "title")
        constraints = [
            models.UniqueConstraint(fields=("course", "session", "title"), name="unique_fee_title_per_course_session")
        ]

    def __str__(self):
        return f"{self.title} — {self.course} ({self.session})"


class TeacherAttendance(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="attendance_records")
    work_date = models.DateField(default=timezone.localdate)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-work_date", "-checked_in_at")
        constraints = [models.UniqueConstraint(fields=("staff", "work_date"), name="unique_teacher_attendance_per_day")]

    def __str__(self):
        return f"{self.staff} — {self.work_date}"


class TeacherPayrollProfile(models.Model):
    """Demo-only payout destination; it never represents a real bank account."""

    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name="payroll_profile")
    bank_name = models.CharField(max_length=80, default="Velocity Demo Bank")
    account_number = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Demo payroll account for {self.staff}"


class SalaryPayment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        PAID = "paid", "Paid (demo)"
        REJECTED = "rejected", "Rejected"

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="salary_payments")
    pay_period = models.CharField(max_length=7, help_text="YYYY-MM")
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    account_number = models.CharField(max_length=40)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    payment_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_salary_payments")

    class Meta:
        ordering = ("-pay_period", "staff__admin__first_name", "staff__admin__last_name")
        constraints = [models.UniqueConstraint(fields=("staff", "pay_period"), name="unique_salary_payment_per_teacher_period")]

    def __str__(self):
        return f"{self.staff} — {self.pay_period} ({self.get_status_display()})"


class FeePayment(models.Model):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PENDING = "pending", "Pending verification"
        PAID = "paid", "Paid"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_payments")
    fee = models.ForeignKey(FeeStructure, on_delete=models.PROTECT, related_name="payments")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    payment_reference = models.CharField(max_length=120, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_fee_payments")
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ("status", "fee__due_date")
        constraints = [
            models.UniqueConstraint(fields=("student", "fee"), name="unique_fee_record_per_student")
        ]

    def __str__(self):
        return f"{self.student} — {self.fee} ({self.get_status_display()})"


class Notice(models.Model):
    class Audience(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        TEACHERS = "teachers", "Teachers"
        STUDENTS = "students", "Students"

    title = models.CharField(max_length=180)
    message = models.TextField()
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.EVERYONE)
    published = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="notices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class CollegeResource(models.Model):
    class Audience(models.TextChoices):
        STUDENTS = "students", "Students"
        TEACHERS = "teachers", "Teachers and Admin"

    class ResourceType(models.TextChoices):
        NOTES = "notes", "Study Notes"
        MODULE = "module", "Study Module"
        NOTICE = "notice", "Academic Notice"
        OTHER = "other", "Other Resource"

    title = models.CharField(max_length=180)
    resource_type = models.CharField(max_length=12, choices=ResourceType.choices, default=ResourceType.NOTES)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="college_resources/", storage=PrivateResourceStorage())
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.STUDENTS)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_resources")
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_resources")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name="learning_resources")
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="college_resources")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "title")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.semester_id and self.course_id and self.semester.course_id != self.course_id:
            raise ValidationError({"semester": "Choose a semester from the selected course."})
        if self.subject_id and (self.subject.course_id != self.course_id or self.subject.semester_id != self.semester_id):
            raise ValidationError({"subject": "The selected subject must match the selected course and semester."})


class StudentGradeCard(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grade_cards")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="grade_cards")
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to="grade_cards/", storage=PrivateResourceStorage())
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="uploaded_grade_cards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("student__admin__last_name", "student__admin__first_name", "semester__number")
        constraints = [
            models.UniqueConstraint(fields=("student", "semester"), name="unique_student_grade_card_semester"),
        ]

    def __str__(self):
        return f"{self.student} — {self.title}"


class PortalAccessSettings(models.Model):
    """Admin-controlled availability for the student and teacher portals."""

    student_portal_enabled = models.BooleanField(default=True)
    teacher_portal_enabled = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="portal_access_updates",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portal availability"
        verbose_name_plural = "Portal availability"

    def __str__(self):
        return "Portal availability settings"


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == "1":
            Admin.objects.create(admin=instance)
        elif instance.user_type == "2":
            Staff.objects.create(admin=instance)
        elif instance.user_type == "3":
            Student.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    profile_model = {"1": Admin, "2": Staff, "3": Student}.get(instance.user_type)
    if profile_model:
        profile_model.objects.get_or_create(admin=instance)

# todos
