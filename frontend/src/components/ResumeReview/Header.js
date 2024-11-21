import React from 'react';
import { FileText } from 'lucide-react';

export default function Header() {
  return (
    <div className="flex justify-between items-center mb-6">
      <div className="flex-1 flex justify-center items-center">
        <FileText className="text-blue-500 mr-3" size={32} />
        <h1 className="text-3xl font-bold text-blue-500">
          Resume Updates
        </h1>
      </div>
    </div>
  );
}