import React, { useState, useEffect, useRef } from 'react';
import { X, CircleDashed } from 'lucide-react';

const ProjectCard = ({ project, onDiscard, onChange }) => {
  const [isDiscarding, setIsDiscarding] = useState(false);
  const textareaRef = useRef(null);

  // Auto-resize textarea on content change
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [project.content]);

  const handleDiscard = async () => {
    try {
      setIsDiscarding(true);
      await onDiscard(project.project_number);
    } catch (error) {
      console.error('Failed to discard project:', error);
      setIsDiscarding(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 relative">
      <button
        onClick={handleDiscard}
        disabled={isDiscarding}
        className="absolute top-4 right-4 text-gray-400 hover:text-red-500 
                   transition-colors duration-200"
      >
        {isDiscarding ? (
          <CircleDashed size={20} className="animate-spin" />
        ) : (
          <X size={20} />
        )}
      </button>

      <div className="mb-4">
        <h3 className="text-xl font-semibold text-green-400 mb-1">
          {project.name}
        </h3>
        <p className="text-gray-400">
          Project Number: {project.project_number}
        </p>
        <p className="text-gray-400">
          Role: {project.role}
        </p>
        <p className="text-gray-400">
          Hours: {project.total_hours}
        </p>
      </div>

      <textarea
        ref={textareaRef}
        value={project.content}
        onChange={(e) => {
          onChange(e.target.value);
          // Height will be adjusted by useEffect
        }}
        className="w-full min-h-32 bg-gray-800 text-gray-100 p-3 rounded resize-none
                   focus:ring-2 focus:ring-blue-500 focus:outline-none overflow-hidden"
        placeholder="Project description..."
      />
    </div>
  );
};

export default ProjectCard;