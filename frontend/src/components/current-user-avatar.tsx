// CurrentUserAvatar.tsx
import { User } from '@/types'; 

interface CurrentUserAvatarProps {
  user: User;
}

export const CurrentUserAvatar: React.FC<CurrentUserAvatarProps> = ({ user }) => {
  // Your existing component implementation
  return (
    <div className="flex items-center gap-2">
      {/* Avatar display logic */}
      {user.avatar ? (
        <img src={user.avatar} alt="User avatar" className="h-8 w-8 rounded-full" />
      ) : (
        <div className="h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center">
          {user.name?.charAt(0) || user.email?.charAt(0) || 'U'}
        </div>
      )}
    </div>
  );
};