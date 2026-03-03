from django.tasks import task

from .utils import generate_lesson_summary
from .models import Lesson


@task()
def generate_lesson_summary_task(lesson_id):

    try:
        lesson = Lesson.objects.get(id=lesson_id)
        
        result = generate_lesson_summary(lesson)
        
        #  Saving the results back to the lesson model
        lesson.transcript = result['transcript']
        lesson.summary = result['summary']
        lesson.save()
        
        print(f"Successfully processed AI for Lesson {lesson_id}")
        
    except Lesson.DoesNotExist:
        print(f"Task failed: Lesson {lesson_id} not found.")
    except Exception as e:
        print(f"Task failed for Lesson {lesson_id}: {str(e)}")