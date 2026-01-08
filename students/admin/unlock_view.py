from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import Student
from .lock import clear_lock

@csrf_exempt
def unlock_view(request, object_id):
    student = get_object_or_404(Student, pk=object_id)
    clear_lock(student)
    return JsonResponse({'status': 'unlocked'})
