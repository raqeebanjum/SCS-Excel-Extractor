import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

function App() {
  const [currentStep, setCurrentStep] = useState('upload')
  const [file, setFile] = useState(null)
  const [sheetNames, setSheetNames] = useState([])
  const [uploadId, setUploadId] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStatus, setProcessingStatus] = useState('');
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [hasProcessedData, setHasProcessedData] = useState(false);
  const [isPreparingDownload, setIsPreparingDownload] = useState(false);
  const [processedFilePath, setProcessedFilePath] = useState(null);


  const onDrop = useCallback(acceptedFiles => {
    const selectedFile = acceptedFiles[0]
    if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
      setFile(selectedFile)
    } else {
      alert('Please select an Excel file (.xlsx)')
    }
  }, [])


  const handleStopAndSave = async () => {
    try {
      setIsPreparingDownload(true);
      console.log('Sending stop request...');
      
      const response = await fetch('/api/stop', {
        method: 'POST',
      });
  
      console.log('Stop response status:', response.status);
      const data = await response.json();
      console.log('Stop response data:', data);
  
      if (data.success) {
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
      setIsPreparingDownload(false);
    }
  };

  const handleDownload = async () => {
    try {
      setIsPreparingDownload(true);
      
      let retries = 3;
      let response;
      
      while (retries > 0) {
        try {
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
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds between retries
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
  
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'processed_results.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Optional: Show success message
      alert('File downloaded successfully!');
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download file. Please try again.');
    } finally {
      setIsPreparingDownload(false);
    }
  };



  const startProgressMonitoring = () => {
    const eventSource = new EventSource('/api/progress');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };

    return eventSource;
  };



  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    multiple: false
  })

  const handleUpload = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('Uploading file:', file)
      console.log('Sending request to /api/upload')

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      console.log('Response status:', response.status)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Upload response:', data)
      
      if (data.error) {
        throw new Error(data.error)
      }

      setUploadId(data.upload_id)
      setSheetNames(data.sheet_names)
      setCurrentStep('sheet')
      
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Failed to upload file. Please try again.')
    }
  }

  const handleProcess = async () => {
    try {
      setIsProcessing(true)
      setProgress({ current: 0, total: 0 })
      setProcessingStatus('extracting')
      
      // Start progress monitoring
      const eventSource = startProgressMonitoring();
      
      const sheetName = document.getElementById('sheetSelect').value
      const partCell = document.getElementById('partCell').value
      const descCell = document.getElementById('descCell').value
      const vendorCell = document.getElementById('vendorCell').value 

  
      if (!sheetName || !partCell || !descCell || !vendorCell) {
        alert('Please fill in all fields')
        return
      }
  
      console.log('Starting process with:', { sheetName, partCell, descCell, uploadId });
  
      const formData = new FormData()
      formData.append('upload_id', uploadId)
      formData.append('sheet_name', sheetName)
      formData.append('part_cell', partCell)
      formData.append('desc_cell', descCell)
      formData.append('vendor_cell', vendorCell)
  
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
  
      const blob = await response.blob()
      console.log('Received blob:', blob);
  
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'processed_results.xlsx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
  
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
      setIsProcessing(false)
      setProgress({ current: 0, total: 0 })
      setProcessingStatus('')
    }
  }

  return (
    <div className="min-h-screen bg-base-300 text-base-content">
      {/* Header */}
      <div className="navbar bg-base-200 shadow-lg">
        <div className="flex-1 px-4">
          <h1 className="text-2xl font-bold">SCS Excel Processor</h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Progress Steps */}
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

        {/* Content Cards */}
        <div className="max-w-2xl mx-auto">
          {currentStep === 'upload' && (
            <div className="card bg-base-100 shadow-xl">
              <div className="card-body">
                <div 
                  {...getRootProps()} 
                  className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-all duration-200
                    ${isDragActive ? 'border-primary bg-base-200' : 'border-base-content/20 hover:border-primary'}`}
                >
                  <input {...getInputProps()} />
                  <div className="flex flex-col items-center gap-4">
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

                  {/* Add new Vendor Cell input */}
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
                  <div className="mb-8"> 
                    <div className="loading loading-spinner loading-lg text-primary"></div>
                  </div>
                  
                  <div className="mb-8 text-center">
                    <h2 className="card-title justify-center mb-2">Processing Your File</h2> 
                    <p className="text-base-content/60">This may take a few moments...</p>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-base-200 rounded-full h-2.5 mb-4">
                    <div 
                      className="bg-primary h-2.5 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` 
                      }}
                    ></div>
                  </div>

                  {/* Progress Text */}
                  <div className="text-sm text-base-content/70 mb-6">
                    {progress.total > 0 && (
                      <p>
                        Processing row {progress.current} of {progress.total}
                        {' '}
                        ({((progress.current / progress.total) * 100).toFixed(1)}%)
                      </p>
                    )}
                  </div>

                  {/* Processing Steps */}
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

                  {/* Action Buttons */}
                  <div className="flex gap-4 w-full">
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