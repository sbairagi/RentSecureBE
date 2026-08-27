from rest_framework.throttling import UserRateThrottle


class LoginThrottle(UserRateThrottle):
    scope = "login"


class OTPThrottle(UserRateThrottle):
    scope = "otp_verify"


class RegisterThrottle(UserRateThrottle):
    scope = "register"


class ForgotPasswordThrottle(UserRateThrottle):
    scope = "forgot_password"


class SocialAuthThrottle(UserRateThrottle):
    scope = "social_auth"
