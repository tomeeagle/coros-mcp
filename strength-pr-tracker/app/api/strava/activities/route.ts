import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { fetchStravaActivities } from '@/lib/strava';
import StravaToken from '@/lib/models/StravaToken';

export async function GET(request: NextRequest) {
  try {
    await connectDB();
    
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const perPage = parseInt(searchParams.get('perPage') || '30');
    
    // For now, we'll use a default user ID
    // In a real app, you'd get this from the authenticated user session
    const userId = 'default-user';
    
    // Check if user has Strava connected
    const tokenDoc = await StravaToken.findOne({ userId });
    if (!tokenDoc) {
      return NextResponse.json(
        { error: 'Strava not connected. Please connect your account first.' },
        { status: 401 }
      );
    }
    
    // Fetch activities from Strava
    const activities = await fetchStravaActivities(userId, page, perPage);
    
    return NextResponse.json({
      activities,
      pagination: {
        page,
        perPage,
        hasMore: activities.length === perPage
      }
    });
    
  } catch (error) {
    console.error('Error fetching Strava activities:', error);
    
    if (error instanceof Error && error.message.includes('Failed to refresh Strava token')) {
      return NextResponse.json(
        { error: 'Strava connection expired. Please reconnect your account.' },
        { status: 401 }
      );
    }
    
    return NextResponse.json(
      { error: 'Failed to fetch Strava activities' },
      { status: 500 }
    );
  }
}
