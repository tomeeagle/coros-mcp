import { NextResponse } from 'next/server';
import { getStravaAuthUrl } from '@/lib/strava';

export async function GET() {
  try {
    // Debug: Log environment variables
    console.log('Environment variables:');
    console.log('STRAVA_CLIENT_ID:', process.env.STRAVA_CLIENT_ID);
    console.log('STRAVA_CLIENT_SECRET:', process.env.STRAVA_CLIENT_SECRET ? '***SET***' : 'NOT SET');
    console.log('STRAVA_REDIRECT_URI:', process.env.STRAVA_REDIRECT_URI);
    console.log('NEXT_PUBLIC_APP_URL:', process.env.NEXT_PUBLIC_APP_URL);
    
    // Check if required environment variables are set
    if (!process.env.STRAVA_CLIENT_ID) {
      console.error('STRAVA_CLIENT_ID is not set');
      return NextResponse.json(
        { error: 'Strava client ID not configured' },
        { status: 500 }
      );
    }
    
    if (!process.env.STRAVA_CLIENT_SECRET) {
      console.error('STRAVA_CLIENT_SECRET is not set');
      return NextResponse.json(
        { error: 'Strava client secret not configured' },
        { status: 500 }
      );
    }
    
    // Generate OAuth URL with a unique state parameter
    const state = `auth_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const authUrl = getStravaAuthUrl(state);
    
    console.log('Generated auth URL:', authUrl);
    
    // Redirect user to Strava OAuth page
    return NextResponse.redirect(authUrl);
    
  } catch (error) {
    console.error('Error generating Strava auth URL:', error);
    return NextResponse.json(
      { error: 'Failed to generate Strava auth URL' },
      { status: 500 }
    );
  }
}
