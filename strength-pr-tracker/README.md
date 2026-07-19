# Strength PR Tracker

A comprehensive strength training application that tracks your workouts, personal records, and progress over time. Built with Next.js, React, TypeScript, and MongoDB.

## Features

- **Comprehensive Session Tracking**: Log multiple sets with weight, reps, RPE, and notes
- **Exercise Management**: Create and manage exercise types with smart categorization
- **Progress Analytics**: Track improvements across weight, reps, and volume
- **Mobile Responsive**: Works perfectly on all devices with toggleable sidebar
- **Strava Integration**: Connect your Strava account to track cardio and endurance activities
- **Automatic PR Detection**: App identifies when you hit personal bests
- **Beautiful Charts**: Visualize your progress with professional charts

## Tech Stack

- **Frontend**: Next.js 15, React 18, TypeScript, Tailwind CSS
- **Backend**: Next.js API Routes, MongoDB with Mongoose
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React for beautiful icons
- **Database**: MongoDB for data persistence

## Getting Started

### Prerequisites

- Node.js 18+ 
- MongoDB database
- Strava account (for cardio tracking features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd strength-pr-tracker
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env.local
   ```
   
   Edit `.env.local` with your configuration:
   ```env
   # Database
   MONGODB_URI=your_mongodb_connection_string
   
   # Strava API Configuration
   STRAVA_CLIENT_ID=your_strava_client_id
   STRAVA_CLIENT_SECRET=your_strava_client_secret
   STRAVA_REDIRECT_URI=http://localhost:3001/api/strava/callback
   
   # App Configuration
   NEXT_PUBLIC_APP_URL=http://localhost:3001
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3001](http://localhost:3001)

## Strava Integration Setup

To enable Strava integration for tracking cardio and endurance activities:

### 1. Create a Strava API Application

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Set the **Authorization Callback Domain** to `localhost:3001`
4. Note your **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Add your Strava credentials to `.env.local`:
```env
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
STRAVA_REDIRECT_URI=http://localhost:3001/api/strava/callback
```

### 3. Connect Your Account

1. Navigate to the **Strava Activities** page in the app
2. Click **Connect Strava Account**
3. Authorize the app to access your Strava data
4. Your activities will automatically sync

### 4. What Data is Synced

- **Activity Types**: Running, cycling, swimming, walking, hiking
- **Performance Metrics**: Distance, duration, pace, elevation, heart rate
- **Social Features**: Kudos, comments, activity descriptions
- **Route Data**: GPS coordinates for map visualization (when available)

## Data Models

### Exercise
- `name`: Exercise name (e.g., "Bench Press")
- `description`: Optional description
- `createdAt`: Creation timestamp

### Personal Record (Session)
- `exerciseId`: Reference to exercise type
- `sets`: Array of individual sets with weight, reps, RPE, and notes
- `date`: Session date
- `sessionNotes`: Overall session notes
- `totalVolume`: Automatically calculated (weight × reps)
- `maxWeight`: Highest weight used in session
- `maxReps`: Most reps performed in session
- `isPersonalBest`: Whether this session achieved a PR
- `pbType`: Type of PR (weight, reps, volume, first)

### Strava Token
- `userId`: User identifier
- `accessToken`: Strava API access token
- `refreshToken`: Token for refreshing access
- `expiresAt`: Token expiration timestamp
- `athleteId`: Strava athlete ID
- `athleteName`: Athlete's full name

## API Endpoints

### Training Sessions
- `GET /api/personal-record` - Fetch all sessions
- `POST /api/personal-record` - Create new session
- `PUT /api/personal-record/[id]` - Update session
- `DELETE /api/personal-record/[id]` - Delete session

### Exercise Types
- `GET /api/exercise` - Fetch all exercise types
- `POST /api/exercise` - Create new exercise type
- `GET /api/exercise/[id]` - Fetch specific exercise
- `PUT /api/exercise/[id]` - Update exercise
- `DELETE /api/exercise/[id]` - Delete exercise

### Strava Integration
- `GET /api/strava/auth` - Initiate OAuth flow
- `GET /api/strava/callback` - Handle OAuth callback
- `GET /api/strava/status` - Check connection status
- `GET /api/strava/activities` - Fetch Strava activities

## Usage

### Logging Training Sessions

1. Navigate to **Log Session**
2. Select an exercise type
3. Add multiple sets with weight, reps, RPE, and notes
4. Add session-level notes if desired
5. Submit to automatically calculate volume and check for PRs

### Managing Exercise Types

1. Go to **Exercise Types**
2. Create new exercises with descriptive names
3. Use the categorization system for better organization
4. Each exercise gets relevant icons and colors

### Tracking Progress

1. View **Analytics** for overall training insights
2. Check **Progress** for detailed improvement tracking
3. Use **Strava Activities** for cardio and endurance data
4. Monitor PRs and performance trends over time

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please open an issue on GitHub or contact the development team.