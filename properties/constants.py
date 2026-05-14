# Properties App Constants
# Central location for all hardcoded values and configuration constants

# Feature Enforcer Constants
GRACE_PERIOD_DAYS = 7  # Days after subscription expiry before falling back to free plan

# Cache Timeouts (in seconds)
BUILDINGS_CACHE_TIMEOUT = 300  # 5 minutes
UNITS_CACHE_TIMEOUT = 300  # 5 minutes
RENTERS_CACHE_TIMEOUT = 300  # 5 minutes

# File Upload Limits
MAX_UNIT_IMAGES = 10
MAX_UNIT_DOCUMENTS = 5

# Default Values
DEFAULT_COUNTRY = "India"
DEFAULT_CURRENCY = "INR"

# Status Choices (for reference)
PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('PAID', 'Paid'),
    ('FAILED', 'Failed'),
    ('CANCELLED', 'Cancelled'),
]

UNIT_STATUS_CHOICES = [
    ('VACANT', 'Vacant'),
    ('OCCUPIED', 'Occupied'),
]

# Validation Constants
MIN_RENT_AMOUNT = 0
MAX_RENT_AMOUNT = 1000000  # 10 lakhs

# Notification Constants
RENT_REMINDER_DAYS_BEFORE = 3
AGREEMENT_EXPIRY_REMINDER_DAYS = 30