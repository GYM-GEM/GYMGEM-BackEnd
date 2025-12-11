from django.shortcuts import render

from community.models import CommunityPost, CommunityComment, CommunityCommentLike, CommunityLike
from community.serializers import CommunityPostSerializer, CommunityLikeSerializer, CommunityCommentSerializer, CommunityCommentLikeSerializer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet as viewSet
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from utils.views import get_profile_id_from_token
# Create your views here.
class CommunityPostView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="List all community posts",
        description="Retrieve all community posts",
        responses={200: CommunityPostSerializer(many=True)},
    )
    def get(self, request):
        from django.db.models import Count
        posts = (
            CommunityPost.objects.all()
            .select_related('author__account')
            .annotate(
                comments_count=Count('comments'),
                likes_count=Count('likes')
            )
            .order_by('-created_at')
        )
        serializer = CommunityPostSerializer(posts, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Community"],
        summary="Create community post",
        description="Create a new community post",
        request=CommunityPostSerializer,
        responses={201: CommunityPostSerializer, 400: {"description": "Validation error"}},
    )
    def post(self, request):
        serializer = CommunityPostSerializer(data=request.data, context={"request": request})
        author = get_profile_id_from_token(request)
        if serializer.is_valid():
            serializer.save(author_id=author)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class CommunityPostUpdateView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="Update community post",
        description="Update an existing community post",
        request=CommunityPostSerializer,
        responses={200: CommunityPostSerializer, 404: {"description": "Post not found"}, 400: {"description": "Validation error"}},
    )
    def put(self, request, post_id):
        try:
            my_profile = get_profile_id_from_token(request)
            post = CommunityPost.objects.get(id=post_id, author_id=my_profile)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        serializer = CommunityPostSerializer(post, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    @extend_schema(
        tags=["Community"],
        summary="Delete community post",
        description="Delete an existing community post",
        responses={204: {"description": "Post deleted"}, 404: {"description": "Post not found"}},
    )
    def delete(self, request, post_id):
        try:
            my_profile = get_profile_id_from_token(request)
            post = CommunityPost.objects.get(id=post_id, author_id=my_profile)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        post.delete()
        return Response(status=204)

class CommunityPostDetailView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="Retrieve community post details",
        description="Get details of a specific community post",
        responses={200: CommunityPostSerializer, 404: {"description": "Post not found"}},
    )
    def get(self, request, post_id):
        try:
            post = CommunityPost.objects.select_related('author__account').get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        serializer = CommunityPostSerializer(post)
        return Response(serializer.data)
    
class CommunityPostByAuthorView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="List community posts by author",
        description="Retrieve all community posts by a specific author",
        responses={200: CommunityPostSerializer(many=True)},
    )
    def get(self, request, author_id):
        posts = CommunityPost.objects.filter(author_id=author_id).select_related('author__account').order_by('-created_at')
        serializer = CommunityPostSerializer(posts, many=True)
        return Response(serializer.data)
    
class communityPostByProfileView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="List community posts by my profile",
        description="Retrieve all community posts by my profile",
        responses={200: CommunityPostSerializer(many=True)},
    )
    def get(self, request):
        my_profile = get_profile_id_from_token(request)
        posts = CommunityPost.objects.filter(author_id=my_profile).select_related('author__account').order_by('-created_at')
        serializer = CommunityPostSerializer(posts, many=True)
        return Response(serializer.data)
    
    
class CommunityPostCommentsView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="List comments for a community post",
        description="Retrieve all comments for a specific community post",
        responses={200: CommunityCommentSerializer(many=True)},
    )
    def get(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        comments = post.comments.select_related('author__account').order_by('-created_at')
        serializer = CommunityCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=["Community"],
        summary="Create comment",
        description="Create a new comment on a community post",
        request=CommunityCommentSerializer,
        responses={201: CommunityCommentSerializer, 404: {"description": "Post not found"}, 400: {"description": "Validation error"}},
    )
    def post(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        serializer = CommunityCommentSerializer(data={**request.data, "post": post_id}, context={"request": request})
        my_profile = get_profile_id_from_token(request)
        if serializer.is_valid():
            serializer.save(post=post, author_id=my_profile)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class CommunityPostCommentDetailView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="Retrieve comment details",
        description="Get details of a specific comment on a community post",
        responses={200: CommunityCommentSerializer, 404: {"description": "Comment not found"}},
    )
    def get(self, request, comment_id):
        try:
            comment = CommunityComment.objects.select_related('author__account').get(id=comment_id)
        except CommunityComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)
        serializer = CommunityCommentSerializer(comment)
        return Response(serializer.data)
    
    @extend_schema(
        tags=["Community"],
        summary="Update comment",
        description="Update an existing comment on a community post",
        request=CommunityCommentSerializer,
        responses={200: CommunityCommentSerializer, 404: {"description": "Comment not found"}, 400: {"description": "Validation error"}},
    )
    def put(self, request, comment_id):
        try:
            my_profile = get_profile_id_from_token(request)
            comment = CommunityComment.objects.get(id=comment_id, author_id=my_profile)
        except CommunityComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)
        serializer = CommunityCommentSerializer(comment, data={**request.data, "post": comment.post_id}, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    @extend_schema(
        tags=["Community"],
        summary="Delete comment",
        description="Delete an existing comment on a community post",
        responses={204: {"description": "Comment deleted"}, 404: {"description": "Comment not found"}},
    )
    def delete(self, request, comment_id):
        try:
            my_profile = get_profile_id_from_token(request)
            comment = CommunityComment.objects.get(id=comment_id, author_id=my_profile)
        except CommunityComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)

        comment.delete()
        return Response(status=204)
    
class CommunityPostLikesView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="Like a community post",
        description="Like a specific community post",
        responses={200: CommunityLikeSerializer, 404: {"description": "Post not found"}},
    )
    def post(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        my_profile = get_profile_id_from_token(request)
        try:
            if CommunityLike.objects.filter(post=post, profile_id=my_profile).exists():
                CommunityLike.objects.filter(post=post, profile_id=my_profile).delete()
                return Response({"message": "Post unliked"}, status=204)
            else:
                like, _created = CommunityLike.objects.get_or_create(post=post, profile_id=my_profile)
                serializer = CommunityLikeSerializer(like)
                return Response(serializer.data, status=200)
        except CommunityLike.DoesNotExist:
            pass


class CommunityPostLikesListView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="List post likes",
        description="Retrieve all likes for a specific community post",
        responses={200: CommunityLikeSerializer(many=True)},
    )
    def get(self, request, post_id):
        try:
            post = CommunityPost.objects.get(id=post_id)
        except CommunityPost.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        likes = post.likes.select_related('profile__account').order_by('-created_at')
        serializer = CommunityLikeSerializer(likes, many=True)
        return Response(serializer.data)


class CommunityCommentLikesView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="Like a comment",
        description="Like a specific comment",
        responses={200: CommunityCommentLikeSerializer, 404: {"description": "Comment not found"}},
    )
    def post(self, request, comment_id):
        try:
            comment = CommunityComment.objects.get(id=comment_id)
        except CommunityComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)
        try:
            if CommunityCommentLike.objects.filter(comment=comment, profile_id=get_profile_id_from_token(request)).exists():
                CommunityCommentLike.objects.filter(comment=comment, profile_id=get_profile_id_from_token(request)).delete()
                return Response({"message": "Comment unliked"}, status=204)
            else:
                like, _created = CommunityCommentLike.objects.get_or_create(comment=comment, profile_id=get_profile_id_from_token(request))
                serializer = CommunityCommentLikeSerializer(like)
                return Response(serializer.data, status=200)
        except CommunityCommentLike.DoesNotExist:
            return Response({"error": "Like operation failed"}, status=400)


class CommunityCommentLikesListView(viewSet):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=["Community"],
        summary="List comment likes",
        description="Retrieve all likes for a specific comment",
        responses={200: CommunityCommentLikeSerializer(many=True)},
    )
    def get(self, request, comment_id):
        try:
            comment = CommunityComment.objects.get(id=comment_id)
        except CommunityComment.DoesNotExist:
            return Response({"error": "Comment not found"}, status=404)

        likes = comment.likes.select_related('profile__account').order_by('-created_at')
        serializer = CommunityCommentLikeSerializer(likes, many=True)
        return Response(serializer.data)