'use client';

import { useState } from 'react';
import { MapPin, X } from 'lucide-react';

interface StravaMapProps {
  activityId: string;
  activityName: string;
  hasMap: boolean;
  stravaUrl: string;
}

export default function StravaMap({ activityId, activityName, hasMap, stravaUrl }: StravaMapProps) {
  const [showMap, setShowMap] = useState(false);

  if (!hasMap) {
    return null;
  }

  return (
    <>
      {/* Map Button */}
      <button
        onClick={() => setShowMap(true)}
        className="p-2 text-gray-400 hover:text-blue-600 transition-colors bg-blue-50 hover:bg-blue-100 rounded-lg"
        title="View route map"
      >
        <MapPin className="h-4 w-4" />
      </button>

      {/* Map Modal */}
      {showMap && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">{activityName} - Route Map</h3>
              <button
                onClick={() => setShowMap(false)}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            
            {/* Map Content */}
            <div className="p-4">
              <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                <iframe
                  src={`https://www.strava.com/activities/${activityId}/embed/${activityId}`}
                  width="100%"
                  height="100%"
                  frameBorder="0"
                  allowFullScreen
                  title={`${activityName} route map`}
                  className="w-full h-full"
                />
              </div>
              
              {/* Fallback if iframe doesn't work */}
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-600 mb-2">
                  If the map doesn&apos;t load, you can view it on Strava:
                </p>
                <a
                  href={stravaUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                >
                  <MapPin className="h-4 w-4 mr-2" />
                  View on Strava
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
