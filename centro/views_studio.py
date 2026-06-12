import requests
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

@csrf_exempt
@staff_member_required(login_url='/admin/login/')
def studio_proxy(request, path=''):
    req_path = request.path
    if req_path.startswith('/centro/studio/'):
        target_path = req_path[len('/centro/studio/'):]
        if not target_path.startswith('/'):
            target_path = '/' + target_path
    else:
        target_path = req_path

    url = f"http://127.0.0.1:3847{target_path}"
    if request.META.get('QUERY_STRING'):
        url += f"?{request.META['QUERY_STRING']}"

    # Forward headers
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'connection']}

    try:
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.body,
            cookies=request.COOKIES,
            stream=True
        )
    except requests.exceptions.ConnectionError:
        return HttpResponse(
            "El servidor del Content Studio (Node.js) no está respondiendo en el puerto 3847. "
            "Asegúrate de que el proceso del Studio se haya iniciado correctamente en background.",
            status=502
        )

    django_response = StreamingHttpResponse(
        response.iter_content(chunk_size=4096),
        status=response.status_code,
        content_type=response.headers.get('Content-Type')
    )

    for k, v in response.headers.items():
        if k.lower() not in ['content-type', 'content-length', 'transfer-encoding', 'connection']:
            django_response[k] = v

    return django_response
