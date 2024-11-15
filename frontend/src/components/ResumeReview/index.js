// src/components/ResumeReview/index.js
import React, { useState, useEffect } from 'react';
import LoadingScreen from './LoadingScreen';
import ErrorScreen from './ErrorScreen';
import ReviewScreen from './ReviewScreen';
import SuccessScreen from './SuccessScreen';
import EmptyScreen from './EmptyScreen';
import { fetchPendingUpdates } from './api';

const ResumeReview = () => {
  const [viewState, setViewState] = useState('review');
  const [resumeContent, setResumeContent] = useState({ projects: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPendingUpdates();
  }, []);

  const loadPendingUpdates = async () => {
    try {
      setIsLoading(true);
      const data = await fetchPendingUpdates();
      setResumeContent({ projects: data.projects });
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

  if (isLoading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} />;

  // If we're in review state and there are no projects, show empty screen
  if (viewState === 'review' && resumeContent.projects.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <EmptyScreen />
        </div>
      </div>
    );
  }

  const screens = {
    review: <ReviewScreen 
              projects={resumeContent.projects}
              onSave={handleSave}
              onDiscard={handleDiscard}
              onUpdateContent={(updatedProjects) => 
                setResumeContent({ ...resumeContent, projects: updatedProjects })}
            />,
    success: <SuccessScreen />
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-4xl mx-auto">
        {screens[viewState]}
      </div>
    </div>
  );
};

export default ResumeReview;