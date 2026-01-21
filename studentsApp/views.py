from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
def students(request):
    return HttpResponse('<h2> Hello world </h2>')