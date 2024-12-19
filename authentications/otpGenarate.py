import random
import string

def generate_otp(length=4):
    digits = string.digits
    return ''.join(random.choices(digits, k=length))