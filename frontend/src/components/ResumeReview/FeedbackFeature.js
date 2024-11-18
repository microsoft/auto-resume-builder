import React, { useState } from 'react';
import { MessageSquarePlus, X } from 'lucide-react';

const FeedbackButton = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 bg-blue-500 hover:bg-blue-600 
                 text-white rounded-lg px-4 py-2 shadow-lg transition duration-200 
                 ease-in-out transform hover:scale-105 flex items-center space-x-2"
      aria-label="Open feedback form"
    >
      <MessageSquarePlus size={20} />
      <span>Feedback</span>
    </button>
  );
};

const FeedbackModal = ({ isOpen, onClose, onSubmit }) => {
  const [feedbackType, setFeedbackType] = useState('general');
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      await onSubmit({ type: feedbackType, content: feedback });
      setFeedback('');
      setFeedbackType('general');
      onClose();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-xl max-w-2xl w-full p-6 relative shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-300 
                     transition-colors duration-200"
        >
          <X size={20} />
        </button>

        <h2 className="text-2xl font-bold text-blue-400 mb-6">
          Share Your Feedback
        </h2>

        <div className="space-y-6">
          <div>
            <label className="block text-gray-300 mb-2 font-medium">
              Feedback Type
            </label>
            <select
              value={feedbackType}
              onChange={(e) => setFeedbackType(e.target.value)}
              className="w-full bg-gray-900 text-gray-100 rounded p-3 
                         border border-gray-700 focus:border-blue-500 
                         focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="general">General Feedback</option>
              <option value="bug">Report a Bug</option>
              <option value="feature">Feature Request</option>
              <option value="content">Content Improvement</option>
              <option value="process">Process Feedback</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-300 mb-2 font-medium">
              Your Feedback
            </label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Share your thoughts, suggestions, or report issues..."
              className="w-full h-48 bg-gray-900 text-gray-100 p-3 rounded 
                         border border-gray-700 focus:border-blue-500 
                         focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-6 py-2 rounded bg-gray-700 text-gray-300 
                       hover:bg-gray-600 transition duration-200"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!feedback.trim() || isSubmitting}
              className="px-6 py-2 rounded bg-blue-500 text-white 
                       hover:bg-blue-600 transition duration-200 
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function FeedbackFeature({ onSubmitFeedback }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <FeedbackButton onClick={() => setIsModalOpen(true)} />
      <FeedbackModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={onSubmitFeedback}
      />
    </>
  );
}