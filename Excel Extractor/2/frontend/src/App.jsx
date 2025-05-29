// Import necessary React hooks and libraries
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

function App() {
  // State for tracking current step in the workflow
  const [currentStep, setCurrentStep] = useState('upload')
  // State to store the selected Excel file
  const [file, setFile] = useState(null)
  // State to store names of sheets found in the Excel file
  const [sheetNames, setSheetNames] = useState([])
  // State to store the unique ID assigned to the uploaded file
  const [uploadId, setUploadId] = useState(null)
  // State to track if file processing is in progress
  const [isProcessing, setIsProcessing] = useState(false)
  // State to track current processing status ('extracting', 'processing', 'generating')
  const [processingStatus, setProcessingStatus] = useState('');
  // State to track progress of file processing
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  // State to track if we have any processed data available for download
  const [hasProcessedData, setHasProcessedData] = useState(false);
  // State to track if download preparation is in progress
  const [isPreparingDownload, setIsPreparingDownload] = useState(false);
  // State to store the path to the processed file on the server
  const [processedFilePath, setProcessedFilePath] = useState(null);


  // Handler for file drop functionality using react-dropzone
  const onDrop = useCallback(acceptedFiles => {
    const selectedFile = acceptedFiles[0]
    // Only accept .xlsx files
    if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
      setFile(selectedFile)
    } else {
      alert('Please select an Excel file (.xlsx)')
    }
  }, [])


  // Handler to stop processing and save current progress
  const handleStopAndSave = async () => {
    try {
      setIsPreparingDownload(true);
      console.log('Sending stop request...');
      
      // Send request to server to stop processing
      const response = await fetch('/api/stop', {
        method: 'POST',
      });
  
      console.log('Stop response status:', response.status);
      const data = await response.json();
      console.log('Stop response data:', data);
  
      if (data.success) {
        // Update UI states if stop was successful
        setIsProcessing(false);
        if (data.filePath) {
          setProcessedFilePath(data.filePath);
          setHasProcessedData(true);
          console.log('File path received:', data.filePath);
        } else {
          console.log('No file path in response, but processing stopped');
        }
        // Show success message regardless of file path
        alert('Processing stopped successfully.' + 
              (data.filePath ? ' You can now download the file.' : ' Please wait a moment before downloading.'));
      } else {
        throw new Error(data.error || 'Failed to stop processing');
      }
    } catch (error) {
      console.error('Stop processing error:', error);
      alert(`Failed to stop processing: ${error.message}`);
    } finally {
      // Reset loading state
      setIsPreparingDownload(false);
    }
  };

  // Handler to download the processed file
  const handleDownload = async () => {
    try {
      setIsPreparingDownload(true);
      
      // Implement retry logic for more reliable downloads
      let retries = 3;
      let response;
      
      while (retries > 0) {
        try {
          // Request the processed file from the server
          response = await fetch('/api/download', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filePath: processedFilePath }),
          });
  
          if (response.ok) {
            break;
          }
  
          // If response wasn't ok, wait before retrying
          retries--;
          if (retries > 0) {
            // before retrying, wait for 2 seconds
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        } catch (fetchError) {
          console.error('Fetch attempt failed:', fetchError);
          retries--;
          if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        }
      }
  
      if (!response || !response.ok) {
        throw new Error('Failed to download after multiple attempts');
      }
  
      // Create a download link for the file blob
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'processed_results.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Showing the success message when it's finished
      alert('File downloaded successfully!');
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download file. Please try again.');
    } finally {
      setIsPreparingDownload(false);
    }
  };


  // Set up Server-Sent Events for real-time progress updates
  const startProgressMonitoring = () => {
    const eventSource = new EventSource('/api/progress');
    
    // Update progress state when new events are received
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };

    return eventSource;
  };


  // Configure react-dropzone for file uploads
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: false
  })

  // Handler to upload the selected Excel file
  const handleUpload = async () => {
    if (!file) return

    // Create form data with the file for uploading
    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('Uploading file:', file)
      console.log('Sending request to /api/upload')

      // Send file to server
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      console.log('Response status:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Process server response
      const data = await response.json()
      console.log('Upload response:', data)
      
      if (data.error) {
        throw new Error(data.error)
      }

      // Update state with upload results and move to next step
      setUploadId(data.upload_id)
      setSheetNames(data.sheet_names)
      setCurrentStep('sheet')
      
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Failed to upload file. Please try again.')
    }
  }

  // Handler to process the uploaded Excel file with the selected options
  const handleProcess = async () => {
    try {
      // Set initial processing states
      setIsProcessing(true)
      setProgress({ current: 0, total: 0 })
      setProcessingStatus('extracting')
      
      // Start progress monitoring
      const eventSource = startProgressMonitoring();
      
      // Get configuration values from form inputs
      const sheetName = document.getElementById('sheetSelect').value
      const partCell = document.getElementById('partCell').value
      const descCell = document.getElementById('descCell').value
      const vendorCell = document.getElementById('vendorCell').value 

      // Validate input fields
      if (!sheetName || !partCell || !descCell || !vendorCell) {
        alert('Please fill in all fields')
        return
      }
  
      console.log('Starting process with:', { sheetName, partCell, descCell, uploadId });
  
      // Create form data with processing parameters
      const formData = new FormData()
      formData.append('upload_id', uploadId)
      formData.append('sheet_name', sheetName)
      formData.append('part_cell', partCell)
      formData.append('desc_cell', descCell)
      formData.append('vendor_cell', vendorCell)
  
      // Update UI to processing state
      setCurrentStep('processing')
      setProcessingStatus('processing')
  
      console.log('Sending process request...');
      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      })
  
      console.log('Process response status:', response.status);
  
      if (!response.ok) {
        const errorData = await response.text();
        console.error('Process error response:', errorData);
        throw new Error(`Processing failed: ${errorData}`);
      }
  
      // Close progress monitoring
      eventSource.close();
  
      setProcessingStatus('generating')
  
      // Handle the downloaded file blob
      const blob = await response.blob()
      console.log('Received blob:', blob);
  
      // Create a download link for the processed file
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'processed_results.xlsx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
  
      // Reset states and show completion message
      alert('Processing complete! Excel file downloaded.')
      setCurrentStep('upload')
      setFile(null)
      setUploadId(null)
      setSheetNames([])
      
    } catch (error) {
      console.error('Processing failed:', error)
      alert(`Failed to process file: ${error.message}`)
      setCurrentStep('sheet')
    } finally {
      // Reset processing states
      setIsProcessing(false)
      setProgress({ current: 0, total: 0 })
      setProcessingStatus('')
    }
  }

  return (
    <div className="min-h-screen bg-base-300 text-base-content">
      {/* Header - Application title bar */}
      <div className="navbar bg-base-200 shadow-lg">
        <div className="flex-1 px-4">
          <h1 className="text-2xl font-bold">SCS Excel Processor</h1>
        </div>
      </div>

      {/* Main Content - Container for the entire application */}
      <div className="container mx-auto px-4 py-8">
        {/* Progress Steps - Visual indicator of the current step in the workflow */}
        <div className="flex justify-center mb-8">
          <ul className="steps steps-horizontal">
            <li className={`step ${currentStep === 'upload' ? 'step-primary' : ''}`}>
              Upload File
            </li>
            <li className={`step ${currentStep === 'sheet' ? 'step-primary' : ''}`}>
              Configure
            </li>
            <li className={`step ${currentStep === 'processing' ? 'step-primary' : ''}`}>
              Process
            </li>
          </ul>
        </div>

        {/* Content Cards - Different cards shown based on the current step */}
        <div className="max-w-2xl mx-auto">
          {currentStep === 'upload' && (
            <div className="card bg-base-100 shadow-xl">
              <div className="card-body">
                {/* File drop area with visual feedback when dragging */}
                <div 
                  {...getRootProps()} 
                  className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-all duration-200
                    ${isDragActive ? 'border-primary bg-base-200' : 'border-base-content/20 hover:border-primary'}`}
                >
                  <input {...getInputProps()} />
                  <div className="flex flex-col items-center gap-4">
                    {/* Upload icon SVG */}
                    <svg 
                      className="w-16 h-16 text-base-content/50" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth="2" 
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    {/* Conditional rendering based on file selection */}
                    {file ? (
                      <div className="text-success">
                        <p className="font-semibold">{file.name}</p>
                        <p className="text-sm">File selected</p>
                      </div>
                    ) : (
                      <div>
                        <p className="font-semibold">
                          {isDragActive ? 'Drop the file here' : 'Drag & drop your Excel file here'}
                        </p>
                        <p className="text-sm text-base-content/60">
                          or click to select file
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                {/* Upload button - only shown when a file is selected */}
                {file && (
                  <button 
                    className="btn btn-primary mt-4"
                    onClick={handleUpload}
                  >
                    Upload File
                  </button>
                )}
              </div>
            </div>
          )}

          {currentStep === 'sheet' && (
            <div className="card bg-base-100 shadow-xl">
              <div className="card-body">
                <h2 className="card-title mb-4">Configure Sheet Processing</h2>
                <div className="space-y-6">
                  {/* Sheet selection dropdown populated from the Excel file */}
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Sheet Name</span>
                    </label>
                    <select 
                      id="sheetSelect"
                      className="select select-bordered w-full"
                    >
                      {sheetNames.map((sheet, index) => (
                        <option key={index} value={sheet}>{sheet}</option>
                      ))}
                    </select>
                  </div>

                  {/* Part number cell input - user specifies the starting cell */}
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Part Number Starting Cell</span>
                      <span className="label-text-alt text-base-content/60">e.g., A1</span>
                    </label>
                    <input 
                      id="partCell"
                      type="text" 
                      className="input input-bordered"
                      placeholder="Enter part number header cell"
                      required
                    />
                  </div>

                  {/* Description cell input - user specifies the starting cell */}
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Description Starting Cell</span>
                      <span className="label-text-alt text-base-content/60">e.g., B1</span>
                    </label>
                    <input 
                      id="descCell"
                      type="text" 
                      className="input input-bordered"
                      placeholder="Enter description header cell"
                      required
                    />
                  </div>

                  {/* Vendor cell input - user specifies the starting cell */}
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Vendor Starting Cell</span>
                      <span className="label-text-alt text-base-content/60">e.g., C1</span>
                    </label>
                    <input 
                      id="vendorCell"
                      type="text" 
                      className="input input-bordered"
                      placeholder="Enter vendor header cell"
                      required
                    />
                  </div>

                  {/* Process button - begins processing with selected configuration */}
                  <button 
                    className="btn btn-primary w-full"
                    onClick={handleProcess}
                    disabled={isProcessing}
                  >
                    {isProcessing ? (
                      <>
                        <span className="loading loading-spinner"></span>
                        Processing...
                      </>
                    ) : (
                      'Process Sheet'
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
          {currentStep === 'processing' && (
            <div className="card bg-base-100 shadow-xl">
              <div className="card-body items-center justify-center min-h-[400px]"> 
                <div className="w-full max-w-xs flex flex-col items-center justify-center">
                  {/* Loading spinner for visual feedback during processing */}
                  <div className="mb-8"> 
                    <div className="loading loading-spinner loading-lg text-primary"></div>
                  </div>
                  
                  {/* Processing title and description */}
                  <div className="mb-8 text-center">
                    <h2 className="card-title justify-center mb-2">Processing Your File</h2> 
                    <p className="text-base-content/60">This may take a few moments...</p>
                  </div>

                  {/* Progress Bar - Visual indicator of processing completion percentage */}
                  <div className="w-full bg-base-200 rounded-full h-2.5 mb-4">
                    <div 
                      className="bg-primary h-2.5 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` 
                      }}
                    ></div>
                  </div>

                  {/* Progress Text - Numerical representation of processing progress */}
                  <div className="text-sm text-base-content/70 mb-6">
                    {progress.total > 0 && (
                      <p>
                        Processing row {progress.current} of {progress.total}
                        {' '}
                        ({((progress.current / progress.total) * 100).toFixed(1)}%)
                      </p>
                    )}
                  </div>

                  {/* Processing Steps - Shows the different phases of processing */}
                  <div className="text-left text-sm text-base-content/60 w-full mb-8">
                    <p className={processingStatus === 'extracting' ? 'text-primary' : ''}>
                      • Extracting data from Excel
                    </p>
                    <p className={processingStatus === 'processing' ? 'text-primary' : ''}>
                      • Processing through AI
                    </p>
                    <p className={processingStatus === 'generating' ? 'text-primary' : ''}>
                      • Generating results
                    </p>
                  </div>

                  {/* Action Buttons - Stop processing or download completed file */}
                  <div className="flex gap-4 w-full">
                    {/* Stop & Save button - allows interrupting processing while saving progress */}
                    <button 
                      className="btn btn-warning flex-1"
                      onClick={() => {
                        if (window.confirm('Are you sure you want to stop processing? This will save all processed rows so far.')) {
                          handleStopAndSave();
                        }
                      }}
                      disabled={!isProcessing || isPreparingDownload}
                    >
                      {isPreparingDownload ? (
                        <>
                          <span className="loading loading-spinner loading-sm"></span>
                          Stopping...
                        </>
                      ) : (
                        'Stop & Save'
                      )}
                    </button>
                    {/* Download button - gets the processed file when available */}
                    <button 
                      className="btn btn-primary flex-1"
                      onClick={handleDownload}
                      disabled={isProcessing || !hasProcessedData || isPreparingDownload}
                    >
                      {isPreparingDownload ? (
                        <>
                          <span className="loading loading-spinner loading-sm"></span>
                          Preparing...
                        </>
                      ) : (
                        'Download'
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App