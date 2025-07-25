# Hospital Management

## HOW TO RUN THIS PROJECT
- Install Python(3.7.6) (Do not Forget to Add to Path after or while installing Python).
- If you have trouble installing Python Environment, check out tutorials online.
- Open Terminal and Execute Following Commands:
```
pip install django == 3.0.5
pip install django-widget-tweaks
pip install xhtml2pdf
```
- Download This Project Zip Folder and Extract it.
- Move to project folder in Terminal. Then run following Commands:
```
py manage.py makemigrations
py manage.py migrate
py manage.py runserver
```
- Enter following URL in Your Browser
```
http://127.0.0.1:8000/
```

## CHANGES REQUIRED FOR CONTACT US PAGE
- In settins.py file, You are able to give your email and password
```
EMAIL_HOST_USER = 'youremail@gmail.com'
EMAIL_HOST_PASSWORD = 'your email password'
EMAIL_RECEIVING_USER = 'youremail@gmail.com'
```
- Login to gmail through host email id in your browser and open following link and turn it on
```
https://myaccount.google.com/lesssecureapps
```
## Feedback
Any suggestion and feedback is welcome.
- [Visit my GitHub](https://github.com/LN-Fatea)
