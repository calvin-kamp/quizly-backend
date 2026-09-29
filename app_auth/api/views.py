from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        data = {}

        if serializer.is_valid():
            saved_account = serializer.save()
            data = {
                "username": saved_account.username,
                "email": saved_account.email,
                "user_id": saved_account.pk,
            }

            return Response(data)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
