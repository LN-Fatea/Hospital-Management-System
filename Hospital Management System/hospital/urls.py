from django.urls import path
from . import views

urlpatterns = [
    path('admin-add-doctor/', views.admin_add_doctor_view, name='admin-add-doctor'),
    path('admin-add-patient/', views.admin_add_patient_view, name='admin-add-patient'),
    path('admin-add-volunteer/', views.admin_add_volunteer_view, name='admin-add-volunteer'),
    path('admin-view-doctor/', views.admin_view_doctor_view, name='admin-view-doctor'),
    path('admin-view-patient/', views.admin_view_patient_view, name='admin-view-patient'),
    # Removed match-related URL patterns
]
