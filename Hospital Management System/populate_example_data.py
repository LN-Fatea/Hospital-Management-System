import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospitalmanagement.settings')
django.setup()

from hospital.models import Doctor, Patient, Volunteer
from django.contrib.auth.models import User

# Example Doctors
example_doctors = [
    {'first_name': 'John', 'last_name': 'Doe', 'username': 'johndoe1', 'password': 'password123', 'department': 'Cardiology', 'mobile': '1234567890', 'address': '123 Main St', 'profile_pic': 'path/to/profile_pic1.jpg'},
    {'first_name': 'Jane', 'last_name': 'Smith', 'username': 'janesmith1', 'password': 'password123', 'department': 'Neurology', 'mobile': '0987654321', 'address': '456 Elm St', 'profile_pic': 'path/to/profile_pic2.jpg'},
    {'first_name': 'Alice', 'last_name': 'Johnson', 'username': 'alicejohnson1', 'password': 'password123', 'department': 'Pediatrics', 'mobile': '2345678901', 'address': '789 Oak St', 'profile_pic': 'path/to/profile_pic3.jpg'},
    {'first_name': 'Bob', 'last_name': 'Brown', 'username': 'bobbrown1', 'password': 'password123', 'department': 'Orthopedics', 'mobile': '3456789012', 'address': '321 Pine St', 'profile_pic': 'path/to/profile_pic4.jpg'},
    {'first_name': 'Charlie', 'last_name': 'Davis', 'username': 'charliedavis1', 'password': 'password123', 'department': 'Dermatology', 'mobile': '4567890123', 'address': '654 Maple St', 'profile_pic': 'path/to/profile_pic5.jpg'},
]

for doc in example_doctors:
    username = doc['username']
    while User.objects.filter(username=username).exists():
        username += '1'
    user = User.objects.create_user(username=username, first_name=doc['first_name'], last_name=doc['last_name'], password=doc['password'])
    doctor = Doctor(user=user, department=doc['department'], mobile=doc['mobile'], address=doc['address'], profile_pic=doc['profile_pic'], status=True)
    doctor.save()

# Example Patients
example_patients = [
    {'first_name': 'Emily', 'last_name': 'Clark', 'assigned_doctor': 'johndoe1', 'symptoms': 'Fever', 'mobile': '5678901234', 'address': '111 Birch St'},
    {'first_name': 'David', 'last_name': 'Wilson', 'assigned_doctor': 'janesmith1', 'symptoms': 'Cough', 'mobile': '3213214321', 'address': '222 Cedar St'},
    {'first_name': 'Sophia', 'last_name': 'Garcia', 'assigned_doctor': 'alicejohnson1', 'symptoms': 'Headache', 'mobile': '4564564567', 'address': '333 Spruce St'},
    {'first_name': 'Michael', 'last_name': 'Martinez', 'assigned_doctor': 'bobbrown1', 'symptoms': 'Nausea', 'mobile': '7897897890', 'address': '444 Fir St'},
    {'first_name': 'Isabella', 'last_name': 'Hernandez', 'assigned_doctor': 'charliedavis1', 'symptoms': 'Fatigue', 'mobile': '6546546543', 'address': '555 Willow St'},
]

for pat in example_patients:
    username = pat['first_name'].lower() + pat['last_name'].lower()
    while User.objects.filter(username=username).exists():
        username += '1'
    user = User.objects.create_user(username=username, first_name=pat['first_name'], last_name=pat['last_name'], password='password123')
    doctor = User.objects.get(username=pat['assigned_doctor'])
    patient = Patient(user=user, assignedDoctorId=doctor.id, symptoms=pat['symptoms'], mobile=pat['mobile'], address=pat['address'], status=True)
    patient.save()

# Example Volunteers
example_volunteers = [
    {'first_name': 'Liam', 'last_name': 'Taylor', 'department': 'Administration', 'mobile': '1231231234'},
    {'first_name': 'Olivia', 'last_name': 'Anderson', 'department': 'Patient Care', 'mobile': '3213214321'},
    {'first_name': 'Noah', 'last_name': 'Thomas', 'department': 'Logistics', 'mobile': '4564564567'},
    {'first_name': 'Emma', 'last_name': 'Jackson', 'department': 'Outreach', 'mobile': '7897897890'},
    {'first_name': 'Ava', 'last_name': 'White', 'department': 'Fundraising', 'mobile': '6546546543'},
]

for vol in example_volunteers:
    username = vol['first_name'].lower() + vol['last_name'].lower()
    while User.objects.filter(username=username).exists():
        username += '1'
    user = User.objects.create_user(username=username, first_name=vol['first_name'], last_name=vol['last_name'], password='password123')
    volunteer = Volunteer(user=user, department=vol['department'], mobile=vol['mobile'])
    volunteer.save()

print('Example data added successfully!')
