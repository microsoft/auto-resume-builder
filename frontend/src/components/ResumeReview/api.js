// src/components/ResumeReview/api.js
export async function fetchPendingUpdates() {
    const response = await fetch('http://localhost:5000/get_pending_updates');
    const data = await response.json();
    
    if (data.status !== 'success') {
      throw new Error('Failed to load updates');
    }
    
    return data;
  }

  export async function discardUpdate(projectId) {
    const response = await fetch('http://localhost:5000/discard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ projectId })
    });
    
    const data = await response.json();
    
    if (data.status !== 'success') {
        throw new Error(data.message || 'Failed to discard update');
    }
    
    return data;
}