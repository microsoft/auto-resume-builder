import React from 'react';
import { CircleDot } from 'lucide-react';

const BulletItem = ({ children }) => (
  <div className="flex items-start space-x-3 mb-4">
    <CircleDot className="h-2 w-2 text-blue-400 flex-shrink-0 mt-2" />
    <span className="text-gray-300 text-sm leading-relaxed">{children}</span>
  </div>
);

export default function ReviewChecklist() {
  return (
    <div className="absolute right-8 top-20 w-80">
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700">
        <h3 className="text-blue-400 font-semibold mb-4 text-lg">Guidance</h3>
        
        <div className="space-y-2">
          <BulletItem>
            You recently billed enough hours to a project that may warrant it being added to your resume. Review the projects to see if they should be included.
          </BulletItem>
          
          <BulletItem>
            Read through the AI-generated descriptions. They should accurately reflect your role and contributions.
          </BulletItem>
          
          <BulletItem>
            Edit descriptions if needed. Make them concise but comprehensive, highlighting key achievements and responsibilities.
          </BulletItem>
          
          <BulletItem>
            Use action verbs and quantify results where possible (e.g., "Reduced costs by 25%", "Managed team of 5").
          </BulletItem>
          
          <BulletItem>
            Do not worry about the formatting; the AI will handle that.
          </BulletItem>
          
          <BulletItem>
            Click the discard button to remove any projects that shouldn't be added to your resume. You will get another notification if you bill more hours to the project in the future.
          </BulletItem>
          
          <BulletItem>
            Click Save when you're satisfied with all project descriptions.
          </BulletItem>

          <BulletItem>
            After saving, you will have an opportunity to download your updated resume
          </BulletItem>
        </div>
        
        <div className="mt-6 pt-4 border-t border-gray-700">
          <p className="text-gray-400 text-xs italic">
            Project descriptions are AI-generated and may not be perfect. 
          </p>
        </div>
      </div>
    </div>
  );
}