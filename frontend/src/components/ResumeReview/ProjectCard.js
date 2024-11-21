import React, { useState, useEffect, useRef } from 'react';
import { Trash2, CircleDashed } from 'lucide-react';

const ProjectCard = ({ project, onDiscard, onChange }) => {
  const [isDiscarding, setIsDiscarding] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [project.content]);

  const handleDiscardClick = () => {
    setShowConfirm(true);
  };

  const handleConfirmDiscard = async () => {
    try {
      setIsDiscarding(true);
      await onDiscard(project.project_number);
    } catch (error) {
      console.error('Failed to discard project:', error);
      setIsDiscarding(false);
      setShowConfirm(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 relative">
      <div className="absolute top-4 right-4 flex items-center space-x-2">
        {showConfirm ? (
          <div className="flex items-center space-x-3 bg-gray-800 rounded-lg p-2">
            {isDiscarding ? (
              <div className="flex items-center space-x-2">
                <CircleDashed size={16} className="text-gray-400 animate-spin" />
                <span className="text-gray-300 text-sm">Removing...</span>
              </div>
            ) : (
              <>
                <span className="text-gray-300 text-sm">Discard this project for now?</span>
                <button
                  onClick={handleConfirmDiscard}
                  className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded-md text-sm font-medium transition-colors duration-200"
                >
                  Yes
                </button>
                <button
                  onClick={() => setShowConfirm(false)}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-md text-sm font-medium transition-colors duration-200"
                >
                  No
                </button>
              </>
            )}
          </div>
        ) : (
          <button
            onClick={handleDiscardClick}
            disabled={isDiscarding}
            className="group flex items-center space-x-1 text-gray-400 hover:text-red-500 
                     transition-colors duration-200 px-2 py-1 rounded hover:bg-gray-800"
            title="Project should not be added to your resume at this time"
          >
            <Trash2 size={18} />
            <span className="text-sm">Discard</span>
          </button>
        )}
      </div>

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
          e.target.style.height = 'auto';
          e.target.style.height = `${e.target.scrollHeight}px`;
        }}
        className="w-full bg-gray-800 text-gray-100 p-3 rounded
                   focus:ring-2 focus:ring-blue-500 focus:outline-none
                   resize-none overflow-hidden"
        style={{ minHeight: '8rem' }}
        placeholder="Project description..."
      />
    </div>
  );
};

export default ProjectCard;