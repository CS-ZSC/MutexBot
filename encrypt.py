import sys
from utils import encrypt

if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: python run_encrypt.py ")
        sys.exit(1)

    encryption_key = encrypt()
    print(encryption_key)
