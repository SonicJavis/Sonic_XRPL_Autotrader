import sys

# Force UTF-8 on Windows to avoid charmap errors
def setup_encoding():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

setup_encoding()

print('✅ Fixture Health: HEALTHY') # This will now work with encoding fix
# Rest of your CLI logic here...