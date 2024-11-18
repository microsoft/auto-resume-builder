import React, { useState, useEffect } from 'react';
import LoadingScreen from './LoadingScreen';
import ErrorScreen from './ErrorScreen';
import ReviewScreen from './ReviewScreen';
import SuccessScreen from './SuccessScreen';
import EmptyScreen from './EmptyScreen';
import FeedbackFeature from './FeedbackFeature';
import { 
  fetchPendingUpdates, 
  getCurrentUser, 
  saveUpdates, 
  discardUpdate,
  submitFeedback 
} from './api';

const ResumeReview = () => {
  const [viewState, setViewState] = useState('review');
  const [resumeContent, setResumeContent] = useState({ projects: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [employee_id, setEmployeeId] = useState(null);

  useEffect(() => {
    initialize();
  }, []);

  const initialize = async () => {
    try {
      setIsLoading(true);
      const userId = await getCurrentUser();
      setEmployeeId(userId);
      await loadPendingUpdates();
    } catch (err) {
      setError('Failed to initialize application');
      console.error('Error during initialization:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPendingUpdates = async () => {
    try {
      const data = await fetchPendingUpdates();
      setResumeContent({ projects: data.projects });
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Error fetching updates:', err);
      throw err;
    }
  };

  const handleSave = async () => {
    try {
      const project_numbers = resumeContent.projects.map(p => p.project_number);
      await saveUpdates(employee_id, project_numbers);
      setViewState('success');
    } catch (error) {
      setError('Failed to save updates');
      console.error('Error saving resume:', error);
    }
  };

  const handleDiscard = async (project_number) => {
    try {
      await discardUpdate(employee_id, project_number);
      setResumeContent(prev => ({
        ...prev,
        projects: prev.projects.filter(p => p.project_number !== project_number)
      }));
    } catch (error) {
      setError('Failed to discard update');
      console.error('Error discarding project:', error);
    }
  };


  const handleFeedbackSubmit = async (feedbackData) => {
    try {
      await submitFeedback(feedbackData);
      // Optionally show a success message
      // You could use a toast notification here
      console.log('Feedback submitted successfully');
    } catch (error) {
      console.error('Error submitting feedback:', error);
      // Optionally show an error message
      throw error; // This will be caught by the FeedbackModal's error handling
    }
  };

  if (isLoading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} />;

  return (
    <div className="min-h-screen bg-gray-900 p-8 relative">
      <div className="max-w-4xl mx-auto">
        {viewState === 'review' && resumeContent.projects.length === 0 ? (
          <EmptyScreen />
        ) : (
          viewState === 'review' ? (
            <ReviewScreen 
              projects={resumeContent.projects}
              onSave={handleSave}
              onDiscard={handleDiscard}
              onUpdateContent={(updatedProjects) => 
                setResumeContent({ ...resumeContent, projects: updatedProjects })}
            />
          ) : (
            <SuccessScreen />
          )
        )}
      </div>
      <FeedbackFeature onSubmitFeedback={handleFeedbackSubmit} />
    </div>
  );
};

export default ResumeReview;