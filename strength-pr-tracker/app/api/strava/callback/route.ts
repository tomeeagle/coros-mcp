import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { exchangeCodeForToken } from '@/lib/strava';
import StravaToken from '@/lib/models/StravaToken';

export async function GET(request: NextRequest) {
  try {
    await connectDB();
    
    const { searchParams } = new URL(request.url);
    const code = searchParams.get('code');
    const error = searchParams.get('error');
    
    if (error) {
      console.error('Strava OAuth error:', error);
      return NextResponse.redirect(
        `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/strava?error=${error}`
      );
    }
    
    if (!code) {
      console.error('No authorization code received from Strava');
      return NextResponse.redirect(
        `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/strava?error=no_code`
      );
    }
    
    // Exchange code for access token
    const tokenData = await exchangeCodeForToken(code);
    
    // For now, we'll use a default user ID
    // In a real app, you'd get this from the authenticated user session
    const userId = 'default-user';
    
    // Store or update the token in the database
    await StravaToken.findOneAndUpdate(
      { userId },
      {
        userId,
        accessToken: tokenData.accessToken,
        refreshToken: tokenData.refreshToken,
        expiresAt: tokenData.expiresAt,
        athleteId: tokenData.athleteId,
        athleteName: tokenData.athleteName,
        updatedAt: new Date()
      },
      { upsert: true, new: true }
    );
    
    console.log(`Strava token stored for user: ${userId}`);
    
    // Redirect back to the Strava page with success
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/strava?success=true&athlete=${encodeURIComponent(tokenData.athleteName)}`
    );
    
  } catch (error) {
    console.error('Error in Strava OAuth callback:', error);
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'}/strava?error=callback_failed`
    );
  }
}
