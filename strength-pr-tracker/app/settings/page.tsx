'use client';

import { DashboardLayout } from '@/components/DashboardLayout';
import { Settings, User, Database, Info, HelpCircle } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">
          Manage your account and application preferences
        </p>
      </div>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Account Settings */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center mb-4">
            <User className="h-5 w-5 text-blue-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-900">Account Settings</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Profile Information</p>
                <p className="text-sm text-gray-600">Update your personal details</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Password</p>
                <p className="text-sm text-gray-600">Change your password</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">Notifications</p>
                <p className="text-sm text-gray-600">Manage email and push notifications</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
          </div>
        </div>

        {/* Training Preferences */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center mb-4">
            <Settings className="h-5 w-5 text-green-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-900">Training Preferences</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Units</p>
                <p className="text-sm text-gray-600">Weight units (kg/lbs)</p>
              </div>
              <span className="text-sm text-gray-600">Kilograms (kg)</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Default RPE Scale</p>
                <p className="text-sm text-gray-600">Rate of Perceived Exertion</p>
              </div>
              <span className="text-sm text-gray-600">1-10 Scale</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">Auto-calculate Volume</p>
                <p className="text-sm text-gray-600">Automatically calculate total volume</p>
              </div>
              <span className="text-sm text-green-600">Enabled</span>
            </div>
          </div>
        </div>

        {/* Data Management */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center mb-4">
            <Database className="h-5 w-5 text-purple-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-900">Data Management</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Export Data</p>
                <p className="text-sm text-gray-600">Download your training data</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Backup</p>
                <p className="text-sm text-gray-600">Create data backups</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">Clear Data</p>
                <p className="text-sm text-gray-600">Delete all training data</p>
              </div>
              <button className="text-red-600 hover:text-red-700 text-sm font-medium">
                Clear All
              </button>
            </div>
          </div>
        </div>

        {/* About & Help */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center mb-4">
            <Info className="h-5 w-5 text-orange-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-900">About & Help</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">App Version</p>
                <p className="text-sm text-gray-600">Current version information</p>
              </div>
              <span className="text-sm text-gray-600">1.0.0</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <p className="font-medium text-gray-900">Documentation</p>
                <p className="text-sm text-gray-600">User guide and tutorials</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">Support</p>
                <p className="text-sm text-gray-600">Get help and contact support</p>
              </div>
              <span className="text-gray-400">Coming Soon</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              href="/personal-record/new"
              className="flex items-center p-4 bg-white rounded-lg border border-blue-200 hover:border-blue-300 transition-colors"
            >
              <div className="p-2 bg-blue-100 rounded-lg mr-3">
                <Settings className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Log Training Session</p>
                <p className="text-sm text-gray-600">Record your latest workout</p>
              </div>
            </Link>
            
            <Link
              href="/exercises/types"
              className="flex items-center p-4 bg-white rounded-lg border border-blue-200 hover:border-blue-300 transition-colors"
            >
              <div className="p-2 bg-green-100 rounded-lg mr-3">
                <HelpCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Manage Exercises</p>
                <p className="text-sm text-gray-600">Add or edit exercise types</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
