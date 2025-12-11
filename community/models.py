from django.db import models

# Create your models here.
class CommunityPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    attachment = models.URLField(max_length=500, blank=True, null=True)
    attachment_type = models.CharField(max_length=20, choices=[('image', 'Image'), ('video', 'Video'), ('document', 'Document'), ('other', 'Other')], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class CommunityComment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.post.title}"
    
class CommunityLike(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='likes')
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'profile')

    def __str__(self):
        return f"Like by {self.profile} on {self.post.title}"

class CommunityCommentLike(models.Model):
    comment = models.ForeignKey(CommunityComment, on_delete=models.CASCADE, related_name='likes')
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'profile')

    def __str__(self):
        return f"Like by {self.profile} on comment {self.comment_id}"
    

    