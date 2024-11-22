import React, { useState } from 'react';
import { Check, Download } from 'lucide-react';

export default function SuccessScreen() {
  const [isLoading, setIsLoading] = useState(false);

  const handleDownload = async () => {
    console.log('Downloading resume...');
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/download');
      const data = await response.json();

      if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to download resume');
      }

      // Convert base64 to blob
      const content = atob(data.content);
      const bytes = new Uint8Array(content.length);
      for (let i = 0; i < content.length; i++) {
        bytes[i] = content.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: data.contentType });
      
      // Create download link
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error downloading document:', error);
      alert(`Error downloading resume: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-8 shadow-2xl text-center">
      <Check className="text-green-400 mx-auto mb-6" size={48} />
      <h2 className="text-2xl font-bold text-blue-400 mb-6">
        Your resume has been updated!
      </h2>
      <button
        onClick={handleDownload}
        disabled={isLoading}
        className="px-8 py-3 rounded-xl bg-green-500 hover:bg-green-600 text-gray-900 
                 font-semibold transition duration-200 ease-in-out transform hover:scale-105 
                 shadow-lg inline-flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download size={20} className="mr-2" />
        {isLoading ? 'Downloading...' : 'Download Resume'}
      </button>
    </div>
  );
}