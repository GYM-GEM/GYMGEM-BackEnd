from django.urls import path

from .views import (
	CommunityHashTagView,
	CommunityPostView,
	CommunityPostUpdateView,
	CommunityPostDetailView,
	CommunityPostByAuthorView,
	communityPostByProfileView,
	CommunityPostCommentsView,
	CommunityPostCommentDetailView,
	CommunityPostLikesView,
	CommunityPostLikesListView,
	CommunityCommentLikesView,
	CommunityCommentLikesListView,
)

urlpatterns = [
	# Posts list/create
	path("posts/", CommunityPostView.as_view({"get": "get", "post": "post"})),
	path("posts/trending-hashtags/", CommunityHashTagView.as_view({"get": "get"})),

	# Post detail
	path("posts/<int:post_id>/", CommunityPostDetailView.as_view({"get": "get"})),

	# Update/Delete post
	path("posts/<int:post_id>/update/", CommunityPostUpdateView.as_view({"put": "put"})),
	path("posts/<int:post_id>/delete/", CommunityPostUpdateView.as_view({"delete": "delete"})),

	# Posts by specific author (profile-id)
	path("posts/author/<int:author_id>/", CommunityPostByAuthorView.as_view({"get": "get"})),

	# My posts
	path("posts/me/", communityPostByProfileView.as_view({"get": "get"})),

	# Comments list/create for a post
	path(
		"posts/<int:post_id>/comments/",
		CommunityPostCommentsView.as_view({"get": "get", "post": "post"}),
	),

	# Comment detail update/delete
	path("comments/<int:comment_id>/", CommunityPostCommentDetailView.as_view({"get": "get"})),
	path("comments/<int:comment_id>/update/", CommunityPostCommentDetailView.as_view({"put": "put"})),
	path("comments/<int:comment_id>/delete/", CommunityPostCommentDetailView.as_view({"delete": "delete"})),

	# Post likes: like/unlike and list
	path("posts/<int:post_id>/like/", CommunityPostLikesView.as_view({"post": "post"})),
	path("posts/<int:post_id>/likes/", CommunityPostLikesListView.as_view({"get": "get"})),

	# Comment likes: like/unlike and list
	path("comments/<int:comment_id>/like/", CommunityCommentLikesView.as_view({"post": "post"})),
	path("comments/<int:comment_id>/likes/", CommunityCommentLikesListView.as_view({"get": "get"})),
]

