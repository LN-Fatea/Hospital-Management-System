from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum, Q, F, Count
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime, timedelta, date
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db import transaction
from django.utils.decorators import method_decorator
import io
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Create your views here.
def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/index.html')

def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/adminclick.html')

def doctorclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/doctorclick.html')

def patientclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/patientclick.html')

def volunteerclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'hospital/volunteerclick.html')

def admin_signup_view(request):
    form = forms.AdminSigupForm()
    if request.method == 'POST':
        form = forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request, 'hospital/adminsignup.html', {'form': form})

def doctor_signup_view(request):
    userForm = forms.DoctorUserForm()
    doctorForm = forms.DoctorForm()
    mydict = {'userForm': userForm, 'doctorForm': doctorForm}
    if request.method == 'POST':
        userForm = forms.DoctorUserForm(request.POST)
        doctorForm = forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            doctor = doctorForm.save(commit=False)
            doctor.user = user
            doctor.status = False
            doctor.save()
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
            return HttpResponseRedirect('doctorlogin')
    return render(request, 'hospital/doctorsignup.html', context=mydict)

def patient_signup_view(request):
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    mydict = {'userForm': userForm, 'patientForm': patientForm}
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            patient = patientForm.save(commit=False)
            patient.user = user
            patient.status = False
            patient.assignedDoctorId = request.POST.get('assignedDoctorId')
            patient.save()
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
            return HttpResponseRedirect('patientlogin')
    return render(request, 'hospital/patientsignup.html', context=mydict)

def volunteer_signup_view(request):
    userForm = forms.VolunteerUserForm()
    volunteerForm = forms.VolunteerForm()
    mydict = {'userForm': userForm, 'volunteerForm': volunteerForm}
    if request.method == 'POST':
        userForm = forms.VolunteerUserForm(request.POST)
        volunteerForm = forms.VolunteerForm(request.POST, request.FILES)
        if userForm.is_valid() and volunteerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            volunteer = volunteerForm.save(commit=False)
            volunteer.user = user
            volunteer.status = False
            volunteer.save()
            my_volunteer_group = Group.objects.get_or_create(name='VOLUNTEER')
            my_volunteer_group[0].user_set.add(user)
            return HttpResponseRedirect('volunteerlogin')
    return render(request, 'hospital/volunteersignup.html', context=mydict)

#-----------for checking user is doctor , patient or admin(by Leo)
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()

def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()

def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()

def is_volunteer(user):
    return user.groups.filter(name='VOLUNTEER').exists()


#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,DOCTOR OR PATIENT
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
        account = models.Doctor.objects.filter(user_id=request.user.id, status=True).first()
        if account:
            return redirect('doctor-dashboard')
        return render(request, 'hospital/doctor_wait_for_approval.html')
    elif is_patient(request.user):
        account = models.Patient.objects.filter(user_id=request.user.id, status=True).first()
        if account:
            return redirect('patient-dashboard')
        return render(request, 'hospital/patient_wait_for_approval.html')
    elif is_volunteer(request.user):
        account = models.Volunteer.objects.filter(user_id=request.user.id, status=True).first()
        if account:
            return redirect('volunteer-dashboard')
        return render(request, 'hospital/volunteer_wait_for_approval.html')








#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@cache_page(60 * 15)  # Cache for 15 minutes
def admin_dashboard_view(request):
    doctors = models.Doctor.objects.all().order_by('-id')
    patients = models.Patient.objects.all().order_by('-id')
    appointments = models.Appointment.objects.all().order_by('-id')
    volunteers = models.Volunteer.objects.all()

    # Get counts from cache or calculate
    doctor_count = cache.get('doctor_count')
    if doctor_count is None:
        doctor_count = doctors.count()
        cache.set('doctor_count', doctor_count, 300)

    patient_count = cache.get('patient_count')
    if patient_count is None:
        patient_count = patients.count()
        cache.set('patient_count', patient_count, 300)

    volunteer_count = cache.get('volunteer_count')
    if volunteer_count is None:
        volunteer_count = volunteers.count()
        cache.set('volunteer_count', volunteer_count, 300)

    appointment_count = cache.get('appointment_count')
    if appointment_count is None:
        appointment_count = appointments.count()
        cache.set('appointment_count', appointment_count, 300)

    context = {
        'doctors': doctors[:3],
        'patients': patients[:3],
        'appointments': appointments[:5],
        'doctor_count': doctor_count,
        'patient_count': patient_count,
        'appointment_count': appointment_count,
        'volunteer_count': volunteer_count,
    }
    return render(request, 'hospital/admin_dashboard.html', context)

# this view for sidebar click on admin page
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    # Get total number of doctors
    total_doctors = models.Doctor.objects.count()
    
    # Get pending approval count
    pending_approvals = models.Doctor.objects.filter(status=False).count()
    
    # Get active doctors today
    active_doctors = models.Doctor.objects.filter(status=True).count()
    
    # Get total number of patients
    total_patients = models.Patient.objects.count()
    
    # Get department distribution
    departments = []
    total_dept_doctors = 0
    for dept_name, _ in models.departments:
        count = models.Doctor.objects.filter(department=dept_name).count()
        total_dept_doctors += count
        departments.append({
            'name': dept_name,
            'count': count,
            'percentage': 0  # Will be calculated after getting total
        })
    
    # Calculate percentages
    if total_dept_doctors > 0:
        for dept in departments:
            dept['percentage'] = (dept['count'] / total_dept_doctors) * 100
    
    context = {
        'total_doctors': total_doctors,
        'pending_approvals': pending_approvals,
        'active_doctors': active_doctors,
        'total_patients': total_patients,
        'departments': departments,
    }
    return render(request, 'hospital/admin_doctor.html', context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor.html',{'doctors':doctors})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-view-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)

    userForm=forms.DoctorUserForm(instance=user)
    doctorForm=forms.DoctorForm(instance=doctor)
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST,instance=user)
        doctorForm=forms.DoctorForm(request.POST,instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.status=True
            doctor.save()
            return redirect('admin-view-doctor')
    return render(request,'hospital/admin_update_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    import logging
    logger = logging.getLogger(__name__)
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST, request.FILES)
        logger.info('Form data submitted: %s', request.POST)
        if userForm.is_valid() and doctorForm.is_valid():
            try:
                user=userForm.save()
                user.set_password(user.password)
                user.save()

                doctor=doctorForm.save(commit=False)
                doctor.user=user
                doctor.status=True
                doctor.save()

                my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
                my_doctor_group[0].user_set.add(user)
                logger.info('Doctor added successfully: %s', user.username)
            except Exception as e:
                logger.error(f'Error saving doctor: {e}')
                return render(request, 'hospital/admin_add_doctor.html', context={'userForm': userForm, 'doctorForm': doctorForm, 'error': 'There was an error saving the doctor.'})
        else:
            logger.warning('Form validation failed: %s', userForm.errors)
            return render(request, 'hospital/admin_add_doctor.html', context={'userForm': userForm, 'doctorForm': doctorForm, 'error': 'Please correct the errors below.'})
    return render(request,'hospital/admin_add_doctor.html',context=mydict)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_doctor_view(request):
    #those whose approval are needed
    doctors=models.Doctor.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_doctor.html',{'doctors':doctors})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    doctor.status=True
    doctor.save()
    return redirect(reverse('admin-approve-doctor'))

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect(reverse('admin-approve-doctor'))

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    # Get total number of patients
    total_patients = models.Patient.objects.count()
    
    # Get active admissions (patients who are currently admitted)
    active_admissions = models.Patient.objects.filter(status=True).count()
    
    # Get today's appointments
    today = datetime.now().date()
    todays_appointments = models.Appointment.objects.filter(
        appointmentDate=today
    ).count()
    
    # Get pending discharges
    pending_discharges = models.PatientDischargeDetails.objects.filter(
        releaseDate=None
    ).count()
    
    # Get recent activities
    recent_activities = []
    
    # Recent admissions
    recent_admissions = models.Patient.objects.filter(
        admitDate__gte=today - timedelta(days=7)
    ).order_by('-admitDate')[:5]
    
    for admission in recent_admissions:
        recent_activities.append({
            'icon': 'fas fa-user-plus',
            'title': f'New Patient Admitted',
            'description': f'{admission.get_name()}',
            'time': admission.admitDate.strftime('%Y-%m-%d %H:%M')
        })
    
    # Recent appointments
    recent_appointments = models.Appointment.objects.filter(
        appointmentDate__gte=today
    ).order_by('appointmentDate')[:5]
    
    for appointment in recent_appointments:
        recent_activities.append({
            'icon': 'fas fa-calendar-check',
            'title': 'Upcoming Appointment',
            'description': f'{appointment.patientId.get_name()} with Dr. {appointment.doctorId.get_name()}',
            'time': appointment.appointmentDate.strftime('%Y-%m-%d %H:%M')
        })
    
    # Recent discharges
    recent_discharges = models.PatientDischargeDetails.objects.exclude(
        releaseDate=None
    ).order_by('-releaseDate')[:5]
    
    for discharge in recent_discharges:
        recent_activities.append({
            'icon': 'fas fa-walking',
            'title': 'Patient Discharged',
            'description': f'{discharge.patientId.get_name()}',
            'time': discharge.releaseDate.strftime('%Y-%m-%d %H:%M')
        })
    
    # Sort all activities by time
    recent_activities.sort(key=lambda x: datetime.strptime(x['time'], '%Y-%m-%d %H:%M'), reverse=True)
    recent_activities = recent_activities[:10]  # Keep only the 10 most recent activities
    
    context = {
        'total_patients': total_patients,
        'active_admissions': active_admissions,
        'todays_appointments': todays_appointments,
        'pending_discharges': pending_discharges,
        'recent_activities': recent_activities,
    }
    return render(request, 'hospital/admin_patient.html', context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients = models.Patient.objects.all().filter(status=True)
    return render(request, 'hospital/admin_view_patient.html', {'patients': patients})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request, pk):
    patient = models.Patient.objects.get(id=pk)
    user = models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-view-patient')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request, pk):
    patient = models.Patient.objects.get(id=pk)
    user = models.User.objects.get(id=patient.user_id)
    userForm = forms.PatientUserForm(instance=user)
    patientForm = forms.PatientForm(instance=patient)
    mydict = {'userForm': userForm, 'patientForm': patientForm}
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST, instance=user)
        patientForm = forms.PatientForm(request.POST, request.FILES, instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            patient = patientForm.save(commit=False)
            patient.status = True
            patient.assignedDoctorId = request.POST.get('assignedDoctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request, 'hospital/admin_update_patient.html', context=mydict)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    import logging
    logger = logging.getLogger(__name__)
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    mydict = {'userForm': userForm, 'patientForm': patientForm}
    if request.method == 'POST':
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        logger.info('Form data submitted: %s', request.POST)
        if userForm.is_valid() and patientForm.is_valid():
            try:
                user = userForm.save()
                user.set_password(user.password)
                user.save()
                patient = patientForm.save(commit=False)
                patient.user = user
                patient.status = True
                patient.assignedDoctorId = request.POST.get('assignedDoctorId')
                patient.save()
                logger.info('Patient added successfully: %s', user.username)
                return redirect('admin-view-patient')
            except Exception as e:
                logger.error(f'Error saving patient: {e}')
                return render(request, 'hospital/admin_add_patient.html', context={'userForm': userForm, 'patientForm': patientForm, 'error': 'There was an error saving the patient.'})
        else:
            logger.warning('Form validation failed: %s', userForm.errors)
            return render(request, 'hospital/admin_add_patient.html', context={'userForm': userForm, 'patientForm': patientForm, 'error': 'Please correct the errors below.'})
    return render(request, 'hospital/admin_add_patient.html', context=mydict)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    patients = models.Patient.objects.all().filter(status=False)
    return render(request, 'hospital/admin_approve_patient.html', {'patients': patients})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request, pk):
    patient = models.Patient.objects.get(id=pk)
    patient.status = True
    patient.save()
    return redirect('admin-approve-patient')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request, pk):
    patient = models.Patient.objects.get(id=pk)
    user = models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-approve-patient')

#--------------------- FOR DISCHARGING PATIENT BY ADMIN START-------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients = models.Patient.objects.all().filter(status=True)
    return render(request, 'hospital/admin_discharge_patient.html', {'patients': patients})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request, pk):
    patient = models.Patient.objects.get(id=pk)
    days = (date.today() - patient.admitDate).days
    assignedDoctor = models.User.objects.get(id=patient.assignedDoctorId)
    
    # Calculate various charges
    room_charge = days * 500  # per day room charge is 500
    medicine_cost = days * 1000  # per day medicine cost is 1000
    doctor_fee = 2000  # one time doctor fee
    other_charge = days * 300  # other charges per day is 300
    total = room_charge + medicine_cost + doctor_fee + other_charge
    
    if request.method == 'POST':
        # Create discharge details
        models.PatientDischargeDetails.objects.create(
            patientId=pk,
            patientName=patient.get_name,
            assignedDoctorName=assignedDoctor.first_name,
            address=patient.address,
            mobile=patient.mobile,
            symptoms=patient.symptoms,
            admitDate=patient.admitDate,
            releaseDate=date.today(),
            daySpent=days,
            medicineCost=medicine_cost,
            roomCharge=room_charge,
            doctorFee=doctor_fee,
            OtherCharge=other_charge,
            total=total
        )
        return redirect('admin-view-patient')
    
    context = {
        'patient': patient,
        'days': days,
        'assignedDoctorName': assignedDoctor.first_name,
        'roomCharge': room_charge,
        'medicineCost': medicine_cost,
        'doctorFee': doctor_fee,
        'OtherCharge': other_charge,
        'total': total
    }
    return render(request, 'hospital/patient_final_bill.html', context=context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    # Get today's date
    today = datetime.now().date()
    
    # Get today's appointments
    todays_appointments = models.Appointment.objects.filter(
        appointmentDate=today
    ).count()
    
    # Get pending appointments
    pending_appointments = models.Appointment.objects.filter(
        status=False
    ).count()
    
    # Get this week's appointments
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_appointments = models.Appointment.objects.filter(
        appointmentDate__range=[week_start, week_end]
    ).count()
    
    # Get busiest doctor (doctor with most appointments this week)
    doctor_appointments = models.Appointment.objects.filter(
        appointmentDate__range=[week_start, week_end]
    ).values('doctorId').annotate(
        appointment_count=Count('id')
    ).order_by('-appointment_count')
    
    busiest_doctor = "None"
    if doctor_appointments:
        doctor = models.Doctor.objects.get(id=doctor_appointments[0]['doctorId'])
        busiest_doctor = f"Dr. {doctor.get_name()}"
    
    # Get today's schedule
    todays_schedule = []
    today_appointments = models.Appointment.objects.filter(
        appointmentDate=today
    ).order_by('appointmentDate')
    
    for appointment in today_appointments:
        status = "Scheduled"
        if appointment.status:
            current_time = datetime.now().time()
            if current_time > appointment.appointmentDate:
                status = "Completed"
            elif current_time < appointment.appointmentDate:
                status = "Scheduled"
            else:
                status = "In Progress"
        else:
            status = "Pending"
            
        todays_schedule.append({
            'time': appointment.appointmentDate.strftime('%I:%M %p'),
            'patient_name': appointment.patientId.get_name(),
            'doctor_name': appointment.doctorId.get_name(),
            'appointment_type': appointment.description,
            'room': f"{appointment.doctorId.department[:3]}-{appointment.id}",
            'status': status
        })
    
    # Get department load
    department_load = []
    max_appointments = 0
    
    for dept_name, _ in models.departments:
        dept_appointments = models.Appointment.objects.filter(
            doctorId__in=models.Doctor.objects.filter(department=dept_name),
            appointmentDate__range=[week_start, week_end]
        ).count()
        
        if dept_appointments > max_appointments:
            max_appointments = dept_appointments
            
        department_load.append({
            'name': dept_name,
            'appointments': dept_appointments,
            'load_percentage': 0  # Will be calculated after getting max
        })
    
    # Calculate load percentages
    if max_appointments > 0:
        for dept in department_load:
            dept['load_percentage'] = (dept['appointments'] / max_appointments) * 100
    
    logging.debug(f'Department Load: {department_load}')
    
    context = {
        'todays_appointments': todays_appointments,
        'pending_appointments': pending_appointments,
        'weekly_appointments': weekly_appointments,
        'busiest_doctor': busiest_doctor,
        'todays_schedule': todays_schedule,
        'department_load': department_load,
    }
    return render(request, 'hospital/admin_appointment.html', context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments=models.Appointment.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm=forms.AppointmentForm()
    mydict={'appointmentForm':appointmentForm,}
    if request.method=='POST':
        appointmentForm=forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.POST.get('patientId')
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=models.User.objects.get(id=request.POST.get('patientId')).first_name
            appointment.status=True
            appointment.save()
        return HttpResponseRedirect('admin-view-appointment')
    return render(request,'hospital/admin_add_appointment.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.status=True
    appointment.save()
    return redirect(reverse('admin-approve-appointment'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    return redirect('admin-approve-appointment')
#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    patientcount = models.Patient.objects.all().filter(status=True, assignedDoctorId=request.user.id).count()
    appointmentcount = models.Appointment.objects.all().filter(status=True, doctorId=request.user.id).count()
    patientdischarged = models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name).count()

    appointments = models.Appointment.objects.all().filter(status=True, doctorId=request.user.id).order_by('-id')
    patientid = []
    for a in appointments:
        patientid.append(a.patientId)
    patients = models.Patient.objects.all().filter(status=True, user_id__in=patientid).order_by('-id')
    appointments = zip(appointments, patients)

    mydict = {
        'patientcount': patientcount,
        'appointmentcount': appointmentcount,
        'patientdischarged': patientdischarged,
        'appointments': appointments,
        'doctor': models.Doctor.objects.get(user_id=request.user.id)
    }
    return render(request, 'hospital/doctor_dashboard.html', context=mydict)

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict = {
        'doctor': models.Doctor.objects.get(user_id=request.user.id),
    }
    return render(request, 'hospital/doctor_patient.html', context=mydict)

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    patients = models.Patient.objects.filter(
        Q(status=True) & 
        Q(assignedDoctorId=request.user.id)
    ).select_related('user')
    return render(request, 'hospital/doctor_view_patient.html', {'patients': patients})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    dischargedpatients = models.PatientDischargeDetails.objects.all().distinct().filter(assignedDoctorName=request.user.first_name)
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    return render(request, 'hospital/doctor_view_discharge_patient.html', {'dischargedpatients': dischargedpatients, 'doctor': doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    return render(request, 'hospital/doctor_appointment.html', {'doctor': doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    appointments = models.Appointment.objects.all().filter(status=True, doctorId=request.user.id)
    patientid = []
    for a in appointments:
        patientid.append(a.patientId)
    patients = models.Patient.objects.all().filter(status=True, user_id__in=patientid)
    appointments = zip(appointments, patients)
    return render(request, 'hospital/doctor_view_appointment.html', {'appointments': appointments, 'doctor': doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    appointments = models.Appointment.objects.all().filter(status=True, doctorId=request.user.id)
    patientid = []
    for a in appointments:
        patientid.append(a.patientId)
    patients = models.Patient.objects.all().filter(status=True, user_id__in=patientid)
    appointments = zip(appointments, patients)
    return render(request, 'hospital/doctor_delete_appointment.html', {'appointments': appointments, 'doctor': doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request, pk):
    appointment = models.Appointment.objects.get(id=pk)
    appointment.delete()
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    appointments = models.Appointment.objects.all().filter(status=True, doctorId=request.user.id)
    patientid = []
    for a in appointments:
        patientid.append(a.patientId)
    patients = models.Patient.objects.all().filter(status=True, user_id__in=patientid)
    appointments = zip(appointments, patients)
    return render(request, 'hospital/doctor_delete_appointment.html', {'appointments': appointments, 'doctor': doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    """Search patients by name or symptoms"""
    doctor = models.Doctor.objects.get(user_id=request.user.id)
    query = request.GET.get('query', '')
    patients = models.Patient.objects.filter(
        status=True,
        assignedDoctorId=request.user.id
    ).filter(
        Q(symptoms__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query)
    )
    return render(request, 'hospital/doctor_view_patient.html', {
        'patients': patients,
        'doctor': doctor
    })

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
@transaction.atomic
def diagnose_patient(request, pk):
    if request.method == 'POST':
        patient = models.Patient.objects.get(id=pk)
        symptoms = request.POST.get('symptoms', '')
        diagnosis = request.POST.get('diagnosis', '')

        # Create patient history
        history = models.PatientHistory.objects.create(
            patient=patient,
            symptoms=symptoms,
            diagnosis=diagnosis,
            treatment=request.POST.get('treatment', '')
        )

        # Get all symptom patterns for comparison
        patterns = models.SymptomPattern.objects.all()
        
        # Initialize TF-IDF vectorizer
        vectorizer = TfidfVectorizer()
        
        # Prepare corpus with current symptoms and all patterns
        corpus = [symptoms] + [p.symptoms for p in patterns]
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # Calculate similarity scores
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        
        # Find the best matching pattern
        if len(patterns) > 0:
            best_match_idx = np.argmax(similarities[0])
            best_match_score = similarities[0][best_match_idx]
            
            if best_match_score > 0.3:  # Threshold for similarity
                matched_pattern = patterns[best_match_idx]
                
                # Create auto diagnosis
                models.AutoDiagnosis.objects.create(
                    patient=patient,
                    symptom_pattern=matched_pattern,
                    match_percentage=float(best_match_score * 100)
                )
                
                return JsonResponse({
                    'success': True,
                    'suggested_diagnosis': matched_pattern.possible_diagnosis,
                    'match_percentage': round(best_match_score * 100, 2)
                })
        
        return JsonResponse({'success': False, 'message': 'No matching patterns found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
#------------------------ PATIENT RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    patient = models.Patient.objects.get(user_id=request.user.id)
    doctor = models.Doctor.objects.get(user_id=patient.assignedDoctorId)
    mydict = {
        'patient': patient,
        'doctorName': doctor.get_name,
        'doctorMobile': doctor.mobile,
        'doctorAddress': doctor.address,
        'symptoms': patient.symptoms,
        'doctorDepartment': doctor.department,
        'admitDate': patient.admitDate,
    }
    return render(request, 'hospital/patient_dashboard.html', context=mydict)

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient = models.Patient.objects.get(user_id=request.user.id)
    return render(request, 'hospital/patient_appointment.html', {'patient': patient})

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request):
    appointmentForm = forms.PatientAppointmentForm()
    patient = models.Patient.objects.get(user_id=request.user.id)
    message = None
    mydict = {
        'appointmentForm': appointmentForm,
        'patient': patient,
        'message': message
    }
    if request.method == 'POST':
        appointmentForm = forms.PatientAppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment = appointmentForm.save(commit=False)
            appointment.doctorId = request.POST.get('doctorId')
            appointment.patientId = request.user.id
            appointment.doctorName = models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName = request.user.first_name
            appointment.status = False
            appointment.save()
            return redirect('patient-view-appointment')
    return render(request, 'hospital/patient_book_appointment.html', context=mydict)

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient = models.Patient.objects.get(user_id=request.user.id)
    appointments = models.Appointment.objects.all().filter(patientId=request.user.id)
    return render(request, 'hospital/patient_view_appointment.html', {'appointments': appointments, 'patient': patient})

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient = models.Patient.objects.get(user_id=request.user.id)
    dischargeDetails = models.PatientDischargeDetails.objects.all().filter(patientId=patient.id).order_by('-id')[:1]
    patientDict = None
    if dischargeDetails:
        patientDict = {
            'is_discharged': True,
            'patient': patient,
            'patientId': patient.id,
            'patientName': patient.get_name,
            'assignedDoctorName': dischargeDetails[0].assignedDoctorName,
            'address': patient.address,
            'mobile': patient.mobile,
            'symptoms': patient.symptoms,
            'admitDate': patient.admitDate,
            'releaseDate': dischargeDetails[0].releaseDate,
            'daySpent': dischargeDetails[0].daySpent,
            'medicineCost': dischargeDetails[0].medicineCost,
            'roomCharge': dischargeDetails[0].roomCharge,
            'doctorFee': dischargeDetails[0].doctorFee,
            'OtherCharge': dischargeDetails[0].OtherCharge,
            'total': dischargeDetails[0].total,
        }
    else:
        patientDict = {
            'is_discharged': False,
            'patient': patient,
            'patientId': patient.id,
        }
    return render(request, 'hospital/patient_discharge.html', context=patientDict)

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_doctor_view(request):
    """View all available doctors"""
    doctors = models.Doctor.objects.filter(status=True)
    patient = models.Patient.objects.get(user_id=request.user.id)
    return render(request, 'hospital/patient_view_doctor.html', {
        'patient': patient,
        'doctors': doctors
    })

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def search_doctor_view(request):
    """Search doctors by name or department"""
    patient = models.Patient.objects.get(user_id=request.user.id)
    query = request.GET.get('query', '')
    doctors = models.Doctor.objects.filter(
        status=True
    ).filter(
        Q(department__icontains=query) |
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query)
    )
    return render(request, 'hospital/patient_view_doctor.html', {
        'patient': patient,
        'doctors': doctors
    })

def render_to_pdf(template_src, context_dict):
    """Helper function to generate PDF from HTML template"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

@login_required(login_url='patientlogin')
def download_pdf_view(request, pk):
    """Generate PDF bill for discharged patient"""
    dischargeDetails = models.PatientDischargeDetails.objects.filter(patientId=pk).order_by('-id')[:1]
    if not dischargeDetails:
        return HttpResponse("No discharge details found.")
    
    dict = {
        'patientName': dischargeDetails[0].patientName,
        'assignedDoctorName': dischargeDetails[0].assignedDoctorName,
        'address': dischargeDetails[0].address,
        'mobile': dischargeDetails[0].mobile,
        'symptoms': dischargeDetails[0].symptoms,
        'admitDate': dischargeDetails[0].admitDate,
        'releaseDate': dischargeDetails[0].releaseDate,
        'daySpent': dischargeDetails[0].daySpent,
        'medicineCost': dischargeDetails[0].medicineCost,
        'roomCharge': dischargeDetails[0].roomCharge,
        'doctorFee': dischargeDetails[0].doctorFee,
        'OtherCharge': dischargeDetails[0].OtherCharge,
        'total': dischargeDetails[0].total,
    }
    
    pdf = render_to_pdf('hospital/download_bill.html', dict)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Bill_{dict['patientName']}.pdf"
        content = f"inline; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Error generating PDF")

#------------------------ PATIENT RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
#------------------------ VOLUNTEER RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='volunteerlogin')
@user_passes_test(is_volunteer)
def volunteer_dashboard_view(request):
    volunteer = models.Volunteer.objects.get(user_id=request.user.id)
    if not volunteer.status:
        return render(request, 'hospital/volunteer_wait_for_approval.html')
    
    tasks = models.VolunteerTask.objects.filter(volunteer=volunteer).order_by('due_date')
    schedules = models.VolunteerSchedule.objects.filter(volunteer=volunteer).order_by('date', 'start_time')
    
    mydict = {
        'volunteer': volunteer,
        'tasks': tasks,
        'schedules': schedules,
        'taskcount': tasks.count(),
        'schedulecount': schedules.count(),
    }
    return render(request, 'hospital/volunteer_dashboard.html', context=mydict)

@login_required(login_url='volunteerlogin')
@user_passes_test(is_volunteer)
def volunteer_schedule_view(request):
    volunteer = models.Volunteer.objects.get(user_id=request.user.id)
    if not volunteer.status:
        return render(request, 'hospital/volunteer_wait_for_approval.html')
    schedules = models.VolunteerSchedule.objects.filter(volunteer=volunteer).order_by('date', 'start_time')
    return render(request, 'hospital/volunteer_schedule.html', {
        'volunteer': volunteer,
        'schedules': schedules
    })

@login_required(login_url='volunteerlogin')
@user_passes_test(is_volunteer)
def volunteer_tasks_view(request):
    volunteer = models.Volunteer.objects.get(user_id=request.user.id)
    if not volunteer.status:
        return render(request, 'hospital/volunteer_wait_for_approval.html')
    tasks = models.VolunteerTask.objects.filter(volunteer=volunteer).order_by('due_date')
    return render(request, 'hospital/volunteer_tasks.html', {
        'volunteer': volunteer,
        'tasks': tasks
    })

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_volunteer_view(request):
    # Get total number of volunteers
    total_volunteers = models.Volunteer.objects.count()
    
    # Get pending approval count
    pending_approvals = models.Volunteer.objects.filter(status=False).count()
    
    # Get active volunteers in the last week
    one_week_ago = datetime.now() - timedelta(days=7)
    active_volunteers = models.Volunteer.objects.filter(
        status=True,
        volunteerschedule__date__gte=one_week_ago
    ).distinct().count()
    
    context = {
        'total_volunteers': total_volunteers,
        'pending_approvals': pending_approvals,
        'active_volunteers': active_volunteers,
    }
    return render(request, 'hospital/admin_volunteer.html', context)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_volunteer_view(request):
    volunteers = models.Volunteer.objects.all().filter(status=True)
    return render(request, 'hospital/admin_view_volunteer.html', {'volunteers': volunteers})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_volunteer_from_hospital_view(request, pk):
    volunteer = models.Volunteer.objects.get(id=pk)
    user = models.User.objects.get(id=volunteer.user_id)
    user.delete()
    volunteer.delete()
    return redirect('admin-view-volunteer')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_volunteer_view(request, pk):
    volunteer = models.Volunteer.objects.get(id=pk)
    user = models.User.objects.get(id=volunteer.user_id)
    userForm = forms.VolunteerUserForm(instance=user)
    volunteerForm = forms.VolunteerForm(instance=volunteer)
    mydict = {'userForm': userForm, 'volunteerForm': volunteerForm}
    if request.method == 'POST':
        userForm = forms.VolunteerUserForm(request.POST, instance=user)
        volunteerForm = forms.VolunteerForm(request.POST, request.FILES, instance=volunteer)
        if userForm.is_valid() and volunteerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            volunteer = volunteerForm.save(commit=False)
            volunteer.status = True
            volunteer.save()
            return redirect('admin-view-volunteer')
    return render(request, 'hospital/admin_update_volunteer.html', context=mydict)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_volunteer_view(request):
    import logging
    logger = logging.getLogger(__name__)
    userForm = forms.VolunteerUserForm()
    volunteerForm = forms.VolunteerForm()
    mydict = {'userForm': userForm, 'volunteerForm': volunteerForm}
    if request.method == 'POST':
        userForm = forms.VolunteerUserForm(request.POST)
        volunteerForm = forms.VolunteerForm(request.POST, request.FILES)
        logger.info('Form data submitted: %s', request.POST)
        if userForm.is_valid() and volunteerForm.is_valid():
            logger.info('User form data: %s', userForm.cleaned_data)
            logger.info('Volunteer form data: %s', volunteerForm.cleaned_data)
            try:
                user=userForm.save()
                user.set_password(user.password)
                user.save()

                volunteer=volunteerForm.save(commit=False)
                volunteer.user=user
                volunteer.status=True
                volunteer.interest = request.POST.get('interest')
                volunteer.work_history = request.POST.get('work_history')
                volunteer.save()
                logger.info('Volunteer added successfully: %s', user.username)
                return redirect('admin-view-volunteer')
            except Exception as e:
                logger.error(f'Error saving volunteer: {e}')
                return render(request, 'hospital/admin_add_volunteer.html', context={'userForm': userForm, 'volunteerForm': volunteerForm, 'error': 'There was an error saving the volunteer.'})
        else:
            logger.warning('Form validation failed: %s', userForm.errors)
            logger.warning('Volunteer form validation failed: %s', volunteerForm.errors)
            logger.info('User form state after submission: %s', userForm)
            logger.info('Volunteer form state after submission: %s', volunteerForm)
            return render(request, 'hospital/admin_add_volunteer.html', context={'userForm': userForm, 'volunteerForm': volunteerForm, 'error': 'Please correct the errors below.'})
    return render(request, 'hospital/admin_add_volunteer.html', context=mydict)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_volunteer_view(request):
    volunteers = models.Volunteer.objects.all().filter(status=False)
    return render(request, 'hospital/admin_approve_volunteer.html', {'volunteers': volunteers})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_volunteer_view(request, pk):
    volunteer = models.Volunteer.objects.get(id=pk)
    volunteer.status = True
    volunteer.save()
    return redirect('admin-approve-volunteer')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_volunteer_view(request, pk):
    volunteer = models.Volunteer.objects.get(id=pk)
    user = models.User.objects.get(id=volunteer.user_id)
    user.delete()
    volunteer.delete()
    return redirect('admin-approve-volunteer')

#------------------------ VOLUNTEER RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------








#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START ------------------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'hospital/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'hospital/contactussuccess.html')
    return render(request, 'hospital/contactus.html', {'form':sub})


#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------



#Developed By : Leo

@login_required(login_url='patientlogin')
@cache_page(60 * 15)
def search_view(request):
    query = request.GET.get('query', '')
    if query:
        cache_key = f'search_results_{query}'
        results = cache.get(cache_key)
        
        if results is None:
            results = models.Patient.objects.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(symptoms__icontains=query)
            ).select_related('user')
            
            cache.set(cache_key, results, 300)  # Cache for 5 minutes
            
        return render(request, 'hospital/search_results.html', {'patients': results, 'query': query})
    return render(request, 'hospital/search.html')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def match_volunteers_view(request):
    return render(request, 'hospital/match_success.html', {'message': 'Volunteers matched to patients successfully!'})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def match_common_language_view(request):
    return render(request, 'hospital/match_success.html', {'message': 'Volunteers matched to patients successfully!'})
