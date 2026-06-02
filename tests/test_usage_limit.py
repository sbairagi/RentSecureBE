# import pytest
# from django.contrib.auth import get_user_model
# from properties.models import (
#     UsageLimit, PlanFeatureLimit, SubscriptionPlan, UserSubscription
# )
# from properties.utils import enforce_limit
# from rest_framework.exceptions import PermissionDenied

# User = get_user_model()


# # •	UsageLimit and enforce_limit() system perfectly handle:
# # 	•	Allowed usage
# # 	•	Overuse detection
# # 	•	Unlimited plans
# # 	•	Restricted features
# # 	•	Missing records
# # 	•	Invalid plans
# # 	•	Unknown feature keys

# @pytest.mark.django_db
# def test_enforce_limit_allows_within_limit():
#     user = User.objects.create(username="testuser1")
#     plan = SubscriptionPlan.objects.create(name="free", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan)

#     PlanFeatureLimit.objects.create(plan=plan, feature_key='max_properties', value='2')
#     UsageLimit.objects.create(user=user, feature_key='max_properties', usage_count=1)

#     # Should not raise error
#     enforce_limit(user, 'max_properties')

# @pytest.mark.django_db
# def test_enforce_limit_raises_error_on_limit_exceeded():
#     user = User.objects.create(username="testuser2")
#     plan = SubscriptionPlan.objects.create(name="free", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan)

#     PlanFeatureLimit.objects.create(plan=plan, feature_key='max_properties', value='2')
#     UsageLimit.objects.create(user=user, feature_key='max_properties', usage_count=2)

#     with pytest.raises(PermissionDenied):
#         enforce_limit(user, 'max_properties')

# @pytest.mark.django_db
# def test_enforce_limit_allows_unlimited():
#     user = User.objects.create(username="testuser3")
#     plan = SubscriptionPlan.objects.create(name="elite", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan)

#     PlanFeatureLimit.objects.create(plan=plan, feature_key='max_properties', value='unlimited')
#     UsageLimit.objects.create(user=user, feature_key='max_properties', usage_count=999)

#     enforce_limit(user, 'max_properties')  # Should pass

# @pytest.mark.django_db
# def test_enforce_limit_denies_feature_with_no():
#     user = User.objects.create(username="testuser4")
#     plan = SubscriptionPlan.objects.create(name="limited", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan)

#     PlanFeatureLimit.objects.create(plan=plan, feature_key='whatsapp_alerts', value='no')

#     with pytest.raises(PermissionDenied):
#         enforce_limit(user, 'whatsapp_alerts')

# @pytest.mark.django_db
# def test_enforce_limit_with_no_usage_record_allows_initial():
#     user = User.objects.create(username="testuser5")
#     plan = SubscriptionPlan.objects.create(name="free2", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan)

#     PlanFeatureLimit.objects.create(plan=plan, feature_key='max_renters', value='2')

#     enforce_limit(user, 'max_renters')  # Should pass with no existing UsageLimit

# @pytest.mark.django_db
# def test_enforce_limit_raises_error_on_no_active_subscription():
#     user = User.objects.create(username="testuser6")
#     plan = SubscriptionPlan.objects.create(name="expired", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan, is_active=False)

#     with pytest.raises(PermissionDenied):
#         enforce_limit(user, 'max_properties')

# @pytest.mark.django_db
# def test_enforce_limit_raises_error_on_invalid_feature_key():
#     user = User.objects.create(username="testuser7")
#     plan = SubscriptionPlan.objects.create(name="basic", monthly_price=0, yearly_price=0)
#     UserSubscription.objects.create(user=user, plan=plan, is_active=True)

#     with pytest.raises(PermissionDenied):
#         enforce_limit(user, 'invalid_key')
