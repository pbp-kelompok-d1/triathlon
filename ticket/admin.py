from django.contrib import admin
from .models import Ticket
from datetime import date

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'ticket_number',
        'customer_name', 
        'place', 
        'ticket_quantity', 
        'total_price', 
        'booking_date',
        'status_badge',
        'created_at'
    ]
    list_filter = [
        'booking_date', 
        'created_at', 
        'place',
        'place__genre'
    ]
    search_fields = [
        'customer_name', 
        'place__name',
        'id'
    ]
    readonly_fields = [
        'total_price', 
        'created_at', 
        'updated_at',
        'status_display'
    ]
    date_hierarchy = 'booking_date'
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'user')
        }),
        ('Booking Details', {
            'fields': ('place', 'ticket_quantity', 'booking_date')
        }),
        ('Price Information', {
            'fields': ('total_price',)
        }),
        ('Status', {
            'fields': ('status_display',)
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Menampilkan status badge di admin"""
        from django.utils.html import format_html
        colors = {
            'past': '#6c757d',
            'today': '#28a745',
            'upcoming': '#007bff'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status_display
        )
    status_badge.short_description = 'Status'