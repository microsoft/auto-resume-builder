// src/components/ResumeReview/EmptyScreen.js
import React from 'react';
import { ClipboardX } from 'lucide-react';

export default function EmptyScreen() {
  return (
    <div className="bg-gray-800 rounded-xl p-8 shadow-2xl text-center">
      <ClipboardX className="text-blue-400 mx-auto mb-6" size={48} />
      <h2 className="text-2xl font-bold text-blue-400 mb-4">
        No Updates to Review
      </h2>
      <p className="text-gray-300">
        You've reviewed all available updates. 
      </p>
    </div>
  );
}