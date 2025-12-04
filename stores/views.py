from .serializers import StoreBranchSerializer, StoreSerializer
from .models import Store , StoreBranch
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class StoreView(APIView):

    def get(self, request):
       stores = Store.objects.all()
       serializer = StoreSerializer(stores, many=True)
       return Response(serializer.data)
    
    def post(self, request):
        serializer = StoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class StoreUpdateView(APIView):
    def put(self, request, store_id):
        try:
            store = Store.objects.get(profile_id=store_id)
        except Store.DoesNotExist:
            return Response({"error": "Store not found"}, status=404)

        serializer = StoreSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, store_id):
        try:
            store = Store.objects.get(profile_id=store_id)
        except Store.DoesNotExist:
            return Response({"error": "Store not found"}, status=404)

        store.delete()
        return Response(status=204)

    def patch(self, request, store_id):
        try:
            store = Store.objects.get(profile_id=store_id)
        except Store.DoesNotExist:
            return Response({"error": "Store not found"}, status=404)

        serializer = StoreSerializer(store, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class StoreBranchView(APIView):

    def get(self, request):
       storebranches = StoreBranch.objects.all()
       serializer = StoreBranchSerializer(storebranches, many=True)
       return Response(serializer.data)
    
    def post(self, request):
        serializer = StoreBranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class StoreBranchUpdateView(APIView):
    def put(self, request, branch_id):
        try:
            storebranch = StoreBranch.objects.get(id=branch_id)
        except StoreBranch.DoesNotExist:
            return Response({"error": "StoreBranch not found"}, status=404)

        serializer = StoreBranchSerializer(storebranch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, branch_id):
        try:
            storebranch = StoreBranch.objects.get(id=branch_id)
        except StoreBranch.DoesNotExist:
            return Response({"error": "StoreBranch not found"}, status=404)

        storebranch.delete()
        return Response(status=204)

    def patch(self, request, branch_id):
        try:
            storebranch = StoreBranch.objects.get(id=branch_id)
        except StoreBranch.DoesNotExist:
            return Response({"error": "StoreBranch not found"}, status=404)

        serializer = StoreBranchSerializer(storebranch, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)