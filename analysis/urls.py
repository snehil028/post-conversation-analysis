from django.urls import path
from .views import ConversationUploadView, TriggerAnalysisView, AnalysesListView

urlpatterns = [
    path("upload/", ConversationUploadView.as_view(), name="conv-upload"),
    path("analyze/", TriggerAnalysisView.as_view(), name="conv-analyze"),
    path("analyses/", AnalysesListView.as_view(), name="analyses-list"),
]
