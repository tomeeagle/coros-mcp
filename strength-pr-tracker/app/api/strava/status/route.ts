import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import StravaToken from '@/lib/models/StravaToken';

export async function GET() {
  try {
    await connectDB();
    
    // For now, we'll use a default user ID
    // In a real app, you'd get this from the authenticated user session
    const userId = 'default-user';
    
    const tokenDoc = await StravaToken.findOne({ userId });
    
    if (!tokenDoc) {
      return NextResponse.json({
        connected: false,
        message: 'Strava not connected'
      });
    }
    
    // Check if token is expired
    const isExpired = tokenDoc.isExpired();
    const expiresSoon = tokenDoc.expiresSoon();
    
    return NextResponse.json({
      connected: !isExpired,
      athleteName: tokenDoc.athleteName,
      athleteId: tokenDoc.athleteId,
      expiresAt: tokenDoc.expiresAt,
      expiresSoon,
      message: isExpired ? 'Strava token expired' : 'Strava connected'
    });
    
  } catch (error) {
    console.error('Error checking Strava status:', error);
    return NextResponse.json(
      { error: 'Failed to check Strava status' },
      { status: 500 }
    );
  }
}
