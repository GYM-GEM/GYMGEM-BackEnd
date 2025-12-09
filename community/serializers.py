from .models import CommunityPost, CommunityComment, CommunityLike, CommunityCommentLike
from rest_framework import serializers

class CommunityPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    likes_count = serializers.SerializerMethodField(read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_profile_picture = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CommunityPost
        fields = ['id', 'title', 'content', 'author', 'author_id', 'author_name', 'author_profile_picture', 'created_at', 'updated_at', 'comments_count', 'likes_count']
    
    def get_author_name(self, obj):
        profile = getattr(obj, 'author', None)
        return _get_profile_display_name(profile)

    def get_comments_count(self, obj):
        # Prefer annotated value if present
        annotated = getattr(obj, 'comments_count', None)
        if annotated is not None:
            return annotated
        return obj.comments.count()

    def get_likes_count(self, obj):
        annotated = getattr(obj, 'likes_count', None)
        if annotated is not None:
            return annotated
        return obj.likes.count()

    def get_author_profile_picture(self, obj):
        profile = getattr(obj, 'author', None)
        return _get_profile_picture(profile)
        
class CommunityCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField(read_only=True)
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_profile_picture = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CommunityComment
        fields = ['id', 'post', 'author', 'author_id', 'author_name', 'author_profile_picture', 'content', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        profile = getattr(obj, 'author', None)
        return _get_profile_display_name(profile)
    
    def get_author_profile_picture(self, obj):
        profile = getattr(obj, 'author', None)
        return _get_profile_picture(profile)
        
class CommunityLikeSerializer(serializers.ModelSerializer):
    profile_name = serializers.SerializerMethodField(read_only=True)
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    profile_profile_picture = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CommunityLike
        fields = ['id', 'post', 'profile', 'profile_id', 'profile_name', 'profile_profile_picture', 'created_at']

    def get_profile_name(self, obj):
        profile = getattr(obj, 'profile', None)
        return _get_profile_display_name(profile)

    def get_profile_profile_picture(self, obj):
        profile = getattr(obj, 'profile', None)
        return _get_profile_picture(profile)


class CommunityCommentLikeSerializer(serializers.ModelSerializer):
    profile_name = serializers.SerializerMethodField(read_only=True)
    profile_id = serializers.IntegerField(source='profile.id', read_only=True)
    profile_profile_picture = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CommunityCommentLike
        fields = ['id', 'comment', 'profile', 'profile_id', 'profile_name', 'profile_profile_picture', 'created_at']

    def get_profile_name(self, obj):
        profile = getattr(obj, 'profile', None)
        return _get_profile_display_name(profile)

    def get_profile_profile_picture(self, obj):
        profile = getattr(obj, 'profile', None)
        return _get_profile_picture(profile)


def _get_profile_display_name(profile):
    if not profile:
        return None
    # Try trainer
    trainer = getattr(profile, 'trainer', None)
    if trainer and getattr(trainer, 'name', None):
        return trainer.name
    # Try trainee
    trainee = getattr(profile, 'trainee', None)
    if trainee and getattr(trainee, 'name', None):
        return trainee.name
    # Try gym
    gym = getattr(profile, 'gym', None)
    if gym and getattr(gym, 'name', None):
        return gym.name
    # Try store
    store = getattr(profile, 'store', None)
    if store and getattr(store, 'name', None):
        return store.name
    # Fallback to username if available via account
    account = getattr(profile, 'account', None)
    if account and getattr(account, 'username', None):
        return account.username
    return None

def _get_profile_picture(profile):
    if not profile:
        return None
    # Try trainer
    trainer = getattr(profile, 'trainer', None)
    if trainer and getattr(trainer, 'profile_picture', None):
        return trainer.profile_picture
    # Try trainee
    trainee = getattr(profile, 'trainee', None)
    if trainee and getattr(trainee, 'profile_picture', None):
        return trainee.profile_picture
    # Try gym
    gym = getattr(profile, 'gym', None)
    if gym and getattr(gym, 'profile_picture', None):
        return gym.profile_picture
    # Try store
    store = getattr(profile, 'store', None)
    if store and getattr(store, 'profile_picture', None):
        return store.profile_picture
    return None
        
