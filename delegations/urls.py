
from . import views
from django.urls import path
from delegations import views


urlpatterns = [
    path('org/<uuid:org_id>/delegations/', 
         views.DelegationListCreateView.as_view(), 
         name='delegation-list-create'),
    
    path('org/<uuid:org_id>/delegations/<uuid:pk>/', 
         views.DelegationDetailView.as_view(), 
         name='delegation-detail'),
    
    path('org/<uuid:org_id>/delegations/<uuid:pk>/revoke/', 
         views.DelegationRevokeView.as_view(), 
         name='delegation-revoke'),
    
    path('org/<uuid:org_id>/effective-role/', 
         views.EffectiveRoleView.as_view(), 
         name='effective-role'),
]