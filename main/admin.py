from django.contrib import admin
from .models import Client, Project, Task, Invoice, Payment, Expense, Note, ProjectFile

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'company', 'date_added')
    search_fields = ('name', 'email', 'company')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'start_date', 'due_date', 'status', 'budget')
    list_filter = ('status', 'client')
    search_fields = ('title',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'due_date', 'completed_at')
    list_filter = ('status',)
    search_fields = ('title',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'amount', 'status', 'issue_date', 'due_date')
    list_filter = ('status',)
    search_fields = ('project__title',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'date', 'method', 'reference')
    list_filter = ('method',)
    search_fields = ('invoice__project__title', 'reference')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'date')
    list_filter = ('category',)
    search_fields = ('title',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('project', 'created_at')
    search_fields = ('project__title',)


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ('project', 'file', 'uploaded_at')
