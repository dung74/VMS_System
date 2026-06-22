from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('change_password/', views.change_password_view, name='change_password'),

    path('', views.dashboard, name='dashboard'),
    path('video_feed/', views.video_feed_view, name='video_feed'),
    path('history/', views.history_view, name='history'),
    path('api/latest_logs/', views.get_latest_logs_api, name='api_latest_logs'),
    path('api/toggle_detect/', views.toggle_detection_api, name='toggle_detect'),
    path('history/delete/', views.delete_log_view, name='delete_date_logs'),
    path('log/delete/<int:log_id>/', views.delete_single_log_view, name = 'delete_single_log'),

    path('history/videos/', views.video_history_view, name='video_history'),
    path('history/videos/delete-single/<int:video_id>/', views.delete_single_video_view, name='delete_single_video'),
    path('history/videos/delete-date/', views.delete_date_videos_view, name='delete_date_videos'),

  
    path('api/toggle-recording/', views.toggle_recording_api, name='toggle_recording'),

]