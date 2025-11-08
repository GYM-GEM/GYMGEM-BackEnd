from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Trainee
from .serializers import TraineeSerializer

# Create your views here.
class TraineeView(APIView):
    
    def get(self, request):
        trainees = Trainee.objects.all()
        serializer = TraineeSerializer(trainees, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TraineeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)  

class TraineeUpdateView(APIView):
    def put(self, request, trainee_id):
        try:
            trainee = Trainee.objects.get(id=trainee_id)
        except Trainee.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        serializer = TraineeSerializer(trainee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    def delete(self, request, trainee_id):
        try:
            trainee = Trainee.objects.get(id=trainee_id)
        except Trainee.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        trainee.delete()
        return Response(status=204)
    
    def patch(self, request, trainee_id):
        try:
            trainee = Trainee.objects.get(id=trainee_id)
        except Trainee.DoesNotExist:
            return Response({"error": "Trainee not found"}, status=404)
        
        serializer = TraineeSerializer(trainee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)