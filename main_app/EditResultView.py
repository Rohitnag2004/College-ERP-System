from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from django.db.models import Q
from .models import Subject, Staff, Student, StudentResult
from .forms import EditResultForm
from django.urls import reverse


class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        staff = get_object_or_404(Staff, admin=request.user)
        resultForm.fields['subject'].queryset = Subject.objects.filter(Q(staff=staff) | Q(co_teachers=staff)).distinct()
        context = {
            'form': resultForm,
            'page_title': "Edit Student's Result"
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        staff = get_object_or_404(Staff, admin=request.user)
        form = EditResultForm(request.POST)
        form.fields['subject'].queryset = Subject.objects.filter(Q(staff=staff) | Q(co_teachers=staff)).distinct()
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            student = form.cleaned_data.get('student')
            subject = form.cleaned_data.get('subject')
            session = form.cleaned_data.get('session_year')
            if student.course_id != subject.course_id or student.session_id != session.pk:
                messages.warning(request, "Select a student enrolled in this subject's course and session.")
            else:
                result = StudentResult.objects.filter(student=student, subject=subject).first()
                if result is None:
                    messages.warning(request, "No result exists for this student and subject yet.")
                else:
                    result.exam = form.cleaned_data.get('exam')
                    result.test = form.cleaned_data.get('test')
                    result.save(update_fields=['exam', 'test', 'updated_at'])
                    messages.success(request, "Result updated.")
                    return redirect(reverse('edit_student_result'))
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "staff_template/edit_student_result.html", context)
