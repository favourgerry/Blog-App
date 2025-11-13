# main/admin.py

from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum
from .models import Client, Project, Task, Invoice, Payment, Expense, Note, ProjectFile
from django.utils import timezone # For Task overdue check

# --- REPORTLAB IMPORTS for PDF Generation ---
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
# ---------------------------------------------


# =================================================================
# INLINE DEFINITIONS (Connecting related models)
# =================================================================

class TaskInline(admin.TabularInline):
    """Shows tasks under the parent project."""
    model = Task
    extra = 1
    fields = ('title', 'status', 'due_date')
    ordering = ('-due_date',)


class InvoiceInline(admin.TabularInline):
    """Shows invoices under the parent project."""
    model = Invoice
    extra = 0
    fields = ('amount', 'status', 'issue_date', 'due_date')
    readonly_fields = ('status',)
    show_change_link = True


class ExpenseInline(admin.TabularInline):
    """Shows expenses under the parent project."""
    model = Expense
    extra = 1
    fields = ('title', 'category', 'amount', 'date')


class NoteInline(admin.StackedInline):
    """Shows notes using StackedInline for more room for content."""
    model = Note
    extra = 1
    fields = ('content',)


class ProjectFileInline(admin.TabularInline):
    """Shows files under the parent project."""
    model = ProjectFile
    extra = 0
    fields = ('file', 'description', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


class ProjectInline(admin.TabularInline):
    """Shows projects under the parent client."""
    model = Project
    extra = 0
    fields = ('title', 'status', 'start_date', 'due_date')
    show_change_link = True


class PaymentInline(admin.TabularInline):
    """Shows payments under the parent invoice."""
    model = Payment
    extra = 0
    fields = ('date', 'amount', 'method', 'reference')
    readonly_fields = ('amount',)


# =================================================================
# ADMIN REGISTRATIONS
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
        # Calculate the sum of all invoices for all projects linked to this client
        total = Invoice.objects.filter(project__client=obj).aggregate(total=Sum('amount'))['total']
        return f'${total:,.2f}' if total is not None else '$0.00'
    total_invoiced.short_description = 'Total Invoiced'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'start_date', 'due_date', 'status', 'budget')
    list_filter = ('status', 'client')
    search_fields = ('title', 'client__name')
    # Group all related items on the Project change page
    inlines = [TaskInline, InvoiceInline, ExpenseInline, NoteInline, ProjectFileInline]

    # Custom fieldsets for a clean layout
    fieldsets = (
        ('Project Details', {
            'fields': ('client', 'title', 'description', 'budget', 'status'),
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date'),
        }),
    )


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


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'amount', 'status', 'issue_date', 'due_date', 'print_invoice_link')
    list_filter = ('status', 'project')
    search_fields = ('project__title', 'id')
    inlines = [PaymentInline]

    # -----------------------------
    # CUSTOM ADMIN ACTION: PDF PRINTING using ReportLab
    # -----------------------------
    def export_as_pdf(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one invoice to print.", level='error')
            return

        invoice = queryset.first()

        # --- ReportLab Setup ---
        response = HttpResponse(content_type='application/pdf')
        filename = f'invoice_{invoice.id}_{invoice.project.title.replace(" ", "_")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [] # List to hold drawing elements

        # --- 1. Header (Company and Invoice Details) ---
        header_data = [
            [
                Paragraph("<b>Your Company Name</b><br/>123 Business Lane, City<br/>contact@yourcompany.com", styles['Normal']),
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

        # --- 2. Client Details ---
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
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
        ]))
        story.append(client_table)
        story.append(Paragraph("<br/><br/>", styles['Normal']))


        # --- 3. Items Table (The main service item) ---
        item_data = [
            ['DESCRIPTION', 'QTY', 'UNIT PRICE', 'AMOUNT'],
            [
                Paragraph(invoice.project.description or "Project service fee.", styles['Normal']),
                '1',
                f"${invoice.amount}",
                f"${invoice.amount}"
            ]
        ]

        # Add a placeholder for Total Row
        item_data.append(['', '', 'TOTAL:', f"${invoice.amount}"])

        item_table = Table(item_data, colWidths=[4 * 72, 0.7 * 72, 1.3 * 72, 1 * 72])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.royalblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),

            # Style for the TOTAL row
            ('BACKGROUND', (2, -1), (-1, -1), colors.yellow),
            ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
            ('LEFTPADDING', (0, -1), (0, -1), 200),
        ]))
        story.append(item_table)
        story.append(Paragraph("<br/><br/>", styles['Normal']))

        # --- 4. Notes and Footer ---
        story.append(Paragraph(f"<b>Notes:</b> {invoice.notes or 'Thank you for your business!'}", styles['Normal']))
        story.append(Paragraph("<br/>", styles['Normal']))
        story.append(Paragraph(f"**Current Status:** <font color='red'><b>{invoice.status}</b></font>", styles['Normal']))

        # Build the PDF
        doc.build(story)

        return response

    export_as_pdf.short_description = "Print Selected Invoice as PDF (ReportLab)"
    actions = ['export_as_pdf']

    # -----------------------------
    # CUSTOM DISPLAY LINK (for Change List page)
    # -----------------------------
    def print_invoice_link(self, obj):
        # Creates a clickable link for the Print action on the list view
        return f'<a href="?action=export_as_pdf&amp;select_across=1&amp;_selected_action={obj.id}" title="Download PDF">📄 Print</a>'

    print_invoice_link.allow_tags = True
    print_invoice_link.short_description = 'Actions'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'date', 'method', 'reference')
    list_filter = ('method', 'invoice__project__client')
    search_fields = ('invoice__project__title', 'reference', 'invoice__id')
    date_hierarchy = 'date'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_link', 'category', 'amount', 'date')
    list_filter = ('category', 'project')
    search_fields = ('title', 'description')
    date_hierarchy = 'date'

    def project_link(self, obj):
        if obj.project:
            # Assumes your admin URL for the Project model is /admin/main/project/
            return f'<a href="/admin/{obj._meta.app_label}/project/{obj.project.pk}/">{obj.project.title}</a>'
        return 'N/A'
    project_link.allow_tags = True
    project_link.short_description = 'Project'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('project', 'content_snippet', 'created_at')
    search_fields = ('project__title', 'content')
    date_hierarchy = 'created_at'

    def content_snippet(self, obj):
        return f"{obj.content[:50]}..." if len(obj.content) > 50 else obj.content
    content_snippet.short_description = 'Note Snippet'


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
