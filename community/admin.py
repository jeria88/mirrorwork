from django.contrib import admin
from .models import Follow, SharedInsight, Reaction, Comment


@admin.register(SharedInsight)
class SharedInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'source_type', 'short_text', 'visibility', 'created_at']
    list_filter  = ['source_type', 'visibility']
    raw_id_fields = ['user', 'test_result', 'espejo_session', 'recipient', 'repost_of']

    def short_text(self, obj):
        return obj.display_text[:60] if obj.display_text else '—'
    short_text.short_description = 'Texto'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    raw_id_fields = ['follower', 'following']


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'insight']
    raw_id_fields = ['user', 'insight']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight', 'created_at']
    raw_id_fields = ['user', 'insight']
