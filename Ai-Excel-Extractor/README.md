# SCS Excel Processor

An AI-powered tool for processing industrial equipment descriptions. This application automatically extracts structured data from equipment descriptions in Excel files.

## System Requirements

### Windows
- Windows 10 or 11
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection

### Mac
- macOS Monterey (12) or later
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- Internet connection

## Installation Guide

### Windows Setup

1. **Install Docker Desktop**
   - Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
   - Run the installer
   - Follow the installation wizard
   - Restart your computer if prompted
   - Start Docker Desktop and wait for it to fully initialize (whale icon in taskbar becomes steady)

2. **Install Ollama**
   - Download [Ollama for Windows](https://ollama.ai/)
   - Run the installer
   - Follow the installation wizard
   - Open Command Prompt as Administrator
   - Run: `ollama serve`
   - Wait for Ollama to start

3. **Start the Application**
   - Extract the industrial-data-processor.zip to your desired location
   - Double-click `start.bat`
   - Wait for the application to initialize
   - The script will automatically:
     - Check if Docker is running
     - Check if Ollama is running
     - Install required AI model if needed
     - Start the application
   - Open your web browser and go to http://localhost:5000

### Mac Setup

1. **Install Docker Desktop**
   - Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
   - Open the downloaded .dmg file
   - Drag Docker to Applications folder
   - Start Docker Desktop from Applications
   - Wait for Docker to fully initialize (whale icon in menu bar becomes steady)

2. **Install Ollama**
   - Download [Ollama for Mac](https://ollama.ai/)
   - Open the downloaded .dmg file
   - Drag Ollama to Applications folder
   - Open Terminal
   - Run: `ollama serve`
   - Wait for Ollama to start

3. **Start the Application**
   - Extract the industrial-data-processor.zip to your desired location
   - Open Terminal
   - Navigate to the application folder:
     ```bash
     cd path/to/industrial-data-processor
     ```
   - Make the start script executable (first time only):
     ```bash
     chmod +x start.sh
     ```
   - Run the application:
     ```bash
     ./start.sh
     ```
   - Wait for the application to initialize
   - Open your web browser and go to http://localhost:5000

## Using the Application

1. **Prepare Your Excel File**
   - Must be in .xlsx format
   - Should contain columns for:
     - Part numbers
     - Equipment descriptions

2. **Process Files**
   - Click "Upload File" or drag and drop your Excel file
   - Select the appropriate sheet
   - Enter the starting cell for part numbers (e.g., A2)
   - Enter the starting cell for descriptions (e.g., B2)
   - Click "Process"
   - Wait for processing to complete
   - Download the processed Excel file

3. **Output Format**
   The processed Excel file will contain:
   - Original part numbers and descriptions
   - Extracted data in structured columns
   - Empty cells for fields not found in descriptions

## Stopping the Application

### Windows
1. Go to the Command Prompt window running the application
2. Press `Ctrl+C`
3. Type `Y` when prompted
4. Close the window

### Mac
1. Go to the Terminal window running the application
2. Press `Command+C`
3. Close the Terminal window

## Troubleshooting

### Common Issues

1. **"Docker is not running"**
   - Open Docker Desktop
   - Wait for it to fully initialize
   - Try starting the application again

2. **"Ollama is not running"**
   - Open new Terminal/Command Prompt
   - Run: `ollama serve`
   - Try starting the application again

3. **"Port 5000 already in use"**
   - Check for other applications using port 5000
   - Close those applications
   - Try starting again

4. **"Permission denied" (Mac only)**
   - Run: `chmod +x start.sh`
   - Try starting again

5. **Slow Processing**
   - Check internet connection
   - Ensure computer meets minimum requirements
   - Try processing smaller batches

### Still Having Issues?

1. Try these steps:
   - Restart Docker Desktop
   - Restart Ollama
   - Restart your computer
   - Start the application again

2. Check Logs:
   - Windows: Check the Command Prompt window
   - Mac: Check the Terminal window
   - Look for specific error messages

## Uninstallation

### Windows
1. Close the application
2. Delete the application folder
3. Optionally:
   - Uninstall Docker Desktop
   - Uninstall Ollama

### Mac
1. Close the application
2. Delete the application folder
3. Optionally:
   - Remove Docker Desktop from Applications
   - Remove Ollama from Applications


