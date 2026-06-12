import requests
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

@csrf_exempt
@staff_member_required(login_url='/admin/login/')
def studio_proxy(request, path=''):
    import traceback
    try:
        req_path = request.path
        target_path = req_path
        for prefix in ['/centro/studio/', '/cgm/']:
            if req_path.startswith(prefix):
                target_path = req_path[len(prefix):]
                break
        if req_path == '/centro/studio' or req_path == '/cgm':
            target_path = '/'
        if not target_path.startswith('/'):
            target_path = '/' + target_path

        url = f"http://127.0.0.1:3847{target_path}"
        if request.META.get('QUERY_STRING'):
            url += f"?{request.META['QUERY_STRING']}"

        # Forward headers cleanly, filtering out host, connection, empty values, and body-related headers for non-mutating requests
        headers = {}
        for k, v in request.headers.items():
            k_low = k.lower()
            if k_low in ['host', 'connection']:
                continue
            if not v or str(v).strip() == '':
                continue
            if request.method not in ['POST', 'PUT', 'PATCH'] and k_low in ['content-length', 'content-type']:
                continue
            headers[k] = v

        # Forward body only for mutating methods
        data = request.body if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] else None


        print(f"PROXY REQ: {request.method} {url}")
        print(f"PROXY HEADERS: {headers}")
        print(f"PROXY COOKIES: {request.COOKIES}")

        try:
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=data,
                cookies=request.COOKIES,
                stream=False
            )
            print(f"PROXY RESP STATUS: {response.status_code}")
            print(f"PROXY RESP HEADERS: {dict(response.headers)}")
        except requests.exceptions.ConnectionError:
            print("PROXY CONNECTION ERROR")
            return HttpResponse(
                "El servidor del Content Studio (Node.js) no está respondiendo en el puerto 3847. "
                "Asegúrate de que el proceso del Studio se haya iniciado correctamente en background.",
                status=502
            )

        django_response = HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )

        for k, v in response.headers.items():
            k_low = k.lower()
            if k_low not in [
                'content-type', 'content-length', 'content-encoding',
                'connection', 'keep-alive', 'proxy-authenticate',
                'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
                'upgrade'
            ]:
                django_response[k] = v

        return django_response
    except Exception as e:
        tb = traceback.format_exc()
        return HttpResponse(f"<pre>{tb}</pre>", status=500, content_type="text/html")


