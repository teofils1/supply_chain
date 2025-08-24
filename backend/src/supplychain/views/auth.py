from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, "profile", None)

        response_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        if profile:
            response_data.update(
                {
                    "active_role": profile.active_role,
                    "roles": profile.roles,
                }
            )
        else:
            response_data.update(
                {
                    "active_role": None,
                    "roles": [],
                }
            )

        return Response(response_data)

    def patch(self, request):
        """Switch the user's active role"""
        user = request.user
        profile = getattr(user, "profile", None)

        if not profile:
            return Response(
                {"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        new_active_role = request.data.get("active_role")
        if not new_active_role:
            return Response(
                {"error": "active_role is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has this role assigned
        if not profile.has_role(new_active_role):
            return Response(
                {"error": f"You do not have the {new_active_role} role"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update the active role
        profile.active_role = new_active_role
        profile.save()

        # Return updated user info
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "active_role": profile.active_role,
                "roles": profile.roles,
            }
        )
