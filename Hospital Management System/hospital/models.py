from django.db import models
from django.contrib.auth.models import User



departments=[('Cardiologist','Cardiologist'),
('Dermatologists','Dermatologists'),
('Emergency Medicine Specialists','Emergency Medicine Specialists'),
('Allergists/Immunologists','Allergists/Immunologists'),
('Anesthesiologists','Anesthesiologists'),
('Colon and Rectal Surgeons','Colon and Rectal Surgeons')
]
class Doctor(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    # profile_pic= models.ImageField(upload_to='profile_pic/DoctorProfilePic/',null=True,blank=True)  # Removed profile picture
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    department= models.CharField(max_length=50,choices=departments,default='Cardiologist')
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return "{} ({})".format(self.user.first_name,self.department)



class Patient(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/PatientProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    symptoms = models.CharField(max_length=100,null=False)
    assignedDoctorId = models.PositiveIntegerField(null=True)
    admitDate=models.DateField(auto_now=True)
    status=models.BooleanField(default=False)
    language = models.CharField(max_length=50, blank=True, null=True)  # New field for language
    def get_name(self):
        return f'{self.user.first_name} {self.user.last_name}'
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return self.user.first_name+" ("+self.symptoms+")"


class Appointment(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    doctorId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40,null=True)
    doctorName=models.CharField(max_length=40,null=True)
    appointmentDate=models.DateField(auto_now=True)
    description=models.TextField(max_length=500)
    status=models.BooleanField(default=False)



class PatientDischargeDetails(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40)
    assignedDoctorName=models.CharField(max_length=40)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    symptoms = models.CharField(max_length=100,null=True)

    admitDate=models.DateField(null=False)
    releaseDate=models.DateField(null=False)
    daySpent=models.PositiveIntegerField(null=False)

    roomCharge=models.PositiveIntegerField(null=False)
    medicineCost=models.PositiveIntegerField(null=False)
    doctorFee=models.PositiveIntegerField(null=False)
    OtherCharge=models.PositiveIntegerField(null=False)
    total=models.PositiveIntegerField(null=False)


class Volunteer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/VolunteerProfilePic/', null=True, blank=True)
    address = models.TextField()
    mobile = models.CharField(max_length=15, blank=True, null=True)  
    department = models.CharField(max_length=50, choices=departments, default='Cardiologist')
    interest = models.TextField(blank=True, null=True)  
    work_history = models.TextField(blank=True, null=True)  
    language = models.CharField(max_length=50, blank=True, null=True)  # New field for language
    status = models.BooleanField(default=False)
    
    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name
        
    @property
    def get_id(self):
        return self.user.id
        
    def __str__(self):
        return "{} ({})".format(self.user.first_name, self.department)


class VolunteerSchedule(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    department = models.CharField(max_length=50, choices=departments)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')

    def __str__(self):
        return f"{self.volunteer.user.first_name} - {self.date} ({self.start_time} to {self.end_time})"


class VolunteerTask(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=50, choices=departments)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')

    def __str__(self):
        return f"{self.title} - {self.volunteer.user.first_name}"

class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    symptoms = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField()
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.patient.get_name} - {self.date}"

class SymptomPattern(models.Model):
    name = models.CharField(max_length=100)
    symptoms = models.TextField(help_text="Comma-separated list of symptoms")
    possible_diagnosis = models.TextField()
    recommended_tests = models.TextField(blank=True)
    severity_level = models.IntegerField(choices=[
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_symptoms_list(self):
        return [s.strip() for s in self.symptoms.split(',')]

    class Meta:
        ordering = ['-severity_level', 'name']

class AutoDiagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    symptom_pattern = models.ForeignKey(SymptomPattern, on_delete=models.SET_NULL, null=True)
    match_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by_doctor = models.BooleanField(default=False)
    doctor_notes = models.TextField(blank=True)
    confirmed_diagnosis = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.get_name} - {self.symptom_pattern.name} ({self.match_percentage}%)"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Auto Diagnoses"

class VolunteerPatientMatch(models.Model):
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    match_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)  # Optional notes about the match

#Developed By : Leo