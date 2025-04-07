# Navigate to your project directory
cd path/to/your/project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# To deactivate when done
deactivate


#########################################
# Navigate to your project directory
cd path\to\your\project

# Create virtual environment
python -m venv venv

# Activate virtual environment (Command Prompt)
venv\Scripts\activate

# OR for PowerShell
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# To deactivate when done
deactivate

Set-ExecutionPolicy RemoteSigned -Scope CurrentUser