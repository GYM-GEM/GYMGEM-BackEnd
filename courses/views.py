from django.shortcuts import render
from rest_framework import APIView
from .models import Course
from .serializers import CourseSerializer
from rest_framework.response import Response

# Create your views here.
class CoursesView(APIView):
    
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
