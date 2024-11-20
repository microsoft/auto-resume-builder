import React from 'react';
import { FileText, HelpCircle } from 'lucide-react';

export default function Header() {
  const handleTipsClick = () => {
    // Using the correct route from your Flask backend
    window.open('http://localhost:5000/tips-pdf', '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="flex justify-between items-center mb-6">
      <div className="flex-1 flex justify-center items-center">
        <FileText className="text-blue-500 mr-3" size={32} />
        <h1 className="text-3xl font-bold text-blue-500">
          Dan Giannone Work Experience
        </h1>
      </div>
      <button
        onClick={handleTipsClick}
        className="absolute right-8 p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition duration-200 
                 text-green-400 hover:text-green-300 flex items-center gap-2"
      >
        <HelpCircle size={20} />
        <span>Tips</span>
      </button>
    </div>
  );
}