import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    width = 60
    print("\n" + "=" * width)
    print(f"{text:^{width}}")
    print("=" * width + "\n")

def print_section(text):
    print(f"\n{'─' * 60}")
    print(f"  {text}")
    print('─' * 60)

def print_success(text):
    print(f"\n✓ {text}")