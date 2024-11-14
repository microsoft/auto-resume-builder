// src/components/ResumeReview/SuccessScreen.js
import React from 'react';
import { Check, Download } from 'lucide-react';

export default function SuccessScreen() {
  const handleDownload = () => {
    console.log('Downloading resume...');
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