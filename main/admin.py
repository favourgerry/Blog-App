# main/admin.py

from django.contrib import admin
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.db.models import Sum # Used for Client admin
from .models import Client, Project, Task, Invoice, Payment, Expense, Note, ProjectFile


# =================================================================
# INLINE DEFINITIONS (Connecting related models)
# =================================================================

class TaskInline(admin.TabularInline):
    """Shows tasks under the parent project."""
    model = Task
    extra = 1 # Show 1 empty form by default
    fields = ('title', 'status', 'due_date')
    ordering = ('-due_date',)


class InvoiceInline(admin.TabularInline):
    """Shows invoices under the parent project."""
    model = Invoice
    extra = 0 # No empty forms by default
    fields = ('amount', 'status', 'issue_date', 'due_date')
    readonly_fields = ('status',)
    show_change_link = True # Allows quick navigation to the invoice detail page


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
    readonly_fields = ('amount',) # Amount should be driven by the payment entry

# =================================================================
# ADMIN REGISTRATIONS
# =================================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company', 'project_count', 'total_invoiced', 'date_added')
    search_fields = ('name', 'email', 'company')
    inlines = [ProjectInline] # Link projects directly to the client
    
    # Custom display methods
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
    list_editable = ('status', 'due_date') # Allow quick changes from the list view

    def is_overdue(self, obj):
        from django.utils import timezone
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
    inlines = [PaymentInline] # Show payments under the invoice
    
    # -----------------------------
    # CUSTOM ADMIN ACTION: PDF PRINTING
    # -----------------------------
    def export_as_pdf(self, request, queryset):
        # Enforce selecting only one invoice for printing
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one invoice to print.", level='error')
            return

        invoice = queryset.first()
        
        # 1. Render the HTML content using the professional template
        html_content = render_to_string('main/invoice_pdf.html', {'invoice': invoice})

        # 2. Convert HTML to PDF using WeasyPrint
        # Use a base_url argument if you had static assets (logos)
        pdf_file = HTML(string=html_content).write_pdf()

        # 3. Create the HTTP response for download
        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f'invoice_{invoice.id}_{invoice.project.title.replace(" ", "_")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

    export_as_pdf.short_description = "Print Selected Invoice as PDF"
    actions = ['export_as_pdf'] # Register the action

    # -----------------------------
    # CUSTOM DISPLAY LINK (for Change List page)
    # -----------------------------
    def print_invoice_link(self, obj):
        # Create a link that points to the admin action for a specific object
        return f'<a href="?action=export_as_pdf&amp;select_across=1&amp;_selected_action={obj.id}" title="Download PDF">📄 Print</a>'
    
    print_invoice_link.allow_tags = True
    print_invoice_link.short_description = 'Actions'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'date', 'method', 'reference')
    list_filter = ('method', 'invoice__project__client') # Filter by client too
    search_fields = ('invoice__project__title', 'reference', 'invoice__id')
    date_hierarchy = 'date'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_link', 'category', 'amount', 'date')
    list_filter = ('category', 'project')
    search_fields = ('title', 'description')
    date_hierarchy = 'date'
    
    def project_link(self, obj):
        # Displays the project title and links to the project change page
        if obj.project:
            return f'<a href="/admin/main/project/{obj.project.pk}/">{obj.project.title}</a>'
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
        # Provides a clickable link to the file itself
        if obj.file:
            return f'<a href="{obj.file.url}" target="_blank">Download File</a>'
        return 'No file'
    file_link.allow_tags = True
    file_link.short_description = 'File'
