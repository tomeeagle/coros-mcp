import StravaToken from './models/StravaToken';

// Strava API configuration
export const STRAVA_CONFIG = {
  clientId: process.env.STRAVA_CLIENT_ID!,
  clientSecret: process.env.STRAVA_CLIENT_SECRET!,
  redirectUri: process.env.STRAVA_REDIRECT_URI || 'http://localhost:3001/api/strava/callback',
  apiBaseUrl: 'https://www.strava.com/api/v3',
  authUrl: 'https://www.strava.com/oauth/authorize',
  tokenUrl: 'https://www.strava.com/oauth/token'
};

// Generate OAuth authorization URL
export function getStravaAuthUrl(state?: string): string {
  console.log('getStravaAuthUrl called with:');
  console.log('STRAVA_CONFIG.clientId:', STRAVA_CONFIG.clientId);
  console.log('STRAVA_CONFIG.redirectUri:', STRAVA_CONFIG.redirectUri);
  console.log('state:', state);
  
  const params = new URLSearchParams({
    client_id: STRAVA_CONFIG.clientId,
    redirect_uri: STRAVA_CONFIG.redirectUri,
    response_type: 'code',
    scope: 'read,activity:read_all',
    state: state || 'default'
  });
  
  const authUrl = `${STRAVA_CONFIG.authUrl}?${params.toString()}`;
  console.log('Generated auth URL:', authUrl);
  
  return authUrl;
}

// Exchange authorization code for access token
export async function exchangeCodeForToken(code: string) {
  const response = await fetch(STRAVA_CONFIG.tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      client_id: STRAVA_CONFIG.clientId,
      client_secret: STRAVA_CONFIG.clientSecret,
      code,
      grant_type: 'authorization_code'
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to exchange code for token: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: new Date(Date.now() + data.expires_in * 1000),
    athleteId: data.athlete.id,
    athleteName: `${data.athlete.firstname} ${data.athlete.lastname}`
  };
}

// Refresh access token
export async function refreshAccessToken(refreshToken: string) {
  const response = await fetch(STRAVA_CONFIG.tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      client_id: STRAVA_CONFIG.clientId,
      client_secret: STRAVA_CONFIG.clientSecret,
      refresh_token: refreshToken,
      grant_type: 'refresh_token'
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to refresh token: ${response.statusText}`);
  }

  const data = await response.json();
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    expiresAt: new Date(Date.now() + data.expires_in * 1000)
  };
}

// Get valid access token (refresh if needed)
export async function getValidAccessToken(userId: string): Promise<string> {
  const tokenDoc = await StravaToken.findOne({ userId });
  
  if (!tokenDoc) {
    throw new Error('No Strava token found for user');
  }

  // Check if token is expired or expires soon
  if (tokenDoc.expiresSoon()) {
    try {
      const newTokens = await refreshAccessToken(tokenDoc.refreshToken);
      
      // Update token in database
      await StravaToken.findOneAndUpdate(
        { userId },
        {
          accessToken: newTokens.accessToken,
          refreshToken: newTokens.refreshToken,
          expiresAt: newTokens.expiresAt,
          updatedAt: new Date()
        }
      );
      
      return newTokens.accessToken;
    } catch {
      // If refresh fails, remove the token
      await StravaToken.deleteOne({ userId });
      throw new Error('Failed to refresh Strava token');
    }
  }

  return tokenDoc.accessToken;
}

// Fetch activities from Strava API
export async function fetchStravaActivities(userId: string, page: number = 1, perPage: number = 30) {
  const accessToken = await getValidAccessToken(userId);
  
  const response = await fetch(
    `${STRAVA_CONFIG.apiBaseUrl}/athlete/activities?page=${page}&per_page=${perPage}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch Strava activities: ${response.statusText}`);
  }

  const activities = await response.json();
  
  // Transform Strava data to our format
  return activities.map((activity: {
    id: number;
    name: string;
    type: string;
    distance: number;
    moving_time: number;
    average_speed: number;
    max_speed: number;
    average_heartrate?: number;
    max_heartrate?: number;
    total_elevation_gain: number;
    start_date: string;
    map?: { summary_polyline?: string };
    description?: string;
    kudos_count: number;
    comment_count: number;
    average_cadence?: number;
    average_watts?: number;
    max_watts?: number;
    calories?: number;
    suffer_score?: number;
  }) => ({
    id: activity.id.toString(),
    name: activity.name,
    type: activity.type,
    distance: activity.distance / 1000, // Convert meters to km
    duration: activity.moving_time, // Moving time in seconds
    averageSpeed: activity.average_speed * 3.6, // Convert m/s to km/h
    maxSpeed: activity.max_speed * 3.6,
    averageHeartRate: activity.average_heartrate,
    maxHeartRate: activity.max_heartrate,
    elevationGain: activity.total_elevation_gain,
    startDate: activity.start_date,
    hasMap: activity.map && activity.map.summary_polyline,
    description: activity.description,
    kudos: activity.kudos_count,
    comments: activity.comment_count,
    // Additional Strava-specific fields
    stravaUrl: `https://www.strava.com/activities/${activity.id}`,
    averageCadence: activity.average_cadence,
    averageWatts: activity.average_watts,
    maxWatts: activity.max_watts,
    calories: activity.calories,
    sufferScore: activity.suffer_score
  }));
}

// Fetch athlete profile
export async function fetchAthleteProfile(userId: string) {
  const accessToken = await getValidAccessToken(userId);
  
  const response = await fetch(
    `${STRAVA_CONFIG.apiBaseUrl}/athlete`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch athlete profile: ${response.statusText}`);
  }

  const athlete = await response.json();
  
  return {
    id: athlete.id,
    name: `${athlete.firstname} ${athlete.lastname}`,
    username: athlete.username,
    city: athlete.city,
    state: athlete.state,
    country: athlete.country,
    weight: athlete.weight,
    profilePicture: athlete.profile,
    followerCount: athlete.follower_count,
    friendCount: athlete.friend_count,
    measurementPreference: athlete.measurement_preference,
    ftp: athlete.ftp,
    maxHeartRate: athlete.max_heartrate
  };
}

// Fetch activity details including map data
export async function fetchActivityDetails(userId: string, activityId: string) {
  const accessToken = await getValidAccessToken(userId);
  
  const response = await fetch(
    `${STRAVA_CONFIG.apiBaseUrl}/activities/${activityId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch activity details: ${response.statusText}`);
  }

  const activity = await response.json();
  
  return {
    ...activity,
    // Include detailed map data if available
    map: activity.map,
    // Include segment efforts if available
    segmentEfforts: activity.segment_efforts,
    // Include photos if available
    photos: activity.photos
  };
}
