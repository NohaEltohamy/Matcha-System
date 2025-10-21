# job_board/permissions.py

from rest_framework import permissions

class IsRecruiterOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow recruiters to create/update/delete
    their own jobs, and admins to view all.
    """

    def has_permission(self, request, view):
        # Admins can do anything
        if request.user and request.user.is_staff:
            return True

        # Recruiters can create jobs
        if view.action == 'create':
            # Assuming a custom user model with an 'is_recruiter' field or similar
            # You might need to adjust this check based on your User model.
            # E.g., request.user.groups.filter(name='Recruiters').exists()
            return request.user and getattr(request.user, 'is_recruiter', False)
        
        # Other actions (list, retrieve, update, destroy) are handled by has_object_permission
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins can view/edit/delete any job
        if request.user and request.user.is_staff:
            return True

        # Recruiters can only retrieve, update, or delete their own jobs
        if request.user and getattr(request.user, 'is_recruiter', False):
            # Read permissions are allowed to any authenticated recruiter
            if request.method in permissions.SAFE_METHODS:
                return True
            # Write permissions are only allowed to the recruiter who owns the job
            return obj.recruiter == request.user
        
        # Deny all other requests
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Admins can do anything.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admins can do anything
        if request.user and request.user.is_staff:
            return True

        # Write permissions are only allowed to the owner of the job.
        return obj.recruiter == request.user
