# main/admin.py

from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone

from .models import Client, Project, Task, Invoice, Payment, Expense, Note, ProjectFile

# --- REPORTLAB IMPORTS ---
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
# -------------------------------------------------------------


# =================================================================
# INLINE DEFINITIONS
# =================================================================

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('title', 'status', 'due_date')
    ordering = ('-due_date',)


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    fields = ('amount', 'status', 'issue_date', 'due_date')
    readonly_fields = ('status',)
    show_change_link = True


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 1
    fields = ('title', 'category', 'amount', 'date')


class NoteInline(admin.StackedInline):
    model = Note
    extra = 1
    fields = ('content',)


class ProjectFileInline(admin.TabularInline):
    model = ProjectFile
    extra = 0
    fields = ('file', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0
    fields = ('title', 'status', 'start_date', 'due_date')
    show_change_link = True


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ('date', 'amount', 'method', 'reference')
    readonly_fields = ('amount',)


# =================================================================
# CLIENT ADMIN
# =================================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company', 'project_count', 'total_invoiced', 'date_added')
    search_fields = ('name', 'email', 'company')
    inlines = [ProjectInline]

    def project_count(self, obj):
        return obj.projects.count()
    project_count.short_description = 'Projects'

    def total_invoiced(self, obj):
        total = Invoice.objects.filter(project__client=obj).aggregate(total=Sum('amount'))['total']
        return f'${total:,.2f}' if total else '$0.00'
    total_invoiced.short_description = 'Total Invoiced'


# =================================================================
# PROJECT ADMIN
# =================================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'start_date', 'due_date', 'status', 'budget')
    list_filter = ('status', 'client')
    search_fields = ('title', 'client__name')
    inlines = [TaskInline, InvoiceInline, ExpenseInline, NoteInline, ProjectFileInline]

    fieldsets = (
        ('Project Details', {
            'fields': ('client', 'title', 'description', 'budget', 'status'),
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date'),
        }),
    )


# =================================================================
# TASK ADMIN
# =================================================================

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'due_date', 'is_overdue', 'completed_at')
    list_filter = ('status', 'project')
    search_fields = ('title', 'project__title')
    list_editable = ('status', 'due_date')

    def is_overdue(self, obj):
        if obj.status != 'Done' and obj.due_date and obj.due_date < timezone.localdate():
            return True
        return False
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'


# =================================================================
# INVOICE ADMIN + PDF EXPORT
# =================================================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'amount', 'status', 'issue_date', 'due_date', 'print_invoice_link')
    list_filter = ('status', 'project')
    search_fields = ('project__title', 'id')
    inlines = [PaymentInline]

    def export_as_pdf(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one invoice to print.", level='error')
            return

        invoice = queryset.first()

        response = HttpResponse(content_type='application/pdf')
        filename = f'invoice_{invoice.id}_{invoice.project.title.replace(" ", "_")}.pdf'
        response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        header_data = [
            [
                Paragraph("<b>Your Company Name</b><br/>123 Business Lane<br/>contact@yourcompany.com", styles['Normal']),
                Paragraph(f"<b>INVOICE</b><br/># {invoice.id}<br/>Issue Date: {invoice.issue_date}<br/>Due Date: {invoice.due_date}", styles['Normal']),
            ]
        ]

        header_table = Table(header_data, colWidths=[3.5 * 72, 3.5 * 72])
        header_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ]))
        story.append(header_table)

        client_data = [
            [
                Paragraph("<b>BILLED TO:</b>", styles['Heading5']),
                Paragraph("<b>PROJECT DETAILS:</b>", styles['Heading5']),
            ],
            [
                Paragraph(f"<b>{invoice.project.client.name}</b><br/>{invoice.project.client.company or 'Individual'}<br/>{invoice.project.client.email}", styles['Normal']),
                Paragraph(f"<b>Project:</b> {invoice.project.title}<br/><b>Status:</b> {invoice.status}", styles['Normal']),
            ]
        ]

        client_table = Table(client_data, colWidths=[3.5 * 72, 3.5 * 72])
        client_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Gainsboro),
        ]))
        story.append(client_table)

        item_data = [
            ['DESCRIPTION', 'QTY', 'UNIT PRICE', 'AMOUNT'],
            [
                Paragraph(invoice.project.description or "Project service fee.", styles['Normal']),
                '1',
                f"${invoice.amount}",
                f"${invoice.amount}"
            ]
        ]
        item_data.append(['', '', 'TOTAL:', f"${invoice.amount}"])

        item_table = Table(item_data, colWidths=[4 * 72, 0.7 * 72, 1.3 * 72, 1 * 72])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.royalblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ]))
        story.append(item_table)

        story.append(Paragraph(f"<b>Notes:</b> {invoice.notes or 'Thank you for your business!'}", styles['Normal']))

        doc.build(story)
        return response

    export_as_pdf.short_description = "Print Selected Invoice as PDF (ReportLab)"
    actions = ['export_as_pdf']

    def print_invoice_link(self, obj):
        return f'<a href="?action=export_as_pdf&amp;select_across=1&amp;_selected_action={obj.id}">📄 Print</a>'
    print_invoice_link.allow_tags = True
    print_invoice_link.short_description = 'Actions'


# =================================================================
# PAYMENT ADMIN
# =================================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'date', 'method', 'reference')
    list_filter = ('method', 'invoice__project__client')
    search_fields = ('invoice__project__title', 'reference', 'invoice__id')
    date_hierarchy = 'date'


# =================================================================
# EXPENSE ADMIN
# =================================================================

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_link', 'category', 'amount', 'date')
    list_filter = ('category', 'project')
    search_fields = ('title', 'description')
    date_hierarchy = 'date'

    def project_link(self, obj):
        if obj.project:
            return f'<a href="/admin/{obj._meta.app_label}/project/{obj.project.pk}/">{obj.project.title}</a>'
        return 'N/A'
    project_link.allow_tags = True
    project_link.short_description = 'Project'


# =================================================================
# NOTE ADMIN
# =================================================================

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('project', 'content_snippet', 'created_at')
    search_fields = ('project__title', 'content')
    date_hierarchy = 'created_at'

    def content_snippet(self, obj):
        return f"{obj.content[:50]}..." if len(obj.content) > 50 else obj.content
    content_snippet.short_description = 'Note Snippet'


# =================================================================
# PROJECT FILE ADMIN
# =================================================================

@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('project', 'description', 'file_link', 'uploaded_at')
    list_filter = ('project',)
    date_hierarchy = 'uploaded_at'

    def file_link(self, obj):
        if obj.file:
            return f'<a href="{obj.file.url}" target="_blank">Download File</a>'
        return 'No file'
    file_link.allow_tags = True
    file_link.short_description = 'File'


# =================================================================
# 💥 OVERRIDE DJANGO ADMIN HOMEPAGE (Dashboard)
# =================================================================

from django.contrib.admin import AdminSite

def custom_admin_index(self, request, extra_context=None):

    total_revenue = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_projects = Project.objects.count()
    total_invoices = Invoice.objects.count()

    monthly = (
        Payment.objects
        .values("date__month")
        .annotate(total=Sum("amount"))
        .order_by("date__month")
    )

    extra_context = extra_context or {}
    extra_context["total_revenue"] = total_revenue
    extra_context["total_projects"] = total_projects
    extra_context["total_invoices"] = total_invoices
    extra_context["monthly_revenue"] = [
        {"month": row["date__month"], "total": row["total"]} for row in monthly
    ]

    return super(AdminSite, self).index(request, extra_context)

admin.site.index = custom_admin_index.__get__(admin.site, AdminSite)
