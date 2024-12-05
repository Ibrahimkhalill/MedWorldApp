import random
import string

def generate_otp(length=6):
    digits = string.digits
    return ''.join(random.choices(digits, k=length))