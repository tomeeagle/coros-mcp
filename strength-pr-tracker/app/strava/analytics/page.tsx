'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { TrendingUp, Clock, Route, Activity, BarChart3, PieChart, Trophy, ExternalLink } from 'lucide-react';
import StravaMap from '@/components/StravaMap';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Cell, Pie } from 'recharts';

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

interface ActivityStats {
  type: string;
  count: number;
  totalDistance: number;
  totalDuration: number;
  totalElevation: number;
  averageSpeed: number;
  averageHeartRate?: number;
  bestDistance: number;
  bestDuration: number;
  bestElevation: number;
  bestSpeed: number;
  totalCalories: number;
  totalSufferScore: number;
}

interface TimeRangeData {
  label: string;
  days: number;
}

const timeRanges: TimeRangeData[] = [
  { label: 'This Week', days: 0 }, // 0 means special handling for week boundaries
  { label: 'This Month', days: 0 }, // 0 means special handling for month boundaries
  { label: '3 Months', days: 90 },
  { label: '6 Months', days: 180 },
  { label: 'This Year', days: 0 }, // 0 means special handling for year boundaries
  { label: 'All Time', days: 3650 }
];

const activityColors = {
  Run: '#ef4444',
  Ride: '#3b82f6',
  Swim: '#06b6d4',
  Walk: '#10b981',
  Hike: '#059669',
  Workout: '#8b5cf6'
};

export default function StravaAnalyticsPage() {
  const [activities, setActivities] = useState<StravaActivity[]>([]);
  const [selectedTimeRange, setSelectedTimeRange] = useState<TimeRangeData>(timeRanges[0]); // Default to This Week
  const [selectedActivityType, setSelectedActivityType] = useState<string>('Run'); // Default to running
  const [useMiles, setUseMiles] = useState<boolean>(true); // Default to miles
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchActivities();
  }, []);

  const fetchActivities = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/strava/activities?perPage=200');
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

  const getFilteredActivities = () => {
    let cutoffDate: Date;
    
    if (selectedTimeRange.label === 'This Week') {
      // Get Monday of current week (Monday = 1, Sunday = 0)
      const today = new Date();
      const dayOfWeek = today.getDay();
      const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // If Sunday, go back 6 days
      cutoffDate = new Date(today);
      cutoffDate.setDate(today.getDate() + mondayOffset);
      cutoffDate.setHours(0, 0, 0, 0); // Start of Monday
    } else if (selectedTimeRange.label === 'This Month') {
      // Get first day of current month
      const today = new Date();
      cutoffDate = new Date(today.getFullYear(), today.getMonth(), 1);
      cutoffDate.setHours(0, 0, 0, 0);
    } else if (selectedTimeRange.label === 'This Year') {
      // Get first day of current year
      const today = new Date();
      cutoffDate = new Date(today.getFullYear(), 0, 1);
      cutoffDate.setHours(0, 0, 0, 0);
    } else {
      // For other ranges, use the simple day subtraction
      cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - selectedTimeRange.days);
    }
    
    return activities.filter(activity => 
      new Date(activity.startDate) >= cutoffDate
    );
  };

  const getFilteredActivitiesByType = () => {
    const filteredByTime = getFilteredActivities();
    return filteredByTime.filter(activity => activity.type === selectedActivityType);
  };

  const getActivityStats = (): ActivityStats[] => {
    const filteredActivities = getFilteredActivities();
    const statsMap = new Map<string, ActivityStats>();
    
    filteredActivities.forEach(activity => {
      const type = activity.type;
      
      if (!statsMap.has(type)) {
        statsMap.set(type, {
          type,
          count: 0,
          totalDistance: 0,
          totalDuration: 0,
          totalElevation: 0,
          averageSpeed: 0,
          averageHeartRate: 0,
          bestDistance: 0,
          bestDuration: 0,
          bestElevation: 0,
          bestSpeed: 0,
          totalCalories: 0,
          totalSufferScore: 0
        });
      }
      
      const stats = statsMap.get(type)!;
      stats.count++;
      stats.totalDistance += activity.distance;
      stats.totalDuration += activity.duration;
      stats.totalElevation += activity.elevationGain;
      stats.totalCalories += activity.calories || 0;
      stats.totalSufferScore += activity.sufferScore || 0;
      
      if (activity.distance > stats.bestDistance) stats.bestDistance = activity.distance;
      if (activity.duration > stats.bestDuration) stats.bestDuration = activity.duration;
      if (activity.elevationGain > stats.bestElevation) stats.bestElevation = activity.elevationGain;
      if (activity.averageSpeed > stats.bestSpeed) stats.bestSpeed = activity.averageSpeed;
    });
    
    // Calculate averages
    statsMap.forEach(stats => {
      if (stats.count > 0) {
        stats.averageSpeed = stats.totalDistance / (stats.totalDuration / 3600); // km/h
        if (stats.averageHeartRate && stats.averageHeartRate > 0) {
          stats.averageHeartRate = stats.averageHeartRate / stats.count;
        }
      }
    });
    
    return Array.from(statsMap.values()).sort((a, b) => b.totalDistance - a.totalDistance);
  };

  const getSelectedActivityStats = (): ActivityStats | null => {
    const stats = getActivityStats();
    return stats.find(stat => stat.type === selectedActivityType) || null;
  };

  const getChartData = () => {
    const filteredActivities = getFilteredActivitiesByType();
    
    // Group activities by week/month for trend analysis
    const groupedData = new Map<string, { distance: number; duration: number; elevation: number; count: number }>();
    
    filteredActivities.forEach(activity => {
      const date = new Date(activity.startDate);
      let key: string;
      
      if (selectedTimeRange.days <= 30) {
        // Group by day for short periods
        key = date.toISOString().split('T')[0];
      } else if (selectedTimeRange.days <= 90) {
        // Group by week for medium periods
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = weekStart.toISOString().split('T')[0];
      } else {
        // Group by month for long periods
        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      }
      
      const existing = groupedData.get(key) || { distance: 0, duration: 0, elevation: 0, count: 0 };
      existing.distance += activity.distance;
      existing.duration += activity.duration;
      existing.elevation += activity.elevationGain;
      existing.count += 1;
      groupedData.set(key, existing);
    });
    
    return Array.from(groupedData.entries())
      .map(([key, data]) => ({
        period: key,
        distance: Math.round(data.distance * 10) / 10,
        duration: Math.round(data.duration / 3600 * 10) / 10, // Convert to hours
        elevation: Math.round(data.elevation),
        count: data.count
      }))
      .sort((a, b) => a.period.localeCompare(b.period));
  };

  const getPieChartData = () => {
    const stats = getActivityStats();
    return stats.map(stat => ({
      name: stat.type,
      value: stat.totalDistance,
      color: activityColors[stat.type as keyof typeof activityColors] || '#6b7280'
    }));
  };

  const getAvailableActivityTypes = () => {
    const types = new Set(activities.map(activity => activity.type));
    return Array.from(types).sort();
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatSpeed = (kmh: number) => {
    if (useMiles) {
      const mph = kmh * 0.621371;
      return `${mph.toFixed(1)} mph`;
    }
    return `${kmh.toFixed(1)} km/h`;
  };

  const formatDistance = (km: number) => {
    if (useMiles) {
      const miles = km * 0.621371;
      if (miles >= 1) {
        return `${miles.toFixed(1)} mi`;
      }
      return `${(miles * 5280).toFixed(0)} ft`;
    }
    if (km >= 1) {
      return `${km.toFixed(1)} km`;
    }
    return `${(km * 1000).toFixed(0)} m`;
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Strava analytics...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Strava Analytics</h1>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-red-800 mb-2">Error</h3>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={fetchActivities}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const chartData = getChartData();
  const pieChartData = getPieChartData();

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Strava Analytics Page</h1>
        <p className="text-gray-600">
          Detailed insights into your cardio and endurance activities
        </p>
      </div>

      {/* Time Range Selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Time Period</h3>
            <div className="flex flex-wrap gap-2">
              {timeRanges.map((range) => (
                <button
                  key={range.label}
                  onClick={() => setSelectedTimeRange(range)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedTimeRange.label === range.label
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Units</h3>
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setUseMiles(true)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  useMiles
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Miles
              </button>
              <button
                onClick={() => setUseMiles(false)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  !useMiles
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Kilometers
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Activity Type Selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Filter by Activity Type</h3>
        <div className="flex flex-wrap gap-2">
          {getAvailableActivityTypes().map(type => (
            <button
              key={type}
              onClick={() => setSelectedActivityType(type)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedActivityType === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="h-5 w-5 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">{selectedActivityType} Activities</p>
              <p className="text-2xl font-bold text-gray-900">
                {getFilteredActivitiesByType().length}
              </p>
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
              <p className="text-2xl font-bold text-gray-900">
                {formatDistance(getFilteredActivitiesByType().reduce((sum, a) => sum + a.distance, 0))}
              </p>
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
              <p className="text-2xl font-bold text-gray-900">
                {formatDuration(getFilteredActivitiesByType().reduce((sum, a) => sum + a.duration, 0))}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <TrendingUp className="h-5 w-5 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Elevation</p>
              <p className="text-2xl font-bold text-gray-900">
                {getFilteredActivitiesByType().reduce((sum, a) => sum + a.elevationGain, 0).toLocaleString()} m
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activities for Selected Type */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Recent {selectedActivityType} Activities</h3>
        {getFilteredActivitiesByType().length > 0 ? (
          <div className="space-y-4">
            {getFilteredActivitiesByType()
              .sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime())
              .slice(0, 5)
              .map((activity) => (
                <div key={activity.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h4 className="font-medium text-gray-900">{activity.name}</h4>
                        <span className="text-sm text-gray-500">
                          {new Date(activity.startDate).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Distance:</span>
                          <span className="ml-2 font-medium">{formatDistance(activity.distance)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Time:</span>
                          <span className="ml-2 font-medium">{formatDuration(activity.duration)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Speed:</span>
                          <span className="ml-2 font-medium">{formatSpeed(activity.averageSpeed)}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Elevation:</span>
                          <span className="ml-2 font-medium">{activity.elevationGain.toLocaleString()} m</span>
                        </div>
                      </div>
                    </div>
                                         <div className="flex items-center space-x-2">
                       <StravaMap
                         activityId={activity.id}
                         activityName={activity.name}
                         hasMap={activity.hasMap}
                         stravaUrl={activity.stravaUrl || ''}
                       />
                       <a
                         href={activity.stravaUrl}
                         target="_blank"
                         rel="noopener noreferrer"
                         className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                         title="Open in Strava"
                       >
                         <ExternalLink className="h-5 w-5" />
                       </a>
                     </div>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Activity className="h-12 w-12 mx-auto mb-4" />
            <p>No {selectedActivityType} activities found for this time period</p>
          </div>
        )}
      </div>

      {/* Activity Type Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Selected Activity Type Stats */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-6">{selectedActivityType} Statistics</h3>
          {(() => {
            const stats = getSelectedActivityStats();
            return stats ? (
              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-3 mb-3">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: activityColors[selectedActivityType as keyof typeof activityColors] }}
                    />
                    <h4 className="font-medium text-gray-900">{selectedActivityType}</h4>
                    <span className="text-sm text-gray-500">{stats.count} activities</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Distance</p>
                      <p className="font-medium text-gray-900">{formatDistance(stats.totalDistance)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Time</p>
                      <p className="font-medium text-gray-900">{formatDuration(stats.totalDuration)}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Elevation</p>
                      <p className="font-medium text-gray-900">{stats.totalElevation.toLocaleString()} m</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Avg Speed</p>
                      <p className="font-medium text-gray-900">{formatSpeed(stats.averageSpeed)}</p>
                    </div>
                    {stats.averageHeartRate && stats.averageHeartRate > 0 && (
                      <div>
                        <p className="text-gray-600">Avg HR</p>
                        <p className="font-medium text-gray-900">{Math.round(stats.averageHeartRate)} bpm</p>
                      </div>
                    )}
                    {stats.totalCalories > 0 && (
                      <div>
                        <p className="text-gray-600">Calories</p>
                        <p className="font-medium text-gray-900">{stats.totalCalories.toLocaleString()}</p>
                      </div>
                    )}
                  </div>
                              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Activity className="h-12 w-12 mx-auto mb-4" />
              <p>No {selectedActivityType} activities found for this time period</p>
            </div>
          );
        })()}
        </div>

        {/* Distance Distribution Pie Chart */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Distance Distribution</h3>
          {pieChartData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [formatDistance(value as number), useMiles ? 'Distance (mi)' : 'Distance (km)']} />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <PieChart className="h-12 w-12 mx-auto mb-4" />
              <p>No data available for chart</p>
            </div>
          )}
        </div>
      </div>

      {/* Progress Charts */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-6">{selectedActivityType} Progress Over Time</h3>
        {chartData.length > 0 ? (
          <div className="space-y-8">
            {/* Distance Chart */}
            <div>
              <h4 className="text-md font-medium text-gray-700 mb-4">{selectedActivityType} Distance Progress</h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis tickFormatter={(value) => formatDistance(value).split(' ')[0]} />
                    <Tooltip formatter={(value) => [formatDistance(value as number), useMiles ? 'Distance (mi)' : 'Distance (km)']} />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="distance" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Activity Count Chart */}
            <div>
              <h4 className="text-md font-medium text-gray-700 mb-4">{selectedActivityType} Activity Frequency</h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <BarChart3 className="h-12 w-12 mx-auto mb-4" />
            <p>No {selectedActivityType} chart data available for this time period</p>
          </div>
        )}
      </div>

      {/* Personal Records */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-medium text-gray-900 mb-6">{selectedActivityType} Personal Records</h3>
        {getSelectedActivityStats() ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: activityColors[selectedActivityType as keyof typeof activityColors] }}
                />
                <h4 className="font-medium text-gray-900">Best Distance</h4>
              </div>
              <p className="text-2xl font-bold text-gray-900">{formatDistance(getSelectedActivityStats()!.bestDistance)}</p>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: activityColors[selectedActivityType as keyof typeof activityColors] }}
                />
                <h4 className="font-medium text-gray-900">Best Speed</h4>
              </div>
              <p className="text-2xl font-bold text-gray-900">{formatSpeed(getSelectedActivityStats()!.bestSpeed)}</p>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: activityColors[selectedActivityType as keyof typeof activityColors] }}
                />
                <h4 className="font-medium text-gray-900">Best Elevation</h4>
              </div>
              <p className="text-2xl font-bold text-gray-900">{getSelectedActivityStats()!.bestElevation.toLocaleString()} m</p>
            </div>
            
            {getSelectedActivityStats()!.totalCalories > 0 && (
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <div 
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: activityColors[selectedActivityType as keyof typeof activityColors] }}
                  />
                  <h4 className="font-medium text-gray-900">Total Calories</h4>
                </div>
                <p className="text-2xl font-bold text-gray-900">{getSelectedActivityStats()!.totalCalories.toLocaleString()}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Trophy className="h-12 w-12 mx-auto mb-4" />
            <p>No {selectedActivityType} personal records available for this time period</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
