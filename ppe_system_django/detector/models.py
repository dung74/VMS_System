from django.db import models
from django.utils import timezone

# Create your models here.

class ViolationLog(models.Model):

    ViolationType = [
        ("NO_CARD", "Khong deo the nhan vien"),
        ("NO_MASK", "Khong deo khau trang"),
    ]

    timestamp = models.DateTimeField(auto_now_add = True, verbose_name = "Thoi gian")
    violation_type = models.CharField(max_length = 20, choices = ViolationType, default = "NO_CARD")
    image_path = models.CharField(max_length = 255, null = True, blank = True, verbose_name = "Duong dan anh")



    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        local_timestamp = timezone.localtime(self.timestamp)
        return f"[{self.get_violation_type_display()}] luc {local_timestamp.strftime('%H:%M:%S %d/%m/%Y')}"
    

class SystemAccount(models.Model):
    username = models.CharField(max_length = 50, unique = True, verbose_name = "Ten dang nhap")
    password_hash = models.CharField(max_length = 255, verbose_name = "Mat khau (da ma hoa)")
    created_at = models.DateTimeField(auto_now_add = True)
    is_active = models.BooleanField(default = True)
    
    def __str__(self):
        return self.username
    
    

class VideoRecord(models.Model):
    timestamp = models.DateTimeField(verbose_name = "Thoi gian bat dau ghi hinh")
    video_path = models.CharField(max_length = 255, verbose_name = "Duong dan file video")

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Video luc {self.timestamp.strftime('%H-%M-%S_%d-%m-%Y')}"
    
    
