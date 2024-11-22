// src/components/ResumeReview/SuccessScreen.js
import React, {useState} from 'react';
import { Check, Download } from 'lucide-react';



export default function SuccessScreen() {
  const [isLoading, setIsLoading] = useState(false);
  const handleDownload = async() => {
    console.log('Downloading resume...');
    setIsLoading(true);
    try {
      const url = `http://localhost:5000/download`;
        
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Access-Control-Allow-Origin': 'http://localhost:3001',
        },
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const blob = await response.blob();
      const fileName = response.headers.get('Content-Disposition').split('filename=')[1];
      console.log(fileName)
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    catch (error) {
      console.error('Error downloading document:', error);
      alert(`An error occurred while downloading resume`);
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
        className="px-8 py-3 rounded-xl bg-green-500 hover:bg-green-600 text-gray-900 
                 font-semibold transition duration-200 ease-in-out transform hover:scale-105 
                 shadow-lg inline-flex items-center"
      >
        <Download size={20} className="mr-2" />
        Download Resume
      </button>
    </div>
  );
}