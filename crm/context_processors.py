from .models import CompanyInfo

def company_info(request):
    return {'company_info': CompanyInfo.objects.first()}