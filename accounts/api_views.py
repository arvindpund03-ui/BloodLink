from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET"])
def api_home(request):
    return Response({
        "success": True,
        "message": "Welcome to BloodLink API",
        "version": "1.0"
    })