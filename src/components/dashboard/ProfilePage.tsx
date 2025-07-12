import { useState } from 'react';
import { useAuth } from '@/hooks/auth-context';
import { supabase } from '@/integrations/supabase/client';

const ProfilePage = () => {
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await supabase
      .from('profiles')
      .update({ first_name: user?.id, email: user?.email })
      .eq('id', user?.id ? user.id : '');

    if (error) {
      alert('Error updating profile: ' + error.message);
      return;
    }

    alert('Changes saved successfully!');
    setEditing(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
            <span className="text-gray-600 font-medium">U</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Profile Settings</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={user?.name || ''}
              onChange={() => setEditing(true)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!editing}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={user?.email || ''}
              onChange={() => setEditing(true)}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!editing}
            />
          </div>

          {!editing && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors"
            >
              Edit Profile
            </button>
          )}

          {editing && (
            <button
              type="submit"
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors"
            >
              Save Changes
            </button>
          )}
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;
