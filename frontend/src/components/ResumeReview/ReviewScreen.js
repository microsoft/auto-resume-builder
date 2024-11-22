import React from 'react';
import { Loader2 } from 'lucide-react'; // Import the loading icon
import ProjectCard from './ProjectCard';
import Header from './Header';
import ReviewChecklist from './ReviewChecklist';

export default function ReviewScreen({ projects, onSave, onDiscard, onUpdateContent, isSaving = false }) {
  return (
    <div className="flex-1 flex flex-col">
      <Header />
      
      <div className="bg-gray-800 rounded-xl p-8 shadow-2xl flex-1">
        <div className="space-y-6">
          {projects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              onDiscard={onDiscard}
              onChange={(newContent) => {
                const updatedProjects = projects.map(p =>
                  p.id === project.id ? { ...p, content: newContent } : p
                );
                onUpdateContent(updatedProjects);
              }}
            />
          ))}
        </div>

        <div className="flex justify-end mt-8">
          <button
            onClick={onSave}
            disabled={isSaving}
            className="px-8 py-3 rounded-xl bg-green-500 hover:bg-green-600 text-gray-900 
                     font-semibold transition duration-200 ease-in-out transform hover:scale-105 
                     shadow-lg inline-flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <Loader2 className="animate-spin mr-2" size={20} />
                <span>Saving...</span>
              </>
            ) : (
              'Save'
            )}
          </button>
        </div>
      </div>
      
      <ReviewChecklist />
    </div>
  );
}