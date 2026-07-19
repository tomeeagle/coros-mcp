'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { TrendingUp, Clock, Zap, Heart, Route, Activity, Target, ExternalLink, RefreshCw, BarChart3 } from 'lucide-react';
import StravaMap from '@/components/StravaMap';
import { useState, useEffect } from 'react';
import Link from 'next/link';

interface StravaActivity {
  id: string;
  name: string;
  type: 'Run' | 'Ride' | 'Swim' | 'Walk' | 'Hike' | 'Workout';
  distance: number;
  duration: number;
  averageSpeed: number;
  maxSpeed: number;
  averageHeartRate?: number;
  maxHeartRate?: number;
  elevationGain: number;
  startDate: string;
  hasMap: boolean;
  description?: string;
  kudos: number;
  comments: number;
  stravaUrl?: string;
  averageCadence?: number;
  averageWatts?: number;
  maxWatts?: number;
  calories?: number;
  sufferScore?: number;
}

interface StravaStatus {
  connected: boolean;
  athleteName?: string;
  athleteId?: number;
  expiresAt?: string;
  expiresSoon?: boolean;
  message: string;
}

export default function StravaPage() {
  const [selectedType, setSelectedType] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('7');
  const [activities, setActivities] = useState<StravaActivity[]>([]);
  const [stravaStatus, setStravaStatus] = useState<StravaStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check URL parameters for OAuth results
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('error');
    const successParam = urlParams.get('success');
    const athleteParam = urlParams.get('athlete');

    if (errorParam) {
      setError(getErrorMessage(errorParam));
      // Clean up URL
      window.history.replaceState({}, document.title, '/strava');
    }

    if (successParam && athleteParam) {
      setSuccess(`Successfully connected to Strava as ${athleteParam}!`);
      // Clean up URL
      window.history.replaceState({}, document.title, '/strava');
      // Refresh status and activities
      checkStravaStatus();
      fetchActivities();
    }
  }, []);

  // Check Strava connection status
  const checkStravaStatus = async () => {
    try {
      const response = await fetch('/api/strava/status');
      if (response.ok) {
        const status = await response.json();
        setStravaStatus(status);
      } else {
        setStravaStatus({ connected: false, message: 'Failed to check status' });
      }
    } catch (error) {
      console.error('Error checking Strava status:', error);
      setStravaStatus({ connected: false, message: 'Connection error' });
    }
  };

  // Fetch activities from Strava
  const fetchActivities = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/strava/activities');
      if (response.ok) {
        const data = await response.json();
        setActivities(data.activities);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to fetch activities');
      }
    } catch (error) {
      console.error('Error fetching activities:', error);
      setError('Failed to fetch activities');
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize page
  useEffect(() => {
    checkStravaStatus();
    if (stravaStatus?.connected) {
      fetchActivities();
    } else {
      setIsLoading(false);
    }
  }, [stravaStatus?.connected]);

  // Handle Strava connection
  const connectStrava = async () => {
    setIsConnecting(true);
    try {
      // Redirect to Strava OAuth
      const authUrl = `/api/strava/auth`;
      window.location.href = authUrl;
    } catch (error) {
      console.error('Error connecting to Strava:', error);
      setError('Failed to connect to Strava');
      setIsConnecting(false);
    }
  };

  // Disconnect Strava
  const disconnectStrava = async () => {
    try {
      // In a real app, you'd call an API to remove the token
      setStravaStatus({ connected: false, message: 'Strava disconnected' });
      setActivities([]);
      setSuccess('Successfully disconnected from Strava');
    } catch (error) {
      console.error('Error disconnecting from Strava:', error);
      setError('Failed to disconnect from Strava');
    }
  };

  // Get error message from error code
  const getErrorMessage = (errorCode: string): string => {
    switch (errorCode) {
      case 'access_denied':
        return 'Access was denied. Please try again.';
      case 'no_code':
        return 'Authorization failed. Please try again.';
      case 'callback_failed':
        return 'Connection failed. Please try again.';
      default:
        return 'An error occurred while connecting to Strava.';
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDistance = (km: number) => {
    if (km >= 1) {
      return `${km.toFixed(1)} km`;
    }
    return `${(km * 1000).toFixed(0)} m`;
  };

  const formatSpeed = (kmh: number, type: string) => {
    if (type === 'Run' || type === 'Walk') {
      const pace = 60 / kmh; // minutes per km
      return `${Math.floor(pace)}:${((pace % 1) * 60).toFixed(0).padStart(2, '0')} /km`;
    }
    return `${kmh.toFixed(1)} km/h`;
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'Run':
        return <TrendingUp className="h-5 w-5" />;
      case 'Ride':
        return <Route className="h-5 w-5" />;
      case 'Swim':
        return <Activity className="h-5 w-5" />;
      case 'Walk':
      case 'Hike':
        return <Route className="h-5 w-5" />;
      default:
        return <Target className="h-5 w-5" />;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'Run':
        return 'bg-red-100 text-red-600';
      case 'Ride':
        return 'bg-blue-100 text-cyan-600';
      case 'Swim':
        return 'bg-cyan-100 text-cyan-600';
      case 'Walk':
      case 'Hike':
        return 'bg-green-100 text-green-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const filteredActivities = activities.filter(activity => {
    if (selectedType !== 'all' && activity.type !== selectedType) return false;
    
    const activityDate = new Date(activity.startDate);
    const daysAgo = new Date();
    daysAgo.setDate(daysAgo.getDate() - parseInt(timeRange));
    
    return activityDate >= daysAgo;
  });

  const getStats = () => {
    const totalDistance = filteredActivities.reduce((sum, a) => sum + a.distance, 0);
    const totalDuration = filteredActivities.reduce((sum, a) => sum + a.duration, 0);
    const totalElevation = filteredActivities.reduce((sum, a) => sum + a.elevationGain, 0);
    const activityCount = filteredActivities.length;
    
    return { totalDistance, totalDuration, totalElevation, activityCount };
  };

  const stats = getStats();

  // Show error message
  if (error) {
    return (
      <DashboardLayout>
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Strava Activities</h1>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-red-800 mb-2">Error</h3>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={() => setError(null)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Strava Activities</h1>
            <p className="text-gray-600">
              Track your cardio and endurance activities alongside your strength training
            </p>
          </div>
          {stravaStatus?.connected && (
            <Link
              href="/strava/analytics"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              View Analytics
            </Link>
          )}
        </div>
        
        {/* Success Message */}
        {success && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">{success}</p>
            <button
              onClick={() => setSuccess(null)}
              className="mt-2 text-green-600 hover:text-green-700 text-sm font-medium"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Connection Status */}
        {stravaStatus && (
          <div className={`mt-3 p-3 border rounded-lg ${
            stravaStatus.connected 
              ? 'bg-green-50 border-green-200' 
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${
                  stravaStatus.connected ? 'text-green-800' : 'text-blue-800'
                }`}>
                  <strong>🔗 Strava Status:</strong> {stravaStatus.message}
                </p>
                {stravaStatus.connected && stravaStatus.athleteName && (
                  <p className={`text-sm ${
                    stravaStatus.connected ? 'text-green-700' : 'text-blue-700'
                  } mt-1`}>
                    Connected as: {stravaStatus.athleteName}
                    {stravaStatus.expiresSoon && (
                      <span className="ml-2 text-yellow-600">(Token expires soon)</span>
                    )}
                  </p>
                )}
              </div>
              
              <div className="flex space-x-2">
                {stravaStatus.connected ? (
                  <>
                    <button
                      onClick={fetchActivities}
                      disabled={isLoading}
                      className="px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm flex items-center"
                    >
                      <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                      Refresh
                    </button>
                    <button
                      onClick={disconnectStrava}
                      className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={connectStrava}
                    disabled={isConnecting}
                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium"
                  >
                    {isConnecting ? 'Connecting...' : 'Connect Strava Account'}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Show content only if connected */}
      {stravaStatus?.connected ? (
        <>
          {/* Filters */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-2">
                  Activity Type
                </label>
                <select
                  id="type"
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Activities</option>
                  <option value="Run">Running</option>
                  <option value="Ride">Cycling</option>
                  <option value="Swim">Swimming</option>
                  <option value="Walk">Walking</option>
                  <option value="Hike">Hiking</option>
                </select>
              </div>
              
              <div className="flex-1">
                <label htmlFor="timeRange" className="block text-sm font-medium text-gray-700 mb-2">
                  Time Range
                </label>
                <select
                  id="timeRange"
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 3 months</option>
                </select>
              </div>
            </div>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Activity className="h-5 w-5 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Activities</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.activityCount}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Route className="h-5 w-5 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Distance</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalDistance.toFixed(1)} km</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Clock className="h-5 w-5 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Time</p>
                  <p className="text-2xl font-bold text-gray-900">{formatDuration(stats.totalDuration)}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <div className="flex items-center">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-orange-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Elevation</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalElevation} m</p>
                </div>
              </div>
            </div>
          </div>

          {/* Activities List */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">Recent Activities</h3>
              <span className="text-sm text-gray-500">{filteredActivities.length} activities</span>
            </div>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading activities from Strava...</p>
              </div>
            ) : filteredActivities.length === 0 ? (
              <div className="text-center py-12">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No activities found</h3>
                <p className="text-gray-600">Try adjusting your filters or check your Strava account.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredActivities.map((activity) => (
                  <div key={activity.id} className="border border-gray-200 rounded-lg p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {/* Activity Header */}
                        <div className="flex items-center space-x-3 mb-3">
                          <div className={`p-2 rounded-lg ${getActivityColor(activity.type)}`}>
                            {getActivityIcon(activity.type)}
                          </div>
                          <div>
                            <h4 className="text-lg font-semibold text-gray-900">{activity.name}</h4>
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <span>{activity.type}</span>
                              <span>•</span>
                              <span>{new Date(activity.startDate).toLocaleDateString()}</span>
                              <span>•</span>
                              <span>{new Date(activity.startDate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Activity Stats Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <p className="text-sm text-gray-600">Distance</p>
                            <p className="font-medium text-gray-900">{formatDistance(activity.distance)}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Duration</p>
                            <p className="font-medium text-gray-900">{formatDuration(activity.duration)}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Pace/Speed</p>
                            <p className="font-medium text-gray-900">{formatSpeed(activity.averageSpeed, activity.type)}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Elevation</p>
                            <p className="font-medium text-gray-900">{activity.elevationGain} m</p>
                          </div>
                        </div>
                        
                        {/* Heart Rate & Social */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-6 text-sm">
                            {activity.averageHeartRate && (
                              <div className="flex items-center space-x-2">
                                <Heart className="h-4 w-4 text-red-500" />
                                <span className="text-gray-600">
                                  Avg: {activity.averageHeartRate} bpm
                                </span>
                              </div>
                            )}
                            {activity.maxHeartRate && (
                              <div className="flex items-center space-x-2">
                                <Zap className="h-4 w-4 text-yellow-500" />
                                <span className="text-gray-600">
                                  Max: {activity.maxHeartRate} bpm
                                </span>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>❤️ {activity.kudos}</span>
                            <span>💬 {activity.comments}</span>
                          </div>
                        </div>
                        
                                                 {/* Description */}
                         {activity.description && (
                           <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                             <p className="text-sm text-gray-700 italic">&quot;{activity.description}&quot;</p>
                           </div>
                         )}
                      </div>
                      
                      {/* Action Buttons */}
                      <div className="flex flex-col space-y-2 ml-4">
                        <StravaMap
                          activityId={activity.id}
                          activityName={activity.name}
                          hasMap={activity.hasMap}
                          stravaUrl={activity.stravaUrl || ''}
                        />
                        {activity.stravaUrl && (
                          <a
                            href={activity.stravaUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 text-gray-400 hover:text-orange-600 transition-colors bg-orange-50 hover:bg-orange-100 rounded-lg"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        /* Not Connected State */
        <div className="text-center py-16">
          <div className="max-w-md mx-auto">
            <div className="w-24 h-24 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <TrendingUp className="h-12 w-12 text-orange-600" />
            </div>
            <h3 className="text-xl font-medium text-gray-900 mb-2">Connect Your Strava Account</h3>
            <p className="text-gray-600 mb-8">
              Connect your Strava account to automatically sync your activities and get comprehensive fitness insights.
            </p>
            <button
              onClick={connectStrava}
              disabled={isConnecting}
              className="w-full px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium disabled:opacity-50"
            >
              {isConnecting ? 'Connecting...' : 'Connect Strava Account'}
            </button>
            <p className="text-xs text-gray-500 mt-3">
              Secure OAuth connection - we only read your public activities
            </p>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
