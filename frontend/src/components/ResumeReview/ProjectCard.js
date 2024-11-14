import React, { useState } from 'react';
import { X, CircleDashed } from 'lucide-react';

export default function ProjectCard({ project, onDiscard, onChange }) {
  const [isDiscarding, setIsDiscarding] = useState(false);

  const handleDiscard = async () => {
    try {
      setIsDiscarding(true);
      await fetch('http://localhost:5000/discard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ projectId: project.id })
      });
      
      onDiscard(project.id);
    } catch (error) {
      console.error('Failed to discard project:', error);
      setIsDiscarding(false);
    }
  };

  return (
    <div className="relative group">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-4">
          <h3 className="text-xl font-semibold text-green-400">{project.name}</h3>
          <span className="text-sm text-green-400 bg-green-400/10 px-3 py-1 rounded-full">
            {project.code}
          </span>
        </div>
        <button
          onClick={handleDiscard}
          disabled={isDiscarding}
          className="p-2 rounded-full hover:bg-gray-700 
                  opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out"
          title={isDiscarding ? "Discarding..." : "Discard this project"}
        >
          {isDiscarding ? (
            <CircleDashed size={20} className="text-green-400 animate-spin" />
          ) : (
            <X size={20} className="text-green-400" />
          )}
        </button>
      </div>
      <textarea
        className="w-full p-6 bg-gray-900 border border-gray-700 rounded-xl text-gray-100
                 min-h-[200px] shadow-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500
                 transition duration-200 ease-in-out font-mono text-sm"
        value={project.content}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}