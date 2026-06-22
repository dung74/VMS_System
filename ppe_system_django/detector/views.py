import shutil
import time
import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings
from detector.models import ViolationLog , SystemAccount, VideoRecord
from detector.services.ai_engine import AIEdgeScanner
from django.utils import timezone
from detector.services import ai_engine
import os
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import math
from django.contrib.auth.hashers import make_password, check_password
from detector.decorators import customer_login_required

# Create your views here.
@customer_login_required
def dashboard(request):
    logs = ViolationLog.objects.all()[:10]
    context = {
        'logs': logs,
        'is_detecting': ai_engine.GLOBAL_IS_DETECTING,
        'is_recording': ai_engine.GLOBAL_IS_RECORDING
    }
    return render(request, 'dashboard.html', context)


def _video_stream_generator():
    while True:

        frame_bytes = ai_engine.GLOBAL_FRAME_BYTES

        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            
        time.sleep(0.03)

@customer_login_required         
def video_feed_view(request):
    return StreamingHttpResponse(_video_stream_generator(), 
                                 content_type='multipart/x-mixed-replace; boundary=frame')

@customer_login_required
def get_latest_logs_api(request):
    logs = ViolationLog.objects.all()[ :10]
    data = []

    for log in logs:
        timestamp_local = timezone.localtime(log.timestamp)
        image_url = f"/media/{log.image_path}" if log.image_path else "#"
        data.append({
            'type': log.get_violation_type_display(),
            'timestamp': timestamp_local.strftime('%H:%M:%S %d/%m/%Y'),
            'image_url': image_url,
        })
    return JsonResponse({'logs': data})

@customer_login_required
def toggle_detection_api(request):
    ai_engine.GLOBAL_IS_DETECTING = not ai_engine.GLOBAL_IS_DETECTING
    return JsonResponse({
        'status': 'success',
        'is_detecting': ai_engine.GLOBAL_IS_DETECTING
    })

@customer_login_required
def history_view(request):  
    available_dates = ViolationLog.objects.dates('timestamp', 'day', order = 'DESC')
    # selected_date_str = request.GET.get('date')
    if 'date' in request.GET:
        selected_date_str = request.GET.get('date')
        current_page = request.GET.get('page', 1)

        request.session['last_history_date'] = selected_date_str
        request.session['last_history_page'] = current_page
        request.session.modified = True
    else:
        selected_date_str = request.session.get('last_history_date')
        current_page = request.session.get('last_history_page', 1)




    page_logs = []
    paginator_data = {}

    if selected_date_str:
        logs_list = ViolationLog.objects.filter(timestamp__date=selected_date_str).order_by('-timestamp')
        
        total_items = logs_list.count()
        items_per_page = 10
        total_pages = math.ceil(total_items/items_per_page) if total_items > 0 else 1

        try: 
            current_page = int(request.GET.get('page', 1))
        except ValueError:
            current_page = 1

        if current_page <1:
            current_page = 1
        elif current_page > total_pages:
            current_page = total_pages

        offset = (current_page  - 1) * items_per_page
        limit = offset + items_per_page

        page_logs = logs_list[offset:limit]
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)
        page_range = range(start_page, end_page + 1)

        paginator_data = {
            'current_page': current_page,
            'total_pages': total_pages,
            'has_previous': current_page > 1,
            'has_next': current_page < total_pages,
            'previous_page_number': current_page - 1,
            'next_page_number': current_page + 1,
            'page_range': page_range,
            'start_index': offset + 1,
        }

    context ={
            'available_dates': available_dates,
            'selected_date': selected_date_str,
            'page_logs': page_logs,
            'paginator': paginator_data
    }
        
    return render(request, 'history.html', context)


@customer_login_required
def delete_log_view(request):
    if request.method == 'POST':
        target_date = request.POST.get('target_date')

        if target_date:
            ViolationLog.objects.filter(timestamp__date = target_date).delete()

            folder_path = os.path.join(settings.MEDIA_ROOT, 'violations', target_date)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"==> He thong da xoa thu muc va anh vi pham cua ngay: {target_date}")

    return redirect('history')

@customer_login_required
def delete_single_log_view(request, log_id):
    if request.method == 'POST':
        try:
            log = ViolationLog.objects.get(id=log_id)
            if log.image_path:
                file_path = os.path.join(settings.MEDIA_ROOT, log.image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            log.delete()

        except ViolationLog.DoesNotExist:
            pass
    
    previous_url = request.META.get('HTTP_REFERER', 'history')
    return redirect(previous_url)



def register_view(request):
    error_msg = None
    success_msg = None
    if request.method == 'POST':
        user_input = request.POST.get('username')
        pass_input = request.POST.get('password')

        if SystemAccount.objects.filter(username = user_input).exists():
            error_msg = "Ten dang nhap da ton tai"
        else:
            new_account = SystemAccount(
                username = user_input,
                password_hash = make_password(pass_input)
            )
            new_account.save()

            success_msg = "dang ky thanh cong, vui long dang nhap"
        
    return render(request, 'register.html', {'error_msg': error_msg, 'success_msg': success_msg})


def login_view(request):
    error_msg = None
    if request.method == 'POST':
        user_input = request.POST.get('username')
        pass_input = request.POST.get('password')

        try:
            account = SystemAccount.objects.get(username=user_input)

            if check_password(pass_input, account.password_hash):
                if account.is_active:
                    request.session['account_id'] = account.id
                    request.session['account_name'] = account.username
                    print(f"==> Tai khoan {account.username} da dang nhap thanh cong")
                    # request.session.save()
                    return redirect('dashboard')
                    
                else:
                    error_msg = "Tai khoan cua ban da bi khoa"
            else:
                error_msg = "Mat khau khong chinh xac"

        except SystemAccount.DoesNotExist:
            error_msg = "Tai khoan khong ton tai"

    return render(request, 'login.html', {'error_msg': error_msg})

                
def custom_logout_view(request):
    request.session.flush()
    return redirect('login')


def change_password_view(request):
    error_msg = None
    success_msg = None

    if request.method == 'POST':
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')

        account_id = request.session.get('account_id')
        account = SystemAccount.objects.get(id = account_id)

        if not check_password(old_pass, account.password_hash):
            error_msg = "Mat khau cu khong chinh xac"

        elif new_pass != confirm_pass:
            error_msg = "Mat khau moi va xac nhan mau khau khong khop"
        else:
            account.password_hash = make_password(new_pass)
            account.save()
            success_msg = "Mat khau da duoc cap nhat thanh cong, vui long dang nhap lai"

    return render(request, 'change_password.html', {
        'error_msg': error_msg,
        'success_msg': success_msg
    })

@customer_login_required
def video_history_view(request):
    available_dates = VideoRecord.objects.dates('timestamp', 'day', order = 'DESC')

    if 'date' in request.GET:
        selected_date_str = request.GET.get('date')
        current_page = request.GET.get('page', 1)
        request.session['last_video_date'] = selected_date_str
        request.session['last_video_page'] = current_page
        request.session.modified = True

    else:
        selected_date_str = request.session.get('last_video_date', '')
        current_page = request.session.get('last_video_page', 1)

    page_videos = []
    paginator_data = {}

    if selected_date_str:
        videos_list = VideoRecord.objects.filter(timestamp__date=selected_date_str).order_by('-timestamp')

        total_items = videos_list.count()
        items_per_page = 3
        total_pages = math.ceil(total_items/items_per_page) if total_items > 0 else 1

        try:
            current_page = int(request.GET.get('page', 1))
        except ValueError:
            current_page = 1
        
        if current_page < 1:
            current_page = 1
        elif current_page > total_pages:
            current_page = total_pages

        offset = (current_page - 1) * items_per_page
        limit = offset + items_per_page

        page_videos = videos_list[offset:limit]

        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)
        page_range = range(start_page, end_page +1)

        paginator_data = {
            'current_page': current_page, 
            'total_pages': total_pages, 
            'has_previous': current_page > 1,
            'has_next': current_page < total_pages,
            'previous_page_number': current_page -1,
            'next_page_number': current_page +1,
            'page_range': page_range,
            'start_index': offset + 1,

        }

    context = {
        'available_dates': available_dates,
        'selected_date': selected_date_str,
        'page_videos': page_videos,
        'paginator': paginator_data
    }
    return render(request, 'video_history.html', context)


@customer_login_required
def delete_date_videos_view(request):
    target_date_str = request.POST.get('target_date')
    if target_date_str:
        try:
            parse_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            VideoRecord.objects.filter(timestamp__date = parse_date).delete()

            folder_path = os.path.join(settings.MEDIA_ROOT, 'videos', target_date_str)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
        except ValueError:
            pass

    return redirect('video_history')

@customer_login_required
def delete_single_video_view(request, video_id):
    if request.method == 'POST':
        try:
            vid = VideoRecord.objects.get(id = video_id)
            if vid.video_path:
                file_path = os.path.join(settings.MEDIA_ROOT, vid.video_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                vid.delete()
        except VideoRecord.DoesNotExist:
            pass
        
    return redirect(request.META.get('HTTP_REFERER', 'video_history'))

@customer_login_required
def toggle_recording_api(request):
    """API ngầm để bật/tắt tính năng ghi hình"""
    ai_engine.GLOBAL_IS_RECORDING = not ai_engine.GLOBAL_IS_RECORDING
    return JsonResponse({
        'status': 'success',
        'is_recording': ai_engine.GLOBAL_IS_RECORDING
    })
    
