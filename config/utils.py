def get_base_template(request):
    if request.htmx and request.htmx.target != 'body':
        return "_partial.html"
    else:
        return "_base.html"

def get_htmx_oob_swap_response(content, target, push_URL=None):
    response = '<div hx-swap-oob="' + target + '" '
    
    if push_URL:
        response += 'hx-push-url="/' + push_URL + '"'
        
    response += '>' + content + '</div>'
    return response
