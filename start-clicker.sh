#!/bin/bash

# Function to check if a package is installed
check_package() {
    dpkg -l "$1" &> /dev/null
    return $?
}

# Function to print colored output
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "\e[32m✓ $1\e[0m"  # Green checkmark
    else
        echo -e "\e[31m✗ $1\e[0m"  # Red X
        exit 1
    fi
}

echo "Checking system dependencies..."

# Check for required system packages
for pkg in python3-tk python3-dev; do
    if check_package "$pkg"; then
        print_status "$pkg is installed" 0
    else
        print_status "Error: $pkg is not installed. Run: sudo apt-get install $pkg" 1
    fi
done

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created" $?
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated" $?

# Check if requirements are installed
if ! pip freeze | grep -q "pyautogui"; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    print_status "Dependencies installed" $?
else
    print_status "Python dependencies already installed" 0
fi

# Check if images directory exists
if [ ! -d "images" ]; then
    echo "Creating images directory..."
    mkdir images
    print_status "Images directory created" $?
else
    print_status "Images directory exists" 0
fi

echo -e "\n✨ Setup complete! Starting basic clicker...\n"

# Run the basic clicker
if [ "$1" == "--calibrate" ]; then
    python3 basic_clicker.py --calibrate
else
    python3 basic_clicker.py
fi 