export async function getCurrentUser() {
  const response = await fetch('http://localhost:5000/get_current_user');
  const data = await response.json();
  
  if (data.status !== 'success') {
      throw new Error('Failed to get current user');
  }
  
  return data.employeeId;
}

export async function fetchPendingUpdates() {
  const response = await fetch('http://localhost:5000/get_pending_updates');
  const data = await response.json();
  
  if (data.status !== 'success') {
      throw new Error('Failed to load updates');
  }
  
  return data;
}

export async function saveUpdates(employee_id, project_numbers) {
  const response = await fetch('http://localhost:5000/save', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
          employee_id,
          project_numbers 
      })
  });
  
  const data = await response.json();
  
  if (data.status !== 'success') {
      throw new Error(data.message || 'Failed to save updates');
  }
  
  return data;
}

export async function discardUpdate(employee_id, project_number) {
  const response = await fetch('http://localhost:5000/discard', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
          employee_id,
          project_number 
      })
  });
  
  const data = await response.json();
  
  if (data.status !== 'success') {
      throw new Error(data.message || 'Failed to discard update');
  }
  
  return data;
}

// Add this to your existing api.js file

export async function submitFeedback(feedbackData) {
  const response = await fetch('http://localhost:5000/feedback', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedbackData)
  });
  
  const data = await response.json();
  
  if (data.status !== 'success') {
      throw new Error(data.message || 'Failed to submit feedback');
  }
  
  return data;
}