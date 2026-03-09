
from django.urls import path
from applications.shop.views import sms_webhook, create_order, submit_reference

urlpatterns = [
   
    path('api/sms-webhook/', sms_webhook, name='sms_webhook'),
    path('control/create-order/', create_order, name='create_order'),          
    path('control/submit-reference/', submit_reference, name='submit_reference'),  
]
