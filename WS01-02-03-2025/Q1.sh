#!/bin/bash

# Predefined username and password : Usually stored in a DB
CORRECT_USER="admin"
CORRECT_PASS="password123"

# Prompt user for input
read -p "Enter username: " input_user
read -s -p "Enter password: " input_pass # -s tag for anonymous pass entry
echo  # Move to a new line after password input

# Check if the input matches the predefined credentials
if [[ "$input_user" == "$CORRECT_USER" && "$input_pass" == "$CORRECT_PASS" ]]; then
    echo "Access Granted."
else
    echo "Access Denied. Incorrect username or password."
fi
