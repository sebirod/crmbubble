from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from crm.models import CompanyInfo  # Importa el modelo aquí

def generate_invoice_pdf(payment):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Obtén la información de la empresa
    company_info = CompanyInfo.objects.first()

    if company_info:
        # Dibuja el logo si existe
        if company_info.logo:
            p.drawImage(company_info.logo.path, inch, height - 2*inch, width=1.5*inch, height=1.5*inch)

        # Información de la empresa
        p.setFont("Helvetica-Bold", 16)
        p.drawString(3*inch, height - inch, company_info.name)
        p.setFont("Helvetica", 10)
        p.drawString(3*inch, height - 1.2*inch, company_info.fiscal_address)
        p.drawString(3*inch, height - 1.4*inch, f"Tel: {company_info.phone}")
        p.drawString(3*inch, height - 1.6*inch, f"Email: {company_info.email}")
        if company_info.website:  # Añadimos el sitio web si está disponible
            p.drawString(3*inch, height - 1.8*inch, f"Web: {company_info.website}")

    # Información de la factura
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 3*inch, f"Factura para: {payment.enrollment.student.user.get_full_name()}")
    p.setFont("Helvetica", 10)
    p.drawString(inch, height - 3.5*inch, f"Curso: {payment.enrollment.course.name}")
    p.drawString(inch, height - 3.7*inch, f"Fecha: {payment.date}")
    p.drawString(inch, height - 3.9*inch, f"Monto: {payment.amount}")
    p.drawString(inch, height - 4.1*inch, f"Método de pago: {payment.get_payment_method_display()}")

    p.showPage()
    p.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    return pdf