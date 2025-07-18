// CurrentUserAvatar.tsx
import { User } from '@/types'; 
import { useState } from 'react';

interface CurrentUserAvatarProps {
  user: User;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm: 'h-8 w-8 text-sm',
  md: 'h-12 w-12 text-base',
  lg: 'h-16 w-16 text-lg',
  xl: 'h-24 w-24 text-xl'
};

export const CurrentUserAvatar: React.FC<CurrentUserAvatarProps> = ({ 
  user, 
  size = 'sm',
  className = ''
}) => {
  const [imageError, setImageError] = useState(false);
  
  const initials = user.name?.split(' ').map(n => n.charAt(0)).join('').toUpperCase() || 
                   user.email?.charAt(0).toUpperCase() || 'U';

  const handleImageError = () => {
    setImageError(true);
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      {user.avatar && !imageError ? (
        <img 
          src={user.avatar} 
          alt="User avatar" 
          className={`${sizeClasses[size]} rounded-full object-cover border-2 border-gray-200`}
          onError={handleImageError}
        />
      ) : (
        <div className={`${sizeClasses[size]} bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium`}>
          {initials}
        </div>
      )}
    </div>
  );
};