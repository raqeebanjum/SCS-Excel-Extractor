import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

function App() {
  const [currentStep, setCurrentStep] = useState('upload')
  const [file, setFile] = useState(null)
  const [sheetNames, setSheetNames] = useState([])
  const [uploadId, setUploadId] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const onDrop = useCallback(acceptedFiles => {
    const selectedFile = acceptedFiles[0]
    if (selectedFile && selectedFile.name.endsWith('.xlsx')) {
      setFile(selectedFile)
    } else {
      alert('Please select an Excel file (.xlsx)')
    }
  }, [])

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
      
      const sheetName = document.getElementById('sheetSelect').value
      const partCell = document.getElementById('partCell').value
      const descCell = document.getElementById('descCell').value

      if (!sheetName || !partCell || !descCell) {
        alert('Please fill in all fields')
        return
      }

      const formData = new FormData()
      formData.append('upload_id', uploadId)
      formData.append('sheet_name', sheetName)
      formData.append('part_cell', partCell)
      formData.append('desc_cell', descCell)

      setCurrentStep('processing')

      const response = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const blob = await response.blob()
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
      alert('Failed to process file. Please try again.')
      setCurrentStep('sheet')
    } finally {
      setIsProcessing(false)
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
                      <span className="label-text-alt text-base-content/60">e.g., A2</span>
                    </label>
                    <input 
                      id="partCell"
                      type="text" 
                      className="input input-bordered"
                      placeholder="A2"
                      required
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Description Starting Cell</span>
                      <span className="label-text-alt text-base-content/60">e.g., B2</span>
                    </label>
                    <input 
                      id="descCell"
                      type="text" 
                      className="input input-bordered"
                      placeholder="B2"
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
              <div className="card-body items-center text-center">
                <div className="loading loading-spinner loading-lg text-primary"></div>
                <h2 className="card-title mt-4">Processing Your File</h2>
                <p className="text-base-content/60">This may take a few moments...</p>
                <div className="mt-4 text-sm text-base-content/60">
                  <p>• Extracting data from Excel</p>
                  <p>• Processing through AI</p>
                  <p>• Generating results</p>
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