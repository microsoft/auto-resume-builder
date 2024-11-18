import React, { useState, useEffect } from 'react';
import { FileText, Download, Check, X, HelpCircle } from 'lucide-react';

const ResumeReview = () => {
  const [viewState, setViewState] = useState('review');
  const [resumeContent, setResumeContent] = useState({ projects: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPendingUpdates();
  }, []);

  const fetchPendingUpdates = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:5000/get_pending_updates');
      const data = await response.json();
      
      if (data.status === 'success') {
        setResumeContent({ projects: data.projects });
      } else {
        setError('Failed to load updates');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error fetching updates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setViewState('success');
    } catch (error) {
      console.error('Error saving resume:', error);
    }
  };

  const handleDiscard = async (projectId) => {
    setResumeContent(prev => ({
      ...prev,
      projects: prev.projects.filter(p => p.id !== projectId)
    }));
  };

  const handleDownload = () => {
    console.log('Downloading resume...');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-blue-500 text-xl">Loading updates...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-red-500 text-xl">{error}</div>
      </div>
    );
  }

  const ReviewScreen = () => (
    <div className="flex-1 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1 flex justify-center items-center">
          <FileText className="text-blue-500 mr-3" size={32} />
          <h1 className="text-3xl font-bold text-blue-500">
            Dan Giannone Work Experience
          </h1>
        </div>
        <button
          className="absolute right-8 p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition duration-200 
                   text-green-400 hover:text-green-300 flex items-center gap-2"
        >
          <HelpCircle size={20} />
          <span>Tips</span>
        </button>
      </div>
      
      <div className="bg-gray-800 rounded-xl p-8 shadow-2xl flex-1">
        <div className="space-y-6">
          {resumeContent.projects.map(project => (
            <div key={project.id} className="relative group">
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-4">
                  <h3 className="text-xl font-semibold text-green-400">{project.name}</h3>
                  <span className="text-sm text-green-400 bg-green-400/10 px-3 py-1 rounded-full">
                    {project.code}
                  </span>
                </div>
                <button
                  onClick={() => handleDiscard(project.id)}
                  className="p-2 rounded-full hover:bg-gray-700 
                           opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out"
                  title="Discard this project"
                >
                  <X size={20} className="text-green-400" />
                </button>
              </div>
              <textarea
                className="w-full p-6 bg-gray-900 border border-gray-700 rounded-xl text-gray-100 
                          min-h-[200px] shadow-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 
                          transition duration-200 ease-in-out font-mono text-sm"
                value={project.content}
                onChange={(e) => {
                  const updatedProjects = resumeContent.projects.map(p =>
                    p.id === project.id ? { ...p, content: e.target.value } : p
                  );
                  setResumeContent({ ...resumeContent, projects: updatedProjects });
                }}
              />
            </div>
          ))}
        </div>

        <div className="flex justify-end mt-8">
          <button
            onClick={handleSave}
            className="px-8 py-3 rounded-xl bg-green-500 hover:bg-green-600 text-gray-900 
                     font-semibold transition duration-200 ease-in-out transform hover:scale-105 
                     shadow-lg"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );

  const SuccessScreen = () => (
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

  const DiscardedScreen = () => (
    <div className="bg-gray-800 rounded-xl p-8 shadow-2xl text-center">
      <X className="text-red-400 mx-auto mb-6" size={48} />
      <h2 className="text-2xl font-bold text-blue-400 mb-4">
        Changes Discarded
      </h2>
      <p className="text-gray-300">The resume updates have been discarded.</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {viewState === 'review' && <ReviewScreen />}
        {viewState === 'success' && <SuccessScreen />}
        {viewState === 'discarded' && <DiscardedScreen />}
      </div>
    </div>
  );
};

export default ResumeReview;