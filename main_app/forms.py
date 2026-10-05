from django import forms
from django.contrib.auth.password_validation import validate_password
from django.forms.widgets import DateInput, TextInput
from pathlib import Path
from django.db.models import Q

from .models import *
from . import models


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = (self.cleaned_data.get('email') or '').strip().lower()
        if not formEmail and self.instance.pk:
            return self.instance.admin.email
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            if CustomUser.objects.exclude(pk=self.instance.admin_id).filter(email__iexact=formEmail).exists():
                raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender',  'password','profile_pic', 'address' ]


class StudentForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['course', 'semester', 'session', 'admission_type']

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get("course")
        semester = cleaned.get("semester")
        if semester and not course:
            self.add_error("course", "Select a course for this semester.")
        elif course and semester and semester.course_id != course.pk:
            self.add_error("semester", "Choose a semester that belongs to the selected course.")
        return cleaned


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class StaffForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields + \
            ['course' ]


class CourseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name', 'degree_level', 'entry_type', 'description', 'duration', 'syllabus_year', 'total_semesters', 'total_fee', 'fee_source_status', 'lateral_entry_applicable', 'lateral_entry_admission_year', 'lateral_entry_semester', 'lateral_entry_continuation', 'lateral_entry_duration', 'lateral_entry_total_fee', 'tuition_fee_min', 'tuition_fee_max', 'is_active']
        model = Course


class SubjectForm(FormSettings):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'subject_type', 'syllabus_year', 'source', 'course', 'semester', 'staff']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff'].queryset = Staff.objects.filter(approval_status=Staff.ApprovalStatus.APPROVED).select_related('admin').order_by('admin__first_name', 'admin__last_name')
        self.fields['staff'].required = False
        self.fields['staff'].empty_label = "Unassigned"
        self.fields['semester'].queryset = Semester.objects.select_related('course').order_by('course__name', 'number')
        self.fields['semester'].required = False

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get("course")
        semester = cleaned.get("semester")
        if course and semester and semester.course_id != course.pk:
            self.add_error("semester", "Choose a semester from the selected course.")
        return cleaned


class AdminAccountForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirmation = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirmation = cleaned.get("password_confirmation")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirmation", "The passwords do not match.")
        if password:
            candidate = CustomUser(email=cleaned.get("email", ""), first_name=cleaned.get("first_name", ""), last_name=cleaned.get("last_name", ""))
            try:
                validate_password(password, user=candidate)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned


class SessionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            'start_year': DateInput(attrs={'type': 'date'}),
            'end_year': DateInput(attrs={'type': 'date'}),
        }


class LeaveReportStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStaff
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStaffForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStaff
        fields = ['feedback']


class LeaveReportStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStudentForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStudent
        fields = ['feedback']


class OptionalEditFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            field.widget.attrs.pop("required", None)
        if "gender" in self.fields:
            self.fields["gender"].choices = [("", "Keep current gender")] + list(self.fields["gender"].choices)


class StudentEditForm(OptionalEditFormMixin, StudentForm):
    can_edit_profile = forms.BooleanField(
        required=False,
        label="Allow student to edit personal details",
        help_text="Students can update their name, email, gender, address, and profile picture only when enabled.",
    )
    account_active = forms.ChoiceField(
        required=False,
        label="Account access",
        choices=(("", "Keep current"), ("1", "Active"), ("0", "Disabled")),
        help_text="Current: active or disabled; choose a new value only if it should change.",
    )
    remove_profile_pic = forms.BooleanField(required=False, label="Remove current profile picture")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["account_active"].initial = "1" if self.instance.admin.is_active else "0"
            self.fields["account_active"].help_text = f"Current status: {'active' if self.instance.admin.is_active else 'disabled'}."
            self.fields["can_edit_profile"].initial = self.instance.can_edit_profile


class StudentSelfProfileForm(forms.ModelForm):
    """Limited student form. Course, session, access, and password stay admin-controlled."""

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "gender", "address", "profile_pic")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gender"].required = False
        self.fields["profile_pic"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class StaffEditForm(OptionalEditFormMixin, StaffForm):
    account_active = forms.ChoiceField(
        required=False,
        label="Account access",
        choices=(("", "Keep current"), ("1", "Active"), ("0", "Disabled")),
    )
    approval_status = forms.ChoiceField(
        required=False,
        label="Teacher approval",
        choices=(("", "Keep current"),) + tuple(Staff.ApprovalStatus.choices),
    )
    remove_profile_pic = forms.BooleanField(required=False, label="Remove current profile picture")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["account_active"].initial = "1" if self.instance.admin.is_active else "0"
            self.fields["account_active"].help_text = f"Current status: {'active' if self.instance.admin.is_active else 'disabled'}."
            self.fields["approval_status"].initial = self.instance.approval_status
            self.fields["approval_status"].initial = self.instance.approval_status


class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        label="Session Year", queryset=session_list, required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']

#todos
# class TodoForm(forms.ModelForm):
#     class Meta:
#         model=Todo
#         fields=["title","is_finished"]

#issue book

class IssueBookForm(forms.Form):
    isbn2 = forms.ModelChoiceField(queryset=models.Book.objects.all(), empty_label="Book Name [ISBN]", to_field_name="isbn", label="Book (Name and ISBN)")
    name2 = forms.ModelChoiceField(queryset=models.Student.objects.select_related("admin").all(), empty_label="Name ", to_field_name="pk", label="Student Details")
    
    isbn2.widget.attrs.update({'class': 'form-control'})
    name2.widget.attrs.update({'class':'form-control'})


class BookForm(FormSettings):
    class Meta:
        model = Book
        fields = ("name", "author", "isbn", "category")


class FeeStructureForm(FormSettings):
    class Meta:
        model = FeeStructure
        fields = ("course", "entry_type", "session", "semester", "title", "amount", "due_date", "is_active")
        widgets = {"due_date": DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["semester"].queryset = Semester.objects.select_related("course").order_by("course__name", "number")
        self.fields["semester"].required = False


class NoticeForm(FormSettings):
    class Meta:
        model = Notice
        fields = ("title", "message", "audience", "published")
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}


class SemesterCourseSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        semester = getattr(value, "instance", None)
        if semester:
            option["attrs"]["data-course"] = str(semester.course_id)
        return option


class SubjectScopeSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        subject = getattr(value, "instance", None)
        if subject:
            option["attrs"]["data-course"] = str(subject.course_id)
            option["attrs"]["data-semester"] = str(subject.semester_id or "")
        return option


class CollegeResourceForm(FormSettings):
    class Meta:
        model = CollegeResource
        fields = ("title", "resource_type", "description", "file", "audience", "course", "semester", "subject", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "semester": SemesterCourseSelect(),
            "subject": SubjectScopeSelect(),
        }

    def __init__(self, *args, **kwargs):
        self.uploader_role = str(kwargs.pop("uploader_role", "1"))
        assigned_course_id = kwargs.pop("assigned_course_id", None)
        teacher_id = kwargs.pop("teacher_id", None)
        super().__init__(*args, **kwargs)
        self.fields["course"].required = False
        self.fields["semester"].required = False
        self.fields["semester"].queryset = Semester.objects.select_related("course").order_by("course__name", "number")
        if self.uploader_role == "2":
            self.fields.pop("audience")
            self.fields.pop("is_active")
            assigned_subjects = Q(subject__staff__admin_id=teacher_id) | Q(subject__co_teachers__admin_id=teacher_id)
            self.fields["course"].queryset = Course.objects.filter(
                assigned_subjects, subject__semester__isnull=False,
            ).distinct().order_by("name")
            self.fields["semester"].queryset = Semester.objects.filter(
                Q(subjects__staff__admin_id=teacher_id) | Q(subjects__co_teachers__admin_id=teacher_id),
            ).select_related("course").distinct().order_by("course__name", "number")
            self.fields["subject"].queryset = Subject.objects.filter(
                (Q(staff__admin_id=teacher_id) | Q(co_teachers__admin_id=teacher_id)), semester__isnull=False,
            ).select_related("course", "semester").order_by("course__name", "semester__number", "name")
            self.fields["course"].required = True
            self.fields["semester"].required = True
            self.fields["subject"].required = True
        elif self.uploader_role != "1":
            self.fields["course"].queryset = Course.objects.none()
            self.fields["subject"].queryset = Subject.objects.none()

    def clean_file(self):
        upload = self.cleaned_data.get("file")
        if upload:
            allowed = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".png", ".jpg", ".jpeg", ".webp"}
            if Path(upload.name).suffix.lower() not in allowed:
                raise forms.ValidationError("Upload a PDF, Office document, text file, or image.")
            if upload.size > 25 * 1024 * 1024:
                raise forms.ValidationError("The maximum file size is 25 MB.")
        return upload

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get("course")
        semester = cleaned.get("semester")
        subject = cleaned.get("subject")
        if subject and (subject.course_id != getattr(course, "pk", None) or subject.semester_id != getattr(semester, "pk", None)):
            self.add_error("subject", "Choose a subject assigned to the selected course and semester.")
        if semester and not course:
            self.add_error("course", "Choose the course for this semester resource.")
        if course and semester and semester.course_id != course.pk:
            self.add_error("semester", "Choose a semester from the selected course.")
        return cleaned


class StudentGradeCardForm(FormSettings):
    class Meta:
        model = StudentGradeCard
        fields = ("student", "semester", "title", "file")

    def __init__(self, *args, **kwargs):
        teacher_id = kwargs.pop("teacher_id", None)
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.select_related("admin", "course", "session").order_by("admin__last_name", "admin__first_name")
        self.fields["semester"].queryset = Semester.objects.select_related("course").order_by("course__name", "number")
        self.fields["file"].required = not bool(self.instance.pk and self.instance.file)
        if teacher_id:
            assigned = Q(subjects__staff__admin_id=teacher_id) | Q(subjects__co_teachers__admin_id=teacher_id)
            self.fields["semester"].queryset = self.fields["semester"].queryset.filter(assigned).distinct()
            assigned_course_ids = Subject.objects.filter(
                Q(staff__admin_id=teacher_id) | Q(co_teachers__admin_id=teacher_id)
            ).values("course_id")
            self.fields["student"].queryset = self.fields["student"].queryset.filter(
                course_id__in=assigned_course_ids
            ).distinct()
        self.teacher_id = teacher_id

    def clean_file(self):
        upload = self.cleaned_data.get("file")
        if upload:
            allowed = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
            if Path(upload.name).suffix.lower() not in allowed:
                raise forms.ValidationError("Upload a PDF or image file.")
            if upload.size > 25 * 1024 * 1024:
                raise forms.ValidationError("The maximum file size is 25 MB.")
        return upload

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get("student")
        semester = cleaned.get("semester")
        if student and semester and student.course_id != semester.course_id:
            self.add_error("semester", "Choose a semester from the student's enrolled course.")
        if student and semester and student.course_id == semester.course_id:
            duplicate = StudentGradeCard.objects.filter(student=student, semester=semester)
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                self.add_error("semester", "A grade card already exists for this student's semester. Edit that record instead.")
        if self.teacher_id and semester:
            assigned = Q(staff__admin_id=self.teacher_id) | Q(co_teachers__admin_id=self.teacher_id)
            if not Subject.objects.filter(course_id=semester.course_id, semester=semester).filter(assigned).exists():
                self.add_error("semester", "You can only manage grade cards for semesters assigned to you.")
        if not cleaned.get("file") and not (self.instance.pk and self.instance.file):
            self.add_error("file", "Upload the grade card file.")
        return cleaned


class SelfRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    email = forms.EmailField()
    gender = forms.ChoiceField(
        choices=(("", "Prefer not to say"), ("M", "Male"), ("F", "Female")),
        required=False,
    )
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    password = forms.CharField(widget=forms.PasswordInput, strip=False)
    password_confirmation = forms.CharField(label="Confirm password", widget=forms.PasswordInput, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirmation = cleaned.get("password_confirmation")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirmation", "The passwords do not match.")
        if password:
            candidate = CustomUser(
                email=cleaned.get("email", ""),
                first_name=cleaned.get("first_name", ""),
                last_name=cleaned.get("last_name", ""),
            )
            try:
                validate_password(password, user=candidate)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned

    def create_user(self, user_type):
        data = self.cleaned_data
        create_account = CustomUser.objects.create_superuser if user_type == "1" else CustomUser.objects.create_user
        return create_account(
            email=data["email"],
            password=data["password"],
            user_type=user_type,
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            gender=data.get("gender", ""),
            address=data.get("address", "").strip(),
        )
